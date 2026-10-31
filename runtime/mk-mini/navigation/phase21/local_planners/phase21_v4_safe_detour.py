#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any

import mujoco
import numpy as np

from training.phase21_risk_switch_fusion_sac.envs.mkmini_phase21_v3_exact_pair_baseline import (
    MkMiniPhase21RiskSwitchFusionSACEnv as Phase21V3ExactPairEnv,
)


class MkMiniPhase21RiskSwitchFusionSACEnv(
    Phase21V3ExactPairEnv
):
    """
    Phase21 v4：

    传感器检测路径走廊冲突后，不再只生成一条二次Bezier曲线，
    而是生成左右两侧、不同偏移量和不同重汇入距离的多条候选路径。

    候选筛选只使用：
        1. LiDAR和Depth障碍点；
        2. 已知静态地图中的real_rect_obs / real_circle_obs；
        3. 原A*路径和机器人状态。

    不使用：
        phase19_unknown_circles
        未知障碍圆心
        未知障碍半径
        未知障碍几何ID

    候选路径使用原路径的平滑横向偏移：
        offset(u) = A * sin(pi*u)^2

    该函数在接入点和退出点满足：
        offset = 0
        offset导数 = 0

    相比原二次Bezier，可明显减小路径连接处的航向突变。
    """

    def __init__(
        self,
        *,
        phase21_v4_offsets=(
            0.34,
            0.44,
            0.54,
            0.64,
        ),
        phase21_v4_approach_distances=(
            0.45,
            0.70,
            0.95,
        ),
        phase21_v4_rejoin_distances=(
            1.20,
            1.60,
            2.00,
            2.40,
        ),
        phase21_v4_min_known_margin: float = 0.06,
        phase21_v4_min_sensor_margin: float = 0.025,
        phase21_v4_max_p95_curvature: float = 1.80,
        phase21_v4_max_heading_delta: float = 0.24,
        **kwargs: Any,
    ) -> None:
        self.phase21_v4_offsets = tuple(
            float(value)
            for value in phase21_v4_offsets
        )

        self.phase21_v4_approach_distances = tuple(
            float(value)
            for value in phase21_v4_approach_distances
        )

        self.phase21_v4_rejoin_distances = tuple(
            float(value)
            for value in phase21_v4_rejoin_distances
        )

        self.phase21_v4_min_known_margin = float(
            phase21_v4_min_known_margin
        )

        self.phase21_v4_min_sensor_margin = float(
            phase21_v4_min_sensor_margin
        )

        self.phase21_v4_max_p95_curvature = float(
            phase21_v4_max_p95_curvature
        )

        self.phase21_v4_max_heading_delta = float(
            phase21_v4_max_heading_delta
        )

        self._phase21_v4_clear_telemetry()

        super().__init__(**kwargs)

    def _phase21_v4_clear_telemetry(
        self,
    ) -> None:
        self.phase21_v4_candidate_count = 0
        self.phase21_v4_feasible_count = 0

        self.phase21_v4_selected_score = float(
            "-inf"
        )

        self.phase21_v4_selected_known_margin = float(
            "-inf"
        )

        self.phase21_v4_selected_sensor_margin = float(
            "-inf"
        )

        self.phase21_v4_selected_p95_curvature = float(
            "inf"
        )

        self.phase21_v4_selected_max_heading_delta = float(
            "inf"
        )

        self.phase21_v4_selected_length_ratio = float(
            "inf"
        )

        self.phase21_v4_selected_offset = 0.0
        self.phase21_v4_selected_approach_distance = 0.0
        self.phase21_v4_selected_rejoin_distance = 0.0
        self.phase21_v4_selected_side = "NONE"

        self.phase21_v4_attempt_count = 0
        self.phase21_v4_failed_attempt_count = 0
        self.phase21_v4_last_attempt_reason = "none"
        self.phase21_v4_persistent_failure_reason = "none"

    # ------------------------------------------------------------------
    # 已知静态地图
    # ------------------------------------------------------------------

    def _phase21_v4_known_map_obstacles(
        self,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        只从明确命名为real_rect_obs和real_circle_obs的静态地图几何体
        构造已知障碍数组。

        隐藏未知障碍不使用这些名称，因此不会进入候选路径安全筛选。
        """

        rectangles = []
        circles = []

        model = self.model

        for geom_id in range(model.ngeom):
            name = mujoco.mj_id2name(
                model,
                mujoco.mjtObj.mjOBJ_GEOM,
                geom_id,
            )

            if not name:
                continue

            lowered = name.lower()

            if not (
                "real_rect_obs" in lowered
                or "real_circle_obs" in lowered
            ):
                continue

            if (
                int(model.geom_contype[geom_id]) == 0
                and int(
                    model.geom_conaffinity[geom_id]
                ) == 0
            ):
                continue

            if float(
                model.geom_rgba[geom_id][3]
            ) <= 0.01:
                continue

            if float(
                model.geom_pos[geom_id][2]
            ) < -1.0:
                continue

            x = float(
                model.geom_pos[geom_id][0]
            )

            y = float(
                model.geom_pos[geom_id][1]
            )

            if "real_rect_obs" in lowered:
                half_x = float(
                    model.geom_size[geom_id][0]
                )

                half_y = float(
                    model.geom_size[geom_id][1]
                )

                rectangles.append(
                    [
                        x,
                        y,
                        half_x,
                        half_y,
                    ]
                )

            elif "real_circle_obs" in lowered:
                radius = float(
                    model.geom_size[geom_id][0]
                )

                circles.append(
                    [
                        x,
                        y,
                        radius,
                    ]
                )

        return (
            np.asarray(
                rectangles,
                dtype=np.float32,
            ).reshape(-1, 4),
            np.asarray(
                circles,
                dtype=np.float32,
            ).reshape(-1, 3),
        )

    @staticmethod
    def _phase21_v4_densify(
        path: np.ndarray,
        spacing: float = 0.025,
    ) -> np.ndarray:
        path = np.asarray(
            path,
            dtype=np.float32,
        ).reshape(-1, 2)

        if len(path) < 2:
            return path.copy()

        pieces = []

        for index in range(len(path) - 1):
            start = path[index]
            end = path[index + 1]

            length = float(
                np.linalg.norm(
                    end - start
                )
            )

            count = max(
                2,
                int(
                    math.ceil(
                        length
                        / max(
                            spacing,
                            1e-4,
                        )
                    )
                )
                + 1,
            )

            segment = np.linspace(
                start,
                end,
                count,
                dtype=np.float32,
            )

            if index > 0:
                segment = segment[1:]

            pieces.append(segment)

        return np.concatenate(
            pieces,
            axis=0,
        ).astype(np.float32)

    def _phase21_v4_known_margin(
        self,
        path: np.ndarray,
    ) -> float:
        dense = self._phase21_v4_densify(
            path
        )

        rectangles, circles = (
            self._phase21_v4_known_map_obstacles()
        )

        robot_radius = float(
            getattr(
                self,
                "robot_radius",
                0.28,
            )
        )

        margins = []

        if len(circles) > 0:
            distances = np.linalg.norm(
                dense[:, None, :]
                - circles[None, :, :2],
                axis=2,
            )

            circle_margin = (
                distances
                - circles[None, :, 2]
                - robot_radius
            )

            margins.append(
                float(
                    np.min(
                        circle_margin
                    )
                )
            )

        if len(rectangles) > 0:
            centers = rectangles[:, :2]
            half_sizes = rectangles[:, 2:4]

            delta = (
                np.abs(
                    dense[:, None, :]
                    - centers[None, :, :]
                )
                - half_sizes[None, :, :]
            )

            outside = np.maximum(
                delta,
                0.0,
            )

            distances = np.linalg.norm(
                outside,
                axis=2,
            )

            rectangle_margin = (
                distances
                - robot_radius
            )

            margins.append(
                float(
                    np.min(
                        rectangle_margin
                    )
                )
            )

        if not margins:
            return float("inf")

        return float(min(margins))

    # ------------------------------------------------------------------
    # 候选路径几何
    # ------------------------------------------------------------------

    @staticmethod
    def _phase21_v4_path_metrics(
        path: np.ndarray,
        original_length: float,
    ) -> dict[str, float]:
        path = np.asarray(
            path,
            dtype=np.float32,
        ).reshape(-1, 2)

        vectors = np.diff(
            path,
            axis=0,
        )

        lengths = np.linalg.norm(
            vectors,
            axis=1,
        )

        valid = lengths > 1e-5

        vectors = vectors[valid]
        lengths = lengths[valid]

        if len(vectors) < 2:
            return {
                "length": float("inf"),
                "length_ratio": float("inf"),
                "max_heading_delta": float("inf"),
                "p95_curvature": float("inf"),
            }

        headings = np.unwrap(
            np.arctan2(
                vectors[:, 1],
                vectors[:, 0],
            )
        )

        heading_delta = np.abs(
            np.diff(headings)
        )

        mean_segment_length = 0.5 * (
            lengths[:-1]
            + lengths[1:]
        )

        curvature = (
            heading_delta
            / np.maximum(
                mean_segment_length,
                1e-5,
            )
        )

        total_length = float(
            np.sum(lengths)
        )

        return {
            "length": total_length,
            "length_ratio": float(
                total_length
                / max(
                    original_length,
                    1e-6,
                )
            ),
            "max_heading_delta": float(
                np.max(heading_delta)
            ),
            "p95_curvature": float(
                np.percentile(
                    curvature,
                    95.0,
                )
            ),
        }

    def _phase21_v4_make_candidate(
        self,
        original: np.ndarray,
        approach_index: int,
        rejoin_index: int,
        offset: float,
        side_sign: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        segment = original[
            approach_index:
            rejoin_index + 1
        ].copy()

        if len(segment) < 5:
            raise ValueError(
                "candidate segment too short"
            )

        segment_vectors = np.diff(
            segment,
            axis=0,
        )

        segment_lengths = np.linalg.norm(
            segment_vectors,
            axis=1,
        )

        cumulative = np.concatenate(
            [
                np.zeros(
                    1,
                    dtype=np.float32,
                ),
                np.cumsum(
                    segment_lengths
                ).astype(np.float32),
            ]
        )

        total = float(
            cumulative[-1]
        )

        if total < 0.20:
            raise ValueError(
                "candidate segment length too short"
            )

        parameter = cumulative / total

        tangent = np.gradient(
            segment,
            axis=0,
        )

        tangent_norm = np.linalg.norm(
            tangent,
            axis=1,
            keepdims=True,
        )

        tangent = tangent / np.maximum(
            tangent_norm,
            1e-6,
        )

        normal = np.stack(
            [
                -tangent[:, 1],
                tangent[:, 0],
            ],
            axis=1,
        )

        # 两端偏移和偏移导数均为零。
        profile = np.sin(
            math.pi * parameter
        ) ** 2

        shifted_segment = (
            segment
            + float(side_sign)
            * float(offset)
            * profile[:, None]
            * normal
        ).astype(np.float32)

        active_path = np.concatenate(
            [
                original[:approach_index],
                shifted_segment,
                original[
                    rejoin_index + 1:
                ],
            ],
            axis=0,
        ).astype(np.float32)

        return (
            shifted_segment,
            active_path,
        )

    # ------------------------------------------------------------------
    # 多候选绕行
    # ------------------------------------------------------------------

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        self.phase21_v4_attempt_count += 1
        self.phase21_v4_last_attempt_reason = "attempt_started"

        original = self.phase21_v3_original_path

        if (
            original is None
            or len(original) < 6
        ):
            self.phase21_v3_failure_reason = (
                "invalid_original_path"
            )
            self.phase21_v4_last_attempt_reason = (
                "invalid_original_path"
            )
            self.phase21_v4_persistent_failure_reason = (
                "invalid_original_path"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        original = np.asarray(
            original,
            dtype=np.float32,
        ).reshape(-1, 2)

        (
            sensor_world,
            sensor_local,
        ) = self._phase21_sensor_points()

        if len(sensor_world) == 0:
            self.phase21_v3_failure_reason = (
                "no_sensor_points"
            )
            self.phase21_v4_last_attempt_reason = (
                "no_sensor_points"
            )
            self.phase21_v4_persistent_failure_reason = (
                "no_sensor_points"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        robot_xy = np.asarray(
            self.robot_xy,
            dtype=np.float32,
        ).reshape(2)

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

        if len(future_path) < 3:
            self.phase21_v3_failure_reason = (
                "future_path_too_short"
            )
            self.phase21_v4_last_attempt_reason = (
                "future_path_too_short"
            )
            self.phase21_v4_persistent_failure_reason = (
                "future_path_too_short"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        sensor_path_distance = (
            self._phase21_point_segment_distances(
                sensor_world,
                future_path,
            )
        )

        conflict_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= self.phase21_path_lookahead
                + 0.50
            )
            & (
                sensor_path_distance
                < self.phase21_corridor_radius
                + self.phase21_v3_conflict_margin
            )
        )

        if not np.any(conflict_mask):
            self.phase21_v3_failure_reason = (
                "no_corridor_sensor_cluster"
            )
            self.phase21_v4_last_attempt_reason = (
                "no_corridor_sensor_cluster"
            )
            self.phase21_v4_persistent_failure_reason = (
                "no_corridor_sensor_cluster"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        conflict_points = sensor_world[
            conflict_mask
        ]

        conflict_center = np.median(
            conflict_points,
            axis=0,
        ).astype(np.float32)

        conflict_index = int(
            np.argmin(
                np.linalg.norm(
                    original
                    - conflict_center,
                    axis=1,
                )
            )
        )

        tangent_start = max(
            0,
            conflict_index - 2,
        )

        tangent_end = min(
            len(original) - 1,
            conflict_index + 2,
        )

        tangent = (
            original[tangent_end]
            - original[tangent_start]
        )

        tangent_norm = float(
            np.linalg.norm(tangent)
        )

        if tangent_norm < 1e-6:
            self.phase21_v3_failure_reason = (
                "invalid_path_tangent"
            )
            self.phase21_v4_last_attempt_reason = (
                "invalid_path_tangent"
            )
            self.phase21_v4_persistent_failure_reason = (
                "invalid_path_tangent"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        tangent = tangent / tangent_norm

        left_normal = np.asarray(
            [
                -tangent[1],
                tangent[0],
            ],
            dtype=np.float32,
        )

        obstacle_lateral = float(
            np.dot(
                conflict_center
                - original[conflict_index],
                left_normal,
            )
        )

        if obstacle_lateral > 0.03:
            preferred_side = -1.0
        elif obstacle_lateral < -0.03:
            preferred_side = 1.0
        elif (
            self.phase21_last_left_min
            > self.phase21_last_right_min
        ):
            preferred_side = 1.0
        else:
            preferred_side = -1.0

        side_values = (
            preferred_side,
            -preferred_side,
        )

        best = None
        candidate_count = 0
        feasible_count = 0

        for approach_distance in (
            self.phase21_v4_approach_distances
        ):
            approach_index = (
                self._phase21_v3_index_before(
                    original,
                    conflict_index,
                    approach_distance,
                )
            )

            for rejoin_distance in (
                self.phase21_v4_rejoin_distances
            ):
                rejoin_index = (
                    self._phase21_v3_index_after(
                        original,
                        conflict_index,
                        rejoin_distance,
                    )
                )

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

                original_segment_length = float(
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

                for side_sign in side_values:
                    for offset in (
                        self.phase21_v4_offsets
                    ):
                        candidate_count += 1

                        try:
                            (
                                shifted_segment,
                                active_path,
                            ) = (
                                self._phase21_v4_make_candidate(
                                    original,
                                    approach_index,
                                    rejoin_index,
                                    offset,
                                    side_sign,
                                )
                            )
                        except Exception:
                            continue

                        known_margin = (
                            self._phase21_v4_known_margin(
                                active_path
                            )
                        )

                        sensor_distance = (
                            self._phase21_point_segment_distances(
                                conflict_points,
                                shifted_segment,
                            )
                        )

                        sensor_margin = float(
                            np.min(sensor_distance)
                            - self.phase21_corridor_radius
                        )

                        metrics = (
                            self._phase21_v4_path_metrics(
                                shifted_segment,
                                original_segment_length,
                            )
                        )

                        feasible = bool(
                            known_margin
                            >= self.phase21_v4_min_known_margin
                            and sensor_margin
                            >= self.phase21_v4_min_sensor_margin
                            and metrics[
                                "p95_curvature"
                            ]
                            <= self.phase21_v4_max_p95_curvature
                            and metrics[
                                "max_heading_delta"
                            ]
                            <= self.phase21_v4_max_heading_delta
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
                                sensor_margin,
                                0.50,
                            )
                            + 2.0
                            * min(
                                known_margin,
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
                            "score": float(score),
                            "active_path":
                                active_path,
                            "known_margin":
                                float(
                                    known_margin
                                ),
                            "sensor_margin":
                                float(
                                    sensor_margin
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
                            "side_sign":
                                float(side_sign),
                            "approach_point":
                                original[
                                    approach_index
                                ].copy(),
                            "detour_point":
                                shifted_segment[
                                    len(
                                        shifted_segment
                                    )
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

        self.phase21_v4_candidate_count = int(
            candidate_count
        )

        self.phase21_v4_feasible_count = int(
            feasible_count
        )

        if best is None:
            self.phase21_v3_failure_reason = (
                "no_feasible_candidate"
            )
            self.phase21_v4_last_attempt_reason = (
                "no_feasible_candidate"
            )
            self.phase21_v4_persistent_failure_reason = (
                "no_feasible_candidate"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        changed = self._phase21_v3_apply_path(
            best["active_path"]
        )

        if changed <= 0:
            self.phase21_v3_failure_reason = (
                "no_runtime_path_owner"
            )
            self.phase21_v4_last_attempt_reason = (
                "no_runtime_path_owner"
            )
            self.phase21_v4_persistent_failure_reason = (
                "no_runtime_path_owner"
            )
            self.phase21_v4_failed_attempt_count += 1
            return False

        self.phase21_v3_active_path = (
            best["active_path"].copy()
        )

        self.phase21_v3_conflict_center = (
            conflict_center.copy()
        )

        self.phase21_v3_approach_point = (
            best["approach_point"].copy()
        )

        self.phase21_v3_detour_point = (
            best["detour_point"].copy()
        )

        self.phase21_v3_rejoin_point = (
            best["rejoin_point"].copy()
        )

        self.phase21_v3_chosen_side = (
            "LEFT"
            if best["side_sign"] > 0.0
            else "RIGHT"
        )

        self.phase21_v3_detour_applied = True
        self.phase21_v3_apply_count += 1
        self.phase21_v3_failure_reason = "none"
        self.phase21_v4_last_attempt_reason = "success"
        self.phase21_v4_persistent_failure_reason = "none"

        self.phase21_v4_selected_score = float(
            best["score"]
        )

        self.phase21_v4_selected_known_margin = float(
            best["known_margin"]
        )

        self.phase21_v4_selected_sensor_margin = float(
            best["sensor_margin"]
        )

        self.phase21_v4_selected_p95_curvature = float(
            best["p95_curvature"]
        )

        self.phase21_v4_selected_max_heading_delta = float(
            best["max_heading_delta"]
        )

        self.phase21_v4_selected_length_ratio = float(
            best["length_ratio"]
        )

        self.phase21_v4_selected_offset = float(
            best["offset"]
        )

        self.phase21_v4_selected_approach_distance = float(
            best["approach_distance"]
        )

        self.phase21_v4_selected_rejoin_distance = float(
            best["rejoin_distance"]
        )

        self.phase21_v4_selected_side = str(
            self.phase21_v3_chosen_side
        )

        return True

    def _phase21_v3_fill_info(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        output = super()._phase21_v3_fill_info(
            info
        )

        output.update({
            "phase21_version":
                "v4_candidate_safe_local_reference",
            "phase21_v4_candidate_count":
                int(
                    self.phase21_v4_candidate_count
                ),
            "phase21_v4_feasible_count":
                int(
                    self.phase21_v4_feasible_count
                ),
            "phase21_v4_selected_score":
                float(
                    self.phase21_v4_selected_score
                ),
            "phase21_v4_selected_known_margin":
                float(
                    self.phase21_v4_selected_known_margin
                ),
            "phase21_v4_selected_sensor_margin":
                float(
                    self.phase21_v4_selected_sensor_margin
                ),
            "phase21_v4_selected_p95_curvature":
                float(
                    self.phase21_v4_selected_p95_curvature
                ),
            "phase21_v4_selected_max_heading_delta":
                float(
                    self.phase21_v4_selected_max_heading_delta
                ),
            "phase21_v4_selected_length_ratio":
                float(
                    self.phase21_v4_selected_length_ratio
                ),
            "phase21_v4_selected_offset":
                float(
                    self.phase21_v4_selected_offset
                ),
            "phase21_v4_selected_approach_distance":
                float(
                    self.phase21_v4_selected_approach_distance
                ),
            "phase21_v4_selected_rejoin_distance":
                float(
                    self.phase21_v4_selected_rejoin_distance
                ),
            "phase21_v4_selected_side":
                str(
                    self.phase21_v4_selected_side
                ),
            "phase21_v4_known_map_only":
                True,
            "phase21_v4_unknown_truth_used":
                False,
            "phase21_v4_attempt_count":
                int(
                    self.phase21_v4_attempt_count
                ),
            "phase21_v4_failed_attempt_count":
                int(
                    self.phase21_v4_failed_attempt_count
                ),
            "phase21_v4_last_attempt_reason":
                str(
                    self.phase21_v4_last_attempt_reason
                ),
            "phase21_v4_persistent_failure_reason":
                str(
                    self.phase21_v4_persistent_failure_reason
                ),
        })

        return output

    def reset(
        self,
        *args,
        **kwargs,
    ):
        self._phase21_v4_clear_telemetry()

        return super().reset(
            *args,
            **kwargs,
        )
