from __future__ import annotations

from typing import Any

import numpy as np

from envs.phase21.mkmini_phase21_v4_shadow_compare_env import (
    build_planner_request_from_env,
)
from envs.phase21.mkmini_phase21_v7_adaptive_takeover_env import (
    MkMiniPhase21V7AdaptiveTakeoverEnv,
)
from navigation.phase21.local_planners.phase21_v4_geometry import (
    point_segment_distances,
)


class MkMiniPhase21V8RuntimeRevalidateEnv(
    MkMiniPhase21V7AdaptiveTakeoverEnv
):
    """
    Phase21 v8运行时路径有效性监督。

    在v7基础上增加：
    1. 使用最新传感器点验证活动路径；
    2. 连续两步低于正式安全阈值时重新规划；
    3. 使用冷却时间和最大次数抑制反复振荡。

    不调用局部A*。
    不使用未知障碍真值。
    不重新训练Phase20 SAC。
    """

    REVALIDATE_THRESHOLD = 0.025
    REVALIDATE_CONFIRM_STEPS = 2
    REVALIDATE_COOLDOWN_STEPS = 4
    REVALIDATE_MAX_REPLANS = 3

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        self.phase21_v8_step = 0
        self.phase21_v8_unsafe_streak = 0
        self.phase21_v8_replan_count = 0
        self.phase21_v8_replan_success_count = 0
        self.phase21_v8_replan_failure_count = 0

        self.phase21_v8_last_replan_step = (
            -self.REVALIDATE_COOLDOWN_STEPS
        )

        self.phase21_v8_last_margin = float(
            "inf"
        )

        self.phase21_v8_last_margin_after_replan = (
            float("inf")
        )

        self.phase21_v8_last_replan_route = "none"
        self.phase21_v8_last_replan_family = "none"
        self.phase21_v8_last_replan_reason = "none"

    def _phase21_v8_future_sensor_margin(
        self,
    ) -> float | None:
        active_path = getattr(
            self,
            "phase21_v3_active_path",
            None,
        )

        if active_path is None:
            return None

        active_path = np.asarray(
            active_path,
            dtype=np.float64,
        ).reshape(-1, 2)

        if len(active_path) < 2:
            return None

        request = build_planner_request_from_env(
            self
        )

        sensor_world = np.asarray(
            request.sensor_points_world,
            dtype=np.float64,
        ).reshape(-1, 2)

        sensor_local = np.asarray(
            request.sensor_points_local,
            dtype=np.float64,
        ).reshape(-1, 2)

        if len(sensor_world) == 0:
            return float("inf")

        robot_xy = np.asarray(
            request.robot_pose[:2],
            dtype=np.float64,
        )

        nearest_index = int(
            np.argmin(
                np.linalg.norm(
                    active_path - robot_xy,
                    axis=1,
                )
            )
        )

        future_path = active_path[
            nearest_index:
        ]

        if len(future_path) < 2:
            return float("inf")

        point_count = min(
            len(sensor_world),
            len(sensor_local),
        )

        sensor_world = sensor_world[
            :point_count
        ]

        sensor_local = sensor_local[
            :point_count
        ]

        lookahead = float(
            request.path_lookahead
        )

        valid_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= lookahead + 0.50
            )
        )

        if not np.any(valid_mask):
            return float("inf")

        distances = point_segment_distances(
            sensor_world[valid_mask],
            future_path,
        )

        return float(
            np.min(distances)
            - float(
                request.corridor_radius
            )
        )

    def _phase21_v8_replan(
        self,
        margin_before: float,
    ) -> bool:
        request = build_planner_request_from_env(
            self
        )

        result = self._phase21_v7_planner.plan(
            request
        )

        self.phase21_v8_replan_count += 1
        self.phase21_v8_last_replan_step = (
            self.phase21_v8_step
        )

        self.phase21_v8_last_replan_route = str(
            result.diagnostics.get(
                "phase21_v7_route",
                "unknown",
            )
        )

        self.phase21_v8_last_replan_family = str(
            result.candidate_family
        )

        if not result.success:
            self.phase21_v8_replan_failure_count += 1

            self.phase21_v8_last_replan_reason = str(
                result.failure_reason
                or "unknown"
            )

            print(
                "[Phase21-v8 revalidate failure]",
                f"step={self.phase21_v8_step}",
                f"margin={margin_before:.4f}",
                f"reason={self.phase21_v8_last_replan_reason}",
            )

            return False

        self._phase21_write_planner_result(
            result
        )

        self.phase21_v8_replan_success_count += 1
        self.phase21_v8_last_replan_reason = "none"

        # 保持v7统计口径一致。
        self.phase21_v7_takeover_count += 1

        route = self.phase21_v8_last_replan_route

        if route == "primary_success":
            self.phase21_v7_primary_count += 1

        elif route == "fallback_success":
            self.phase21_v7_hermite_count += 1

        elif route == "cluster_bspline_success":
            self.phase21_v7_bspline_count += 1

        self.phase21_v7_last_route = route
        self.phase21_v7_last_family = str(
            result.candidate_family
        )

        margin_after = (
            self._phase21_v8_future_sensor_margin()
        )

        if margin_after is None:
            margin_after = float("nan")

        self.phase21_v8_last_margin_after_replan = (
            float(margin_after)
        )

        print(
            "[Phase21-v8 runtime replan]",
            f"step={self.phase21_v8_step}",
            f"before={margin_before:.4f}",
            f"after={margin_after:.4f}",
            f"route={route}",
            f"family={result.candidate_family}",
            f"side={result.chosen_side}",
            f"known={result.known_margin:.4f}",
            f"sensor={result.sensor_margin:.4f}",
            f"p95={result.p95_curvature:.4f}",
        )

        return True

    def step(
        self,
        action: Any,
    ):
        margin = (
            self._phase21_v8_future_sensor_margin()
        )

        if margin is not None:
            self.phase21_v8_last_margin = float(
                margin
            )

        has_active_detour = bool(
            getattr(
                self,
                "phase21_v3_detour_applied",
                False,
            )
        )

        if (
            has_active_detour
            and margin is not None
            and np.isfinite(margin)
        ):
            if (
                margin
                < self.REVALIDATE_THRESHOLD
            ):
                self.phase21_v8_unsafe_streak += 1
            else:
                self.phase21_v8_unsafe_streak = 0

            cooldown_ready = (
                self.phase21_v8_step
                - self.phase21_v8_last_replan_step
                >= self.REVALIDATE_COOLDOWN_STEPS
            )

            count_ready = (
                self.phase21_v8_replan_count
                < self.REVALIDATE_MAX_REPLANS
            )

            confirmed_unsafe = (
                self.phase21_v8_unsafe_streak
                >= self.REVALIDATE_CONFIRM_STEPS
            )

            if (
                cooldown_ready
                and count_ready
                and confirmed_unsafe
            ):
                self._phase21_v8_replan(
                    float(margin)
                )

                self.phase21_v8_unsafe_streak = 0

        result = super().step(action)

        self.phase21_v8_step += 1

        if (
            isinstance(result, tuple)
            and len(result) >= 4
            and isinstance(result[-1], dict)
        ):
            info = result[-1]

            info.update({
                "phase21_v8_step":
                    int(
                        self.phase21_v8_step
                    ),
                "phase21_v8_last_margin":
                    float(
                        self.phase21_v8_last_margin
                    ),
                "phase21_v8_unsafe_streak":
                    int(
                        self.phase21_v8_unsafe_streak
                    ),
                "phase21_v8_replan_count":
                    int(
                        self.phase21_v8_replan_count
                    ),
                "phase21_v8_replan_success_count":
                    int(
                        self.phase21_v8_replan_success_count
                    ),
                "phase21_v8_replan_failure_count":
                    int(
                        self.phase21_v8_replan_failure_count
                    ),
                "phase21_v8_last_replan_step":
                    int(
                        self.phase21_v8_last_replan_step
                    ),
                "phase21_v8_last_margin_after_replan":
                    float(
                        self.phase21_v8_last_margin_after_replan
                    ),
                "phase21_v8_last_replan_route":
                    str(
                        self.phase21_v8_last_replan_route
                    ),
                "phase21_v8_last_replan_family":
                    str(
                        self.phase21_v8_last_replan_family
                    ),
                "phase21_v8_last_replan_reason":
                    str(
                        self.phase21_v8_last_replan_reason
                    ),
                "phase21_v8_uses_local_astar":
                    False,
            })

        return result


MkMiniPhase21RiskSwitchFusionSACEnv = (
    MkMiniPhase21V8RuntimeRevalidateEnv
)


__all__ = [
    "MkMiniPhase21V8RuntimeRevalidateEnv",
    "MkMiniPhase21RiskSwitchFusionSACEnv",
]
