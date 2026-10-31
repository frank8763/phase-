from __future__ import annotations

import math
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


class Phase21V4HermiteFallback:
    """
    仅在原v4返回no_feasible_candidate时启用。

    不修改风险检测、不读取MuJoCo对象、不使用未知障碍真值。
    """

    APPROACH_DISTANCES = (0.45,)
    REJOIN_DISTANCES = (1.60,)

    OFFSETS = (
        0.20,
        0.21,
        0.22,
        0.23,
        0.24,
        0.25,
        0.26,
        0.27,
        0.28,
        0.29,
        0.30,
    )

    TANGENT_WINDOWS = (
        2,
        4,
        6,
        8,
    )

    TANGENT_SCALES = (
        0.450,
        0.475,
        0.500,
        0.525,
        0.550,
        0.575,
        0.600,
        0.625,
        0.650,
        0.675,
        0.700,
        0.725,
        0.750,
        0.775,
        0.800,
        0.825,
        0.850,
        0.875,
        0.900,
    )

    SPACINGS = (0.040,)

    def __init__(
        self,
        config: Phase21V4Config | None = None,
    ) -> None:
        self.config = (
            Phase21V4Config()
            if config is None
            else config
        )

    @staticmethod
    def _path_tangent(
        path: np.ndarray,
        index: int,
        window: int,
    ) -> np.ndarray:
        before = max(
            0,
            index - window,
        )

        after = min(
            len(path) - 1,
            index + window,
        )

        vector = (
            path[after]
            - path[before]
        ).astype(np.float32)

        norm = float(
            np.linalg.norm(vector)
        )

        if norm < 1e-6:
            raise ValueError(
                "invalid_endpoint_tangent"
            )

        return (
            vector / norm
        ).astype(np.float32)

    @staticmethod
    def _quintic_smoothstep(
        value: np.ndarray,
    ) -> np.ndarray:
        value = np.clip(
            value,
            0.0,
            1.0,
        )

        return (
            10.0 * value**3
            - 15.0 * value**4
            + 6.0 * value**5
        )

    @classmethod
    def _c2_bump(
        cls,
        parameter: np.ndarray,
    ) -> np.ndarray:
        parameter = np.asarray(
            parameter,
            dtype=np.float32,
        )

        profile = np.empty_like(
            parameter,
            dtype=np.float32,
        )

        first_half = parameter <= 0.5

        profile[first_half] = (
            cls._quintic_smoothstep(
                2.0
                * parameter[first_half]
            )
        )

        profile[~first_half] = (
            cls._quintic_smoothstep(
                2.0
                * (
                    1.0
                    - parameter[~first_half]
                )
            )
        )

        return profile.astype(
            np.float32
        )

    @classmethod
    def _make_candidate(
        cls,
        original: np.ndarray,
        approach_index: int,
        rejoin_index: int,
        offset: float,
        side_sign: float,
        tangent_window: int,
        tangent_scale: float,
        spacing: float,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        start = original[
            approach_index
        ].astype(np.float32)

        end = original[
            rejoin_index
        ].astype(np.float32)

        chord = end - start

        chord_length = float(
            np.linalg.norm(chord)
        )

        if chord_length < 0.20:
            raise ValueError(
                "candidate_chord_too_short"
            )

        chord_unit = (
            chord / chord_length
        ).astype(np.float32)

        start_tangent = cls._path_tangent(
            original,
            approach_index,
            tangent_window,
        )

        end_tangent = cls._path_tangent(
            original,
            rejoin_index,
            tangent_window,
        )

        if float(
            np.dot(
                start_tangent,
                chord_unit,
            )
        ) < 0.0:
            start_tangent *= -1.0

        if float(
            np.dot(
                end_tangent,
                chord_unit,
            )
        ) < 0.0:
            end_tangent *= -1.0

        start_derivative = (
            start_tangent
            * chord_length
            * tangent_scale
        )

        end_derivative = (
            end_tangent
            * chord_length
            * tangent_scale
        )

        point_count = max(
            20,
            int(
                math.ceil(
                    chord_length
                    / spacing
                )
            )
            + 1,
        )

        parameter = np.linspace(
            0.0,
            1.0,
            point_count,
            dtype=np.float32,
        )

        u = parameter
        u2 = u * u
        u3 = u2 * u

        h00 = (
            2.0 * u3
            - 3.0 * u2
            + 1.0
        )

        h10 = (
            u3
            - 2.0 * u2
            + u
        )

        h01 = (
            -2.0 * u3
            + 3.0 * u2
        )

        h11 = (
            u3
            - u2
        )

        centerline = (
            h00[:, None] * start
            + h10[:, None]
            * start_derivative
            + h01[:, None] * end
            + h11[:, None]
            * end_derivative
        ).astype(np.float32)

        tangent = np.gradient(
            centerline,
            axis=0,
        ).astype(np.float32)

        tangent /= np.maximum(
            np.linalg.norm(
                tangent,
                axis=1,
                keepdims=True,
            ),
            1e-6,
        )

        for index in range(
            1,
            len(tangent),
        ):
            if float(
                np.dot(
                    tangent[index],
                    tangent[index - 1],
                )
            ) < 0.0:
                tangent[index] *= -1.0

        normal = np.stack(
            [
                -tangent[:, 1],
                tangent[:, 0],
            ],
            axis=1,
        ).astype(np.float32)

        profile = cls._c2_bump(
            parameter
        )

        shifted = (
            centerline
            + float(side_sign)
            * float(offset)
            * profile[:, None]
            * normal
        ).astype(np.float32)

        active_path = np.concatenate(
            [
                original[:approach_index],
                shifted,
                original[
                    rejoin_index + 1:
                ],
            ],
            axis=0,
        ).astype(np.float32)

        return (
            centerline,
            shifted,
            active_path,
        )

    @staticmethod
    def _reverse_steps(
        centerline: np.ndarray,
        candidate: np.ndarray,
    ) -> tuple[int, float]:
        centerline_vectors = np.diff(
            centerline,
            axis=0,
        )

        candidate_vectors = np.diff(
            candidate,
            axis=0,
        )

        centerline_vectors /= np.maximum(
            np.linalg.norm(
                centerline_vectors,
                axis=1,
                keepdims=True,
            ),
            1e-6,
        )

        candidate_vectors /= np.maximum(
            np.linalg.norm(
                candidate_vectors,
                axis=1,
                keepdims=True,
            ),
            1e-6,
        )

        alignment = np.sum(
            centerline_vectors
            * candidate_vectors,
            axis=1,
        )

        return (
            int(
                np.count_nonzero(
                    alignment < 0.0
                )
            ),
            float(
                np.min(alignment)
            ),
        )

    @staticmethod
    def _local_join_path(
        original: np.ndarray,
        approach_index: int,
        rejoin_index: int,
        shifted: np.ndarray,
    ) -> np.ndarray:
        prefix_start = max(
            0,
            approach_index - 8,
        )

        suffix_end = min(
            len(original),
            rejoin_index + 9,
        )

        return np.concatenate(
            [
                original[
                    prefix_start:
                    approach_index
                ],
                shifted,
                original[
                    rejoin_index + 1:
                    suffix_end
                ],
            ],
            axis=0,
        ).astype(np.float32)

    def plan(
        self,
        request: PlannerRequest,
        *,
        primary_result: PlannerResult,
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
                reason=(
                    "missing_runtime_parameter"
                ),
            )

        path_lookahead = float(
            request.path_lookahead
        )

        corridor_radius = float(
            request.corridor_radius
        )

        conflict_margin = float(
            request.conflict_margin
        )

        robot_radius = float(
            request.robot_radius
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

        conflict_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= path_lookahead + 0.50
            )
            & (
                sensor_path_distance
                < corridor_radius
                + conflict_margin
            )
        )

        if not np.any(conflict_mask):
            return PlannerResult.failed(
                original_path=original,
                reason=(
                    "no_corridor_sensor_cluster"
                ),
            )

        conflict_points = sensor_world[
            conflict_mask
        ]

        conflict_center = np.median(
            conflict_points,
            axis=0,
        ).astype(np.float32)

        conflict_index = int(
            primary_result.diagnostics.get(
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
            primary_result.diagnostics.get(
                "preferred_side",
                "RIGHT",
            )
        )

        preferred_side = (
            1.0
            if preferred_side_name == "LEFT"
            else -1.0
        )

        side_values = (
            preferred_side,
            -preferred_side,
        )

        candidate_count = 0
        feasible_count = 0
        best: dict[str, Any] | None = None
        seen_pairs: set[
            tuple[int, int]
        ] = set()

        for approach_distance in (
            self.APPROACH_DISTANCES
        ):
            approach_index = index_before(
                original,
                conflict_index,
                approach_distance,
            )

            for rejoin_distance in (
                self.REJOIN_DISTANCES
            ):
                rejoin_index = index_after(
                    original,
                    conflict_index,
                    rejoin_distance,
                )

                index_pair = (
                    approach_index,
                    rejoin_index,
                )

                if index_pair in seen_pairs:
                    continue

                seen_pairs.add(index_pair)

                if (
                    approach_index
                    >= conflict_index
                    or rejoin_index
                    <= conflict_index
                    or rejoin_index
                    >= len(original)
                ):
                    continue

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

                for spacing in self.SPACINGS:
                    for tangent_window in (
                        self.TANGENT_WINDOWS
                    ):
                        for tangent_scale in (
                            self.TANGENT_SCALES
                        ):
                            for side_sign in (
                                side_values
                            ):
                                for offset in (
                                    self.OFFSETS
                                ):
                                    try:
                                        (
                                            centerline,
                                            shifted,
                                            active_path,
                                        ) = (
                                            self._make_candidate(
                                                original,
                                                approach_index,
                                                rejoin_index,
                                                offset,
                                                side_sign,
                                                tangent_window,
                                                tangent_scale,
                                                spacing,
                                            )
                                        )
                                    except ValueError:
                                        continue

                                    candidate_count += 1

                                    metrics = (
                                        path_metrics(
                                            shifted,
                                            original_length,
                                        )
                                    )

                                    join_metrics = (
                                        path_metrics(
                                            self._local_join_path(
                                                original,
                                                approach_index,
                                                rejoin_index,
                                                shifted,
                                            ),
                                            original_length,
                                        )
                                    )

                                    candidate_known_margin = (
                                        known_margin(
                                            active_path,
                                            request.known_obstacles,
                                            robot_radius,
                                        )
                                    )

                                    distances = (
                                        point_segment_distances(
                                            conflict_points,
                                            shifted,
                                        )
                                    )

                                    candidate_sensor_margin = float(
                                        np.min(distances)
                                        - corridor_radius
                                    )

                                    (
                                        reverse_count,
                                        min_alignment,
                                    ) = self._reverse_steps(
                                        centerline,
                                        shifted,
                                    )

                                    feasible = bool(
                                        candidate_known_margin
                                        >= self.config.min_known_margin
                                        and candidate_sensor_margin
                                        >= self.config.min_sensor_margin
                                        and metrics[
                                            "p95_curvature"
                                        ]
                                        <= self.config.max_p95_curvature
                                        and metrics[
                                            "max_heading_delta"
                                        ]
                                        <= self.config.max_heading_delta
                                        and join_metrics[
                                            "max_heading_delta"
                                        ]
                                        <= self.config.max_heading_delta
                                        and reverse_count == 0
                                    )

                                    if not feasible:
                                        continue

                                    feasible_count += 1

                                    preference_bonus = (
                                        0.05
                                        if side_sign
                                        == preferred_side
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
                                        * metrics[
                                            "p95_curvature"
                                        ]
                                        - 0.60
                                        * metrics[
                                            "max_heading_delta"
                                        ]
                                        - 0.35
                                        * join_metrics[
                                            "max_heading_delta"
                                        ]
                                        - 0.30
                                        * max(
                                            0.0,
                                            metrics[
                                                "length_ratio"
                                            ]
                                            - 1.0,
                                        )
                                        - 0.05
                                        * offset
                                        + preference_bonus
                                    )

                                    candidate = {
                                        "score":
                                            float(score),
                                        "active_path":
                                            active_path,
                                        "known_margin":
                                            float(
                                                candidate_known_margin
                                            ),
                                        "sensor_margin":
                                            float(
                                                candidate_sensor_margin
                                            ),
                                        "p95_curvature":
                                            float(
                                                metrics[
                                                    "p95_curvature"
                                                ]
                                            ),
                                        "max_heading_delta":
                                            float(
                                                metrics[
                                                    "max_heading_delta"
                                                ]
                                            ),
                                        "join_max_heading_delta":
                                            float(
                                                join_metrics[
                                                    "max_heading_delta"
                                                ]
                                            ),
                                        "length_ratio":
                                            float(
                                                metrics[
                                                    "length_ratio"
                                                ]
                                            ),
                                        "offset":
                                            float(offset),
                                        "approach_distance":
                                            float(
                                                approach_distance
                                            ),
                                        "rejoin_distance":
                                            float(
                                                rejoin_distance
                                            ),
                                        "tangent_window":
                                            int(
                                                tangent_window
                                            ),
                                        "tangent_scale":
                                            float(
                                                tangent_scale
                                            ),
                                        "spacing":
                                            float(spacing),
                                        "side_sign":
                                            float(side_sign),
                                        "min_alignment":
                                            float(
                                                min_alignment
                                            ),
                                        "approach_point":
                                            original[
                                                approach_index
                                            ].copy(),
                                        "detour_point":
                                            shifted[
                                                len(shifted)
                                                // 2
                                            ].copy(),
                                        "rejoin_point":
                                            original[
                                                rejoin_index
                                            ].copy(),
                                    }

                                    if (
                                        best is None
                                        or candidate["score"]
                                        > best["score"]
                                    ):
                                        best = candidate

        common_diagnostics = {
            "fallback_used": True,
            "fallback_name":
                "hermite_c2",
            "conflict_index":
                conflict_index,
            "conflict_center":
                conflict_center.tolist(),
            "preferred_side":
                preferred_side_name,
            "unique_index_pairs":
                len(seen_pairs),
            "primary_failure_reason":
                primary_result.failure_reason,
            "primary_candidate_count":
                primary_result.candidate_count,
            "primary_feasible_count":
                primary_result.feasible_count,
        }

        if best is None:
            return PlannerResult(
                success=False,
                active_path=original,
                chosen_side="NONE",
                candidate_family=(
                    "phase21_v4_hermite_c2_fallback"
                ),
                failure_reason=(
                    "fallback_no_feasible_candidate"
                ),
                candidate_count=candidate_count,
                feasible_count=feasible_count,
                diagnostics=common_diagnostics,
            )

        chosen_side = (
            "LEFT"
            if best["side_sign"] > 0.0
            else "RIGHT"
        )

        diagnostics = dict(
            common_diagnostics
        )

        diagnostics.update({
            "length_ratio":
                best["length_ratio"],
            "offset":
                best["offset"],
            "approach_distance":
                best["approach_distance"],
            "rejoin_distance":
                best["rejoin_distance"],
            "tangent_window":
                best["tangent_window"],
            "tangent_scale":
                best["tangent_scale"],
            "spacing":
                best["spacing"],
            "join_max_heading_delta":
                best[
                    "join_max_heading_delta"
                ],
            "min_alignment":
                best["min_alignment"],
        })

        return PlannerResult(
            success=True,
            active_path=best["active_path"],
            chosen_side=chosen_side,
            candidate_family=(
                "phase21_v4_hermite_c2_fallback"
            ),
            failure_reason=None,
            known_margin=best["known_margin"],
            sensor_margin=best["sensor_margin"],
            p95_curvature=best[
                "p95_curvature"
            ],
            max_heading_delta=best[
                "max_heading_delta"
            ],
            score=best["score"],
            candidate_count=candidate_count,
            feasible_count=feasible_count,
            approach_point=best[
                "approach_point"
            ],
            detour_point=best[
                "detour_point"
            ],
            rejoin_point=best[
                "rejoin_point"
            ],
            diagnostics=diagnostics,
        )


__all__ = [
    "Phase21V4HermiteFallback",
]
