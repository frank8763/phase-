from __future__ import annotations

from typing import Any

import numpy as np

from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import (
    MkMiniPhase21V11CandidateRecoveryEnv,
)

from navigation.phase22.continuous_corridor_planner import (
    search_continuous_corridor,
)


class MkMiniPhase22V1ContinuousCorridorEnv(
    MkMiniPhase21V11CandidateRecoveryEnv
):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._phase22_clear_telemetry()

        super().__init__(
            **kwargs
        )

    def _phase22_clear_telemetry(
        self,
    ) -> None:
        self.phase22_v1_attempted = False
        self.phase22_v1_success = False
        self.phase22_v1_candidate_count = 0
        self.phase22_v1_failure_reason = "none"

        self.phase22_v1_selected_offset = float(
            "nan"
        )

        self.phase22_v1_selected_shoulder = float(
            "nan"
        )

        self.phase22_v1_selected_known_margin = float(
            "nan"
        )

        self.phase22_v1_selected_sensor_margin = float(
            "nan"
        )

        self.phase22_v1_selected_p95_curvature = float(
            "nan"
        )

        self.phase22_v1_selected_heading_delta = float(
            "nan"
        )

        self.phase22_v1_reverse_count = 0

    def reset(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self._phase22_clear_telemetry()

        return super().reset(
            *args,
            **kwargs,
        )

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        failed_before = int(
            getattr(
                self,
                "phase21_v4_failed_attempt_count",
                0,
            )
        )

        original_result = bool(
            super()._phase21_v3_build_detour()
        )

        if original_result:
            return True

        reason = str(
            getattr(
                self,
                "phase21_v3_failure_reason",
                "none",
            )
        )

        if reason != "no_feasible_candidate":
            return False

        self.phase22_v1_attempted = True

        original = getattr(
            self,
            "phase21_v3_original_path",
            None,
        )

        if (
            original is None
            or len(original) < 6
        ):
            self.phase22_v1_failure_reason = (
                "invalid_original_path"
            )

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
            self.phase22_v1_failure_reason = (
                "no_sensor_points"
            )

            return False

        robot_xy = np.asarray(
            self.robot_xy,
            dtype=np.float32,
        ).reshape(2)

        nearest_index = int(
            np.argmin(
                np.linalg.norm(
                    original - robot_xy,
                    axis=1,
                )
            )
        )

        future_path = original[
            nearest_index:
        ]

        if len(future_path) < 3:
            self.phase22_v1_failure_reason = (
                "future_path_too_short"
            )

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

        if not np.any(
            conflict_mask
        ):
            self.phase22_v1_failure_reason = (
                "no_corridor_sensor_cluster"
            )

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

        if tangent_norm <= 1e-6:
            self.phase22_v1_failure_reason = (
                "invalid_path_tangent"
            )

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
                - original[
                    conflict_index
                ],
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

        candidate, candidate_count = (
            search_continuous_corridor(
                env=self,
                original=original,
                sensor_points=sensor_world,
                conflict_points=(
                    conflict_points
                ),
                conflict_center=(
                    conflict_center
                ),
                conflict_index=(
                    conflict_index
                ),
                preferred_side=(
                    preferred_side
                ),
            )
        )

        self.phase22_v1_candidate_count = int(
            candidate_count
        )

        if candidate is None:
            self.phase22_v1_failure_reason = (
                "no_continuous_corridor"
            )

            self.phase21_v3_failure_reason = (
                "no_continuous_corridor"
            )

            self.phase21_v4_last_attempt_reason = (
                "no_continuous_corridor"
            )

            self.phase21_v4_persistent_failure_reason = (
                "no_continuous_corridor"
            )

            self.phase21_v4_failed_attempt_count = (
                failed_before + 1
            )

            return False

        changed = (
            self._phase21_v3_apply_path(
                candidate.active_path
            )
        )

        if changed <= 0:
            self.phase22_v1_failure_reason = (
                "no_runtime_path_owner"
            )

            self.phase21_v3_failure_reason = (
                "no_runtime_path_owner"
            )

            return False

        self.phase21_v3_active_path = (
            candidate.active_path.copy()
        )

        self.phase21_v3_conflict_center = (
            conflict_center.copy()
        )

        self.phase21_v3_approach_point = (
            candidate.local_curve[0].copy()
        )

        self.phase21_v3_detour_point = (
            candidate.local_curve[
                len(
                    candidate.local_curve
                )
                // 2
            ].copy()
        )

        self.phase21_v3_rejoin_point = (
            candidate.local_curve[-1].copy()
        )

        self.phase21_v3_chosen_side = (
            "LEFT"
            if candidate.side_sign > 0.0
            else "RIGHT"
        )

        self.phase21_v3_detour_applied = True
        self.phase21_v3_apply_count += 1
        self.phase21_v3_failure_reason = "none"

        self.phase21_v4_last_attempt_reason = (
            "phase22_continuous_success"
        )

        self.phase21_v4_persistent_failure_reason = (
            "none"
        )

        self.phase21_v4_failed_attempt_count = (
            failed_before
        )

        self.phase21_v4_candidate_count = int(
            candidate_count
        )

        self.phase21_v4_feasible_count = 1

        self.phase21_v4_selected_known_margin = float(
            candidate.known_margin
        )

        self.phase21_v4_selected_sensor_margin = float(
            candidate.sensor_margin
        )

        self.phase21_v4_selected_p95_curvature = float(
            candidate.p95_curvature
        )

        self.phase21_v4_selected_max_heading_delta = float(
            candidate.max_heading_delta
        )

        self.phase21_v4_selected_length_ratio = float(
            candidate.length_ratio
        )

        self.phase21_v4_selected_offset = float(
            candidate.offset
        )

        self.phase21_v4_selected_approach_distance = float(
            candidate.approach_distance
        )

        self.phase21_v4_selected_rejoin_distance = float(
            candidate.rejoin_distance
        )

        self.phase21_v4_selected_side = str(
            self.phase21_v3_chosen_side
        )

        self.phase22_v1_success = True
        self.phase22_v1_failure_reason = "none"

        self.phase22_v1_selected_offset = float(
            candidate.offset
        )

        self.phase22_v1_selected_shoulder = float(
            candidate.shoulder
        )

        self.phase22_v1_selected_known_margin = float(
            candidate.known_margin
        )

        self.phase22_v1_selected_sensor_margin = float(
            candidate.sensor_margin
        )

        self.phase22_v1_selected_p95_curvature = float(
            candidate.p95_curvature
        )

        self.phase22_v1_selected_heading_delta = float(
            candidate.max_heading_delta
        )

        self.phase22_v1_reverse_count = int(
            candidate.reverse_count
        )

        return True

    def _phase21_v3_fill_info(
        self,
        info,
    ):
        info = super()._phase21_v3_fill_info(
            info
        )

        info.update({
            "phase22_v1_attempted":
                bool(
                    self.phase22_v1_attempted
                ),
            "phase22_v1_success":
                bool(
                    self.phase22_v1_success
                ),
            "phase22_v1_candidate_count":
                int(
                    self.phase22_v1_candidate_count
                ),
            "phase22_v1_failure_reason":
                str(
                    self.phase22_v1_failure_reason
                ),
            "phase22_v1_selected_offset":
                float(
                    self.phase22_v1_selected_offset
                ),
            "phase22_v1_selected_shoulder":
                float(
                    self.phase22_v1_selected_shoulder
                ),
            "phase22_v1_selected_known_margin":
                float(
                    self.phase22_v1_selected_known_margin
                ),
            "phase22_v1_selected_sensor_margin":
                float(
                    self.phase22_v1_selected_sensor_margin
                ),
            "phase22_v1_selected_p95_curvature":
                float(
                    self.phase22_v1_selected_p95_curvature
                ),
            "phase22_v1_selected_heading_delta":
                float(
                    self.phase22_v1_selected_heading_delta
                ),
            "phase22_v1_reverse_count":
                int(
                    self.phase22_v1_reverse_count
                ),
        })

        return info


__all__ = [
    "MkMiniPhase22V1ContinuousCorridorEnv",
]
