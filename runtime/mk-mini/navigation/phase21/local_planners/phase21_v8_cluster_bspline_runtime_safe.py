from __future__ import annotations

import math
from collections import Counter, deque
from typing import Any

import numpy as np

from navigation.phase21.interfaces import (
    PlannerRequest,
    PlannerResult,
)
from navigation.phase21.local_planners.phase21_v4_config import (
    Phase21V4Config,
)
from navigation.phase21.local_planners.phase21_v4_geometry import (
    index_after,
    index_before,
    known_margin,
    path_metrics,
    point_segment_distances,
)
from navigation.phase21.local_planners.phase21_v4_hermite_fallback import (
    Phase21V4HermiteFallback,
)


# 不降低原安全阈值，只扫描连续路径几何参数。
APPROACH_DISTANCES = (
    0.85,
    1.00,
    1.20,
    1.40,
)

REJOIN_DISTANCES = (
    1.60,
    2.00,
    2.40,
    2.80,
)

CLUSTER_EPS_VALUES = (
    0.18,
    0.24,
    0.30,
)

LONGITUDINAL_BUFFERS = (
    0.15,
    0.25,
    0.35,
)

LATERAL_EXTRA_BUFFERS = (
    0.05,
    0.10,
    0.15,
    0.20,
)

SHOULDER_SCALES = (
    0.35,
    0.50,
    0.65,
    0.80,
)

MIN_LATERAL_OFFSET = 0.26
PATH_SPACING = 0.040
TANGENT_WINDOW = 4
BSPLINE_DEGREE = 3


def normalize(
    vector: np.ndarray,
) -> np.ndarray:
    vector = np.asarray(
        vector,
        dtype=np.float32,
    ).reshape(2)

    norm = float(
        np.linalg.norm(vector)
    )

    if norm < 1e-6:
        raise ValueError(
            "zero_length_vector"
        )

    return (
        vector / norm
    ).astype(np.float32)


def path_tangent(
    path: np.ndarray,
    index: int,
) -> np.ndarray:
    return (
        Phase21V4HermiteFallback
        ._path_tangent(
            path,
            index,
            TANGENT_WINDOW,
        )
    )


def path_normal(
    path: np.ndarray,
    index: int,
) -> np.ndarray:
    tangent = path_tangent(
        path,
        index,
    )

    return np.asarray(
        [
            -tangent[1],
            tangent[0],
        ],
        dtype=np.float32,
    )


def connected_components(
    points: np.ndarray,
    eps: float,
) -> list[np.ndarray]:
    """
    纯NumPy欧氏距离聚类。

    不依赖sklearn，不读取未知障碍真值。
    """
    points = np.asarray(
        points,
        dtype=np.float32,
    ).reshape(-1, 2)

    count = len(points)

    if count == 0:
        return []

    distances = np.linalg.norm(
        points[:, None, :]
        - points[None, :, :],
        axis=2,
    )

    visited = np.zeros(
        count,
        dtype=bool,
    )

    components: list[np.ndarray] = []

    for start in range(count):
        if visited[start]:
            continue

        queue: deque[int] = deque(
            [start]
        )

        visited[start] = True
        indices: list[int] = []

        while queue:
            current = queue.popleft()
            indices.append(current)

            neighbours = np.flatnonzero(
                distances[current]
                <= float(eps)
            )

            for neighbour in neighbours:
                neighbour = int(neighbour)

                if visited[neighbour]:
                    continue

                visited[neighbour] = True
                queue.append(neighbour)

        components.append(
            points[
                np.asarray(
                    indices,
                    dtype=np.int64,
                )
            ]
        )

    return components


def select_conflict_cluster(
    conflict_points: np.ndarray,
    path_conflict_point: np.ndarray,
    eps: float,
) -> np.ndarray:
    components = connected_components(
        conflict_points,
        eps,
    )

    if not components:
        raise ValueError(
            "no_sensor_cluster"
        )

    def cluster_key(
        cluster: np.ndarray,
    ) -> tuple[float, int]:
        centroid = np.mean(
            cluster,
            axis=0,
        )

        distance = float(
            np.linalg.norm(
                centroid
                - path_conflict_point
            )
        )

        # 首先选离冲突路径点最近的簇；
        # 距离相同时优先点数更多的簇。
        return (
            distance,
            -len(cluster),
        )

    return min(
        components,
        key=cluster_key,
    )


def project_cluster_to_frenet(
    cluster: np.ndarray,
    origin: np.ndarray,
    tangent: np.ndarray,
    normal: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    relative = (
        np.asarray(
            cluster,
            dtype=np.float32,
        )
        - np.asarray(
            origin,
            dtype=np.float32,
        )
    )

    longitudinal = (
        relative @ tangent
    )

    lateral = (
        relative @ normal
    )

    return (
        longitudinal.astype(
            np.float32
        ),
        lateral.astype(
            np.float32
        ),
    )


def make_clamped_knots(
    control_count: int,
    degree: int,
) -> np.ndarray:
    n = control_count - 1

    if n < degree:
        raise ValueError(
            "insufficient_control_points"
        )

    interior_count = n - degree

    knots: list[float] = (
        [0.0] * (degree + 1)
    )

    if interior_count > 0:
        denominator = float(
            interior_count + 1
        )

        knots.extend(
            float(index) / denominator
            for index in range(
                1,
                interior_count + 1,
            )
        )

    knots.extend(
        [1.0] * (degree + 1)
    )

    return np.asarray(
        knots,
        dtype=np.float64,
    )


def de_boor_point(
    control_points: np.ndarray,
    knots: np.ndarray,
    degree: int,
    parameter: float,
) -> np.ndarray:
    control_points = np.asarray(
        control_points,
        dtype=np.float64,
    ).reshape(-1, 2)

    n = len(control_points) - 1

    u = float(
        np.clip(
            parameter,
            0.0,
            1.0,
        )
    )

    if u >= 1.0:
        knot_index = n
    else:
        knot_index = int(
            np.searchsorted(
                knots,
                u,
                side="right",
            )
            - 1
        )

        knot_index = max(
            degree,
            min(
                knot_index,
                n,
            ),
        )

    values = [
        control_points[
            knot_index
            - degree
            + local_index
        ].copy()
        for local_index in range(
            degree + 1
        )
    ]

    for level in range(
        1,
        degree + 1,
    ):
        for local_index in range(
            degree,
            level - 1,
            -1,
        ):
            global_index = (
                knot_index
                - degree
                + local_index
            )

            denominator = (
                knots[
                    global_index
                    + degree
                    - level
                    + 1
                ]
                - knots[global_index]
            )

            if abs(
                float(denominator)
            ) < 1e-12:
                alpha = 0.0
            else:
                alpha = (
                    u
                    - knots[global_index]
                ) / denominator

            values[local_index] = (
                (
                    1.0
                    - alpha
                )
                * values[
                    local_index - 1
                ]
                + alpha
                * values[local_index]
            )

    return values[degree].astype(
        np.float32
    )


def sample_bspline(
    control_points: np.ndarray,
    spacing: float,
) -> np.ndarray:
    control_points = np.asarray(
        control_points,
        dtype=np.float32,
    ).reshape(-1, 2)

    polygon_length = float(
        np.sum(
            np.linalg.norm(
                np.diff(
                    control_points,
                    axis=0,
                ),
                axis=1,
            )
        )
    )

    point_count = max(
        40,
        int(
            math.ceil(
                polygon_length
                / float(spacing)
            )
        )
        + 1,
    )

    knots = make_clamped_knots(
        len(control_points),
        BSPLINE_DEGREE,
    )

    parameters = np.linspace(
        0.0,
        1.0,
        point_count,
        dtype=np.float64,
    )

    curve = np.stack(
        [
            de_boor_point(
                control_points,
                knots,
                BSPLINE_DEGREE,
                parameter,
            )
            for parameter in parameters
        ],
        axis=0,
    ).astype(np.float32)

    # 保证端点与原路径精确连接。
    curve[0] = control_points[0]
    curve[-1] = control_points[-1]

    return curve


def forward_reverse_count(
    candidate: np.ndarray,
    forward_direction: np.ndarray,
) -> tuple[int, float]:
    vectors = np.diff(
        candidate,
        axis=0,
    )

    norms = np.linalg.norm(
        vectors,
        axis=1,
        keepdims=True,
    )

    vectors = (
        vectors
        / np.maximum(
            norms,
            1e-6,
        )
    )

    direction = normalize(
        forward_direction
    )

    alignment = (
        vectors @ direction
    )

    return (
        int(
            np.count_nonzero(
                alignment < -0.05
            )
        ),
        float(
            np.min(alignment)
        ),
    )


def violation_penalty(
    *,
    known_value: float,
    sensor_value: float,
    curvature_value: float,
    path_heading_value: float,
    join_heading_value: float,
    reverse_count: int,
    config: Phase21V4Config,
) -> float:
    penalty = 0.0

    penalty += max(
        0.0,
        (
            config.min_known_margin
            - known_value
        )
        / max(
            config.min_known_margin,
            1e-6,
        ),
    )

    penalty += max(
        0.0,
        (
            config.min_sensor_margin
            - sensor_value
        )
        / max(
            config.min_sensor_margin,
            1e-6,
        ),
    )

    penalty += max(
        0.0,
        (
            curvature_value
            - config.max_p95_curvature
        )
        / max(
            config.max_p95_curvature,
            1e-6,
        ),
    )

    penalty += max(
        0.0,
        (
            path_heading_value
            - config.max_heading_delta
        )
        / max(
            config.max_heading_delta,
            1e-6,
        ),
    )

    penalty += max(
        0.0,
        (
            join_heading_value
            - config.max_heading_delta
        )
        / max(
            config.max_heading_delta,
            1e-6,
        ),
    )

    penalty += float(
        reverse_count
    )

    return float(penalty)



class Phase21V8ClusterBSplineRuntimeSafe:
    """
    障碍簇驱动的非栅格多控制点B样条规划器。

    仅使用：
    1. 初始全局参考路径；
    2. 当前传感器点；
    3. 已知地图障碍。

    不调用局部A*，不使用未知障碍真值。
    """

    def __init__(
        self,
        config: Phase21V4Config | None = None,
    ) -> None:
        self.config = (
            Phase21V4Config()
            if config is None
            else config
        )

    def plan(
        self,
        request: PlannerRequest,
        *,
        prior_result: PlannerResult,
    ) -> PlannerResult:
        original = np.asarray(
            request.original_path,
            dtype=np.float32,
        ).reshape(-1, 2)

        sensor_world = np.asarray(
            request.sensor_points_world,
            dtype=np.float32,
        ).reshape(-1, 2)

        sensor_local = np.asarray(
            request.sensor_points_local,
            dtype=np.float32,
        ).reshape(-1, 2)

        if (
            request.path_lookahead is None
            or request.corridor_radius is None
            or request.conflict_margin is None
        ):
            return PlannerResult.failed(
                original_path=original,
                reason="missing_runtime_parameter",
                diagnostics={
                    "planner_name":
                        "phase21_v8_cluster_bspline_runtime_safe",
                    "uses_local_astar": False,
                    "uses_unknown_ground_truth":
                        False,
                },
            )

        robot_xy = np.asarray(
            request.robot_pose[:2],
            dtype=np.float32,
        )

        nearest_robot_index = int(
            np.argmin(
                np.linalg.norm(
                    original - robot_xy,
                    axis=1,
                )
            )
        )

        future_path = original[
            nearest_robot_index:
        ]

        sensor_path_distance = (
            point_segment_distances(
                sensor_world,
                future_path,
            )
        )

        corridor_radius = float(
            request.corridor_radius
        )

        conflict_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= float(
                    request.path_lookahead
                )
                + 0.50
            )
            & (
                sensor_path_distance
                < corridor_radius
                + float(
                    request.conflict_margin
                )
            )
        )

        if not np.any(conflict_mask):
            return PlannerResult.failed(
                original_path=original,
                reason=(
                    "no_corridor_sensor_cluster"
                ),
                diagnostics={
                    "planner_name":
                        "phase21_v8_cluster_bspline_runtime_safe",
                    "uses_local_astar": False,
                    "uses_unknown_ground_truth":
                        False,
                },
            )

        conflict_points = sensor_world[
            conflict_mask
        ]

        # 冲突点只用于障碍簇识别。
        # 最终候选必须对全部前向可见传感器点安全。
        validation_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= float(
                    request.path_lookahead
                )
                + 0.50
            )
        )

        validation_points = sensor_world[
            validation_mask
        ]

        if len(validation_points) == 0:
            validation_points = conflict_points

        conflict_center = np.median(
            conflict_points,
            axis=0,
        ).astype(np.float32)

        conflict_index = int(
            prior_result.diagnostics.get(
                "conflict_index",
                np.argmin(
                    np.linalg.norm(
                        original
                        - conflict_center,
                        axis=1,
                    )
                ),
            )
        )

        preferred_side_name = str(
            prior_result.diagnostics.get(
                "preferred_side",
                "RIGHT",
            )
        )

        preferred_side_sign = (
            1.0
            if preferred_side_name == "LEFT"
            else -1.0
        )

        side_values = (
            preferred_side_sign,
            -preferred_side_sign,
        )

        conflict_path_point = original[
            conflict_index
        ]

        conflict_tangent = path_tangent(
            original,
            conflict_index,
        )

        conflict_normal = path_normal(
            original,
            conflict_index,
        )

        candidate_count = 0
        feasible_count = 0
        geometry_error_count = 0

        rejection_counts = Counter()

        best: dict[str, Any] | None = None

        seen_geometry: set[
            tuple[Any, ...]
        ] = set()

        for cluster_eps in (
            CLUSTER_EPS_VALUES
        ):
            try:
                selected_cluster = (
                    select_conflict_cluster(
                        conflict_points,
                        conflict_path_point,
                        cluster_eps,
                    )
                )
            except ValueError:
                continue

            (
                cluster_longitudinal,
                cluster_lateral,
            ) = project_cluster_to_frenet(
                selected_cluster,
                conflict_path_point,
                conflict_tangent,
                conflict_normal,
            )

            s_min = float(
                np.min(
                    cluster_longitudinal
                )
            )

            s_max = float(
                np.max(
                    cluster_longitudinal
                )
            )

            l_min = float(
                np.min(
                    cluster_lateral
                )
            )

            l_max = float(
                np.max(
                    cluster_lateral
                )
            )

            for longitudinal_buffer in (
                LONGITUDINAL_BUFFERS
            ):
                pre_distance = max(
                    0.25,
                    -min(
                        s_min,
                        0.0,
                    )
                    + float(
                        longitudinal_buffer
                    ),
                )

                post_distance = max(
                    0.25,
                    max(
                        s_max,
                        0.0,
                    )
                    + float(
                        longitudinal_buffer
                    ),
                )

                pre_index = index_before(
                    original,
                    conflict_index,
                    pre_distance,
                )

                post_index = index_after(
                    original,
                    conflict_index,
                    post_distance,
                )

                for approach_distance in (
                    APPROACH_DISTANCES
                ):
                    approach_index = index_before(
                        original,
                        conflict_index,
                        approach_distance,
                    )

                    for rejoin_distance in (
                        REJOIN_DISTANCES
                    ):
                        rejoin_index = index_after(
                            original,
                            conflict_index,
                            rejoin_distance,
                        )

                        if not (
                            approach_index
                            < pre_index
                            < conflict_index
                            < post_index
                            < rejoin_index
                            < len(original)
                        ):
                            continue

                        first_shoulder_index = int(
                            round(
                                0.5
                                * (
                                    approach_index
                                    + pre_index
                                )
                            )
                        )

                        second_shoulder_index = int(
                            round(
                                0.5
                                * (
                                    post_index
                                    + rejoin_index
                                )
                            )
                        )

                        original_segment = original[
                            approach_index:
                            rejoin_index + 1
                        ]

                        original_length = float(
                            np.sum(
                                np.linalg.norm(
                                    np.diff(
                                        original_segment,
                                        axis=0,
                                    ),
                                    axis=1,
                                )
                            )
                        )

                        forward_direction = (
                            original[rejoin_index]
                            - original[
                                approach_index
                            ]
                        )

                        for lateral_extra in (
                            LATERAL_EXTRA_BUFFERS
                        ):
                            left_target = max(
                                MIN_LATERAL_OFFSET,
                                l_max
                                + corridor_radius
                                + self.config
                                .min_sensor_margin
                                + float(
                                    lateral_extra
                                ),
                            )

                            right_target = min(
                                -MIN_LATERAL_OFFSET,
                                l_min
                                - corridor_radius
                                - self.config
                                .min_sensor_margin
                                - float(
                                    lateral_extra
                                ),
                            )

                            for side_sign in (
                                side_values
                            ):
                                if side_sign > 0.0:
                                    side_name = "LEFT"
                                    target_lateral = (
                                        left_target
                                    )
                                else:
                                    side_name = "RIGHT"
                                    target_lateral = (
                                        right_target
                                    )

                                for shoulder_scale in (
                                    SHOULDER_SCALES
                                ):
                                    geometry_key = (
                                        int(
                                            approach_index
                                        ),
                                        int(pre_index),
                                        int(
                                            conflict_index
                                        ),
                                        int(post_index),
                                        int(rejoin_index),
                                        side_name,
                                        round(
                                            target_lateral,
                                            4,
                                        ),
                                        round(
                                            shoulder_scale,
                                            4,
                                        ),
                                    )

                                    if (
                                        geometry_key
                                        in seen_geometry
                                    ):
                                        continue

                                    seen_geometry.add(
                                        geometry_key
                                    )

                                    try:
                                        pre_normal = (
                                            path_normal(
                                                original,
                                                pre_index,
                                            )
                                        )

                                        post_normal = (
                                            path_normal(
                                                original,
                                                post_index,
                                            )
                                        )

                                        control_points = (
                                            np.stack(
                                                [
                                                    original[
                                                        approach_index
                                                    ],
                                                    original[
                                                        first_shoulder_index
                                                    ],
                                                    (
                                                        original[
                                                            pre_index
                                                        ]
                                                        + float(
                                                            shoulder_scale
                                                        )
                                                        * float(
                                                            target_lateral
                                                        )
                                                        * pre_normal
                                                    ),
                                                    (
                                                        original[
                                                            conflict_index
                                                        ]
                                                        + float(
                                                            target_lateral
                                                        )
                                                        * conflict_normal
                                                    ),
                                                    (
                                                        original[
                                                            post_index
                                                        ]
                                                        + float(
                                                            shoulder_scale
                                                        )
                                                        * float(
                                                            target_lateral
                                                        )
                                                        * post_normal
                                                    ),
                                                    original[
                                                        second_shoulder_index
                                                    ],
                                                    original[
                                                        rejoin_index
                                                    ],
                                                ],
                                                axis=0,
                                            ).astype(
                                                np.float32
                                            )
                                        )

                                        local_curve = (
                                            sample_bspline(
                                                control_points,
                                                PATH_SPACING,
                                            )
                                        )

                                    except ValueError:
                                        geometry_error_count += 1
                                        continue

                                    candidate_count += 1

                                    active_path = (
                                        np.concatenate(
                                            [
                                                original[
                                                    :approach_index
                                                ],
                                                local_curve,
                                                original[
                                                    rejoin_index
                                                    + 1:
                                                ],
                                            ],
                                            axis=0,
                                        ).astype(
                                            np.float32
                                        )
                                    )

                                    metrics = path_metrics(
                                        local_curve,
                                        original_length,
                                    )

                                    join_path = (
                                        Phase21V4HermiteFallback
                                        ._local_join_path(
                                            original,
                                            approach_index,
                                            rejoin_index,
                                            local_curve,
                                        )
                                    )

                                    join_metrics = (
                                        path_metrics(
                                            join_path,
                                            original_length,
                                        )
                                    )

                                    candidate_known_margin = (
                                        known_margin(
                                            active_path,
                                            request
                                            .known_obstacles,
                                            float(
                                                request
                                                .robot_radius
                                            ),
                                        )
                                    )

                                    # 关键修正：
                                    # 不能只验证原路径走廊中的冲突点。
                                    # 绕行曲线必须避开全部前向传感器点。
                                    sensor_distances = (
                                        point_segment_distances(
                                            validation_points,
                                            local_curve,
                                        )
                                    )

                                    candidate_sensor_margin = float(
                                        np.min(
                                            sensor_distances
                                        )
                                        - corridor_radius
                                    )

                                    (
                                        reverse_count,
                                        min_alignment,
                                    ) = (
                                        forward_reverse_count(
                                            local_curve,
                                            forward_direction,
                                        )
                                    )

                                    p95_curvature = float(
                                        metrics[
                                            "p95_curvature"
                                        ]
                                    )

                                    path_heading = float(
                                        metrics[
                                            "max_heading_delta"
                                        ]
                                    )

                                    join_heading = float(
                                        join_metrics[
                                            "max_heading_delta"
                                        ]
                                    )

                                    violations: list[
                                        str
                                    ] = []

                                    if (
                                        candidate_known_margin
                                        < self.config
                                        .min_known_margin
                                    ):
                                        violations.append(
                                            "known_margin"
                                        )

                                    if (
                                        candidate_sensor_margin
                                        < self.config
                                        .min_sensor_margin
                                    ):
                                        violations.append(
                                            "sensor_margin"
                                        )

                                    if (
                                        p95_curvature
                                        > self.config
                                        .max_p95_curvature
                                    ):
                                        violations.append(
                                            "p95_curvature"
                                        )

                                    if (
                                        path_heading
                                        > self.config
                                        .max_heading_delta
                                    ):
                                        violations.append(
                                            "path_heading"
                                        )

                                    if (
                                        join_heading
                                        > self.config
                                        .max_heading_delta
                                    ):
                                        violations.append(
                                            "join_heading"
                                        )

                                    if reverse_count != 0:
                                        violations.append(
                                            "reverse_steps"
                                        )

                                    for violation in (
                                        violations
                                    ):
                                        rejection_counts[
                                            violation
                                        ] += 1

                                    if violations:
                                        continue

                                    feasible_count += 1

                                    preference_bonus = (
                                        0.05
                                        if side_sign
                                        == preferred_side_sign
                                        else 0.0
                                    )

                                    score = (
                                        4.0
                                        * min(
                                            candidate_sensor_margin,
                                            0.50,
                                        )
                                        + 2.0
                                        * min(
                                            candidate_known_margin,
                                            0.50,
                                        )
                                        - 0.35
                                        * p95_curvature
                                        - 0.60
                                        * path_heading
                                        - 0.35
                                        * join_heading
                                        - 0.30
                                        * max(
                                            0.0,
                                            float(
                                                metrics[
                                                    "length_ratio"
                                                ]
                                            )
                                            - 1.0,
                                        )
                                        - 0.05
                                        * abs(
                                            target_lateral
                                        )
                                        + preference_bonus
                                    )

                                    if (
                                        best is not None
                                        and score
                                        <= best["score"]
                                    ):
                                        continue

                                    best = {
                                        "score":
                                            float(score),
                                        "active_path":
                                            active_path,
                                        "local_curve":
                                            local_curve,
                                        "control_points":
                                            control_points,
                                        "selected_cluster":
                                            selected_cluster,
                                        "chosen_side":
                                            side_name,
                                        "approach_index":
                                            int(
                                                approach_index
                                            ),
                                        "rejoin_index":
                                            int(
                                                rejoin_index
                                            ),
                                        "known_margin":
                                            float(
                                                candidate_known_margin
                                            ),
                                        "sensor_margin":
                                            float(
                                                candidate_sensor_margin
                                            ),
                                        "p95_curvature":
                                            p95_curvature,
                                        "path_heading":
                                            path_heading,
                                        "join_heading":
                                            join_heading,
                                        "reverse_count":
                                            int(
                                                reverse_count
                                            ),
                                        "min_alignment":
                                            float(
                                                min_alignment
                                            ),
                                        "cluster_eps":
                                            float(
                                                cluster_eps
                                            ),
                                        "cluster_size":
                                            int(
                                                len(
                                                    selected_cluster
                                                )
                                            ),
                                        "cluster_s_min":
                                            s_min,
                                        "cluster_s_max":
                                            s_max,
                                        "cluster_l_min":
                                            l_min,
                                        "cluster_l_max":
                                            l_max,
                                        "approach_distance":
                                            float(
                                                approach_distance
                                            ),
                                        "rejoin_distance":
                                            float(
                                                rejoin_distance
                                            ),
                                        "longitudinal_buffer":
                                            float(
                                                longitudinal_buffer
                                            ),
                                        "lateral_extra":
                                            float(
                                                lateral_extra
                                            ),
                                        "target_lateral":
                                            float(
                                                target_lateral
                                            ),
                                        "shoulder_scale":
                                            float(
                                                shoulder_scale
                                            ),
                                        "length_ratio":
                                            float(
                                                metrics[
                                                    "length_ratio"
                                                ]
                                            ),
                                    }

        base_diagnostics = {
            "planner_name":
                "phase21_v8_cluster_bspline_runtime_safe",
            "uses_local_astar": False,
            "uses_unknown_ground_truth":
                False,
            "conflict_index":
                int(conflict_index),
            "conflict_center":
                conflict_center.tolist(),
            "preferred_side":
                preferred_side_name,
            "conflict_sensor_point_count":
                int(
                    len(conflict_points)
                ),
            "validation_sensor_point_count":
                int(
                    len(validation_points)
                ),
            "candidate_count":
                int(candidate_count),
            "feasible_count":
                int(feasible_count),
            "geometry_error_count":
                int(geometry_error_count),
            "rejection_counts":
                dict(rejection_counts),
        }

        if best is None:
            failure = PlannerResult.failed(original_path=original, reason='cluster_bspline_no_feasible_candidate', diagnostics=base_diagnostics)
            failure.candidate_family = 'phase21_v8_cluster_guided_bspline_runtime_safe'
            failure.candidate_count = int(candidate_count)
            failure.feasible_count = int(feasible_count)
            return failure

        diagnostics = dict(
            base_diagnostics
        )

        diagnostics.update({
            "selected_cluster_eps":
                best["cluster_eps"],
            "selected_cluster_size":
                best["cluster_size"],
            "selected_cluster_s_min":
                best["cluster_s_min"],
            "selected_cluster_s_max":
                best["cluster_s_max"],
            "selected_cluster_l_min":
                best["cluster_l_min"],
            "selected_cluster_l_max":
                best["cluster_l_max"],
            "selected_approach_distance":
                best["approach_distance"],
            "selected_rejoin_distance":
                best["rejoin_distance"],
            "selected_longitudinal_buffer":
                best["longitudinal_buffer"],
            "selected_lateral_extra":
                best["lateral_extra"],
            "selected_target_lateral":
                best["target_lateral"],
            "selected_shoulder_scale":
                best["shoulder_scale"],
            "selected_join_heading":
                best["join_heading"],
            "selected_reverse_count":
                best["reverse_count"],
            "selected_min_alignment":
                best["min_alignment"],
            "selected_length_ratio":
                best["length_ratio"],
            "control_points":
                np.asarray(
                    best["control_points"]
                ).tolist(),
        })

        return PlannerResult(
            success=True,
            active_path=np.asarray(
                best["active_path"],
                dtype=np.float64,
            ),
            chosen_side=str(
                best["chosen_side"]
            ),
            candidate_family=(
                "phase21_v7_"
                "cluster_guided_bspline"
            ),
            failure_reason=None,
            known_margin=float(
                best["known_margin"]
            ),
            sensor_margin=float(
                best["sensor_margin"]
            ),
            p95_curvature=float(
                best["p95_curvature"]
            ),
            max_heading_delta=float(
                best["path_heading"]
            ),
            score=float(
                best["score"]
            ),
            candidate_count=int(
                candidate_count
            ),
            feasible_count=int(
                feasible_count
            ),
            approach_point=np.asarray(
                best["control_points"][0],
                dtype=np.float64,
            ),
            detour_point=np.asarray(
                best["control_points"][3],
                dtype=np.float64,
            ),
            rejoin_point=np.asarray(
                best["control_points"][-1],
                dtype=np.float64,
            ),
            diagnostics=diagnostics,
        )


__all__ = [
    "Phase21V8ClusterBSplineRuntimeSafe",
]
