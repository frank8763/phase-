from __future__ import annotations

from typing import Any

import numpy as np

from envs.phase21.mkmini_phase21_v4_shadow_compare_env import (
    build_planner_request_from_env,
    phase21_v4_config_from_env,
)
from envs.phase21.mkmini_phase21_v8_runtime_revalidate_env import (
    MkMiniPhase21V8RuntimeRevalidateEnv,
)
from navigation.phase21.local_planners.phase21_v4_geometry import (
    point_segment_distances,
)
from navigation.phase21.local_planners.phase21_v8_adaptive_runtime_safe import (
    Phase21V8AdaptiveRuntimeSafePlanner,
)


class MkMiniPhase21V81RuntimeSafeRevalidateEnv(
    MkMiniPhase21V8RuntimeRevalidateEnv
):
    """
    Phase21 v8.1：

    1. 障碍簇用于生成连续路径；
    2. 全部前向传感器点用于候选验证；
    3. 候选通过运行时复核后才提交；
    4. 不调用局部A*；
    5. 不使用未知障碍真值。
    """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )

        # 保留变量名，确保继承的v7/v8环境调用新规划器。
        self._phase21_v7_planner = (
            Phase21V8AdaptiveRuntimeSafePlanner(
                phase21_v4_config_from_env(
                    self
                )
            )
        )

        self.phase21_v81_candidate_reject_count = 0
        self.phase21_v81_last_candidate_margin = float(
            "inf"
        )

    def _phase21_v81_candidate_margin(
        self,
        candidate_path: np.ndarray,
        request: Any,
    ) -> float:
        path = np.asarray(
            candidate_path,
            dtype=np.float64,
        ).reshape(-1, 2)

        sensor_world = np.asarray(
            request.sensor_points_world,
            dtype=np.float64,
        ).reshape(-1, 2)

        sensor_local = np.asarray(
            request.sensor_points_local,
            dtype=np.float64,
        ).reshape(-1, 2)

        point_count = min(
            len(sensor_world),
            len(sensor_local),
        )

        if point_count == 0:
            return float("inf")

        sensor_world = sensor_world[
            :point_count
        ]

        sensor_local = sensor_local[
            :point_count
        ]

        valid_mask = (
            (sensor_local[:, 0] > 0.05)
            & (
                sensor_local[:, 0]
                <= float(
                    request.path_lookahead
                )
                + 0.50
            )
        )

        if not np.any(valid_mask):
            return float("inf")

        robot_xy = np.asarray(
            request.robot_pose[:2],
            dtype=np.float64,
        )

        nearest_index = int(
            np.argmin(
                np.linalg.norm(
                    path - robot_xy,
                    axis=1,
                )
            )
        )

        future_path = path[
            nearest_index:
        ]

        if len(future_path) < 2:
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

        route = str(
            result.diagnostics.get(
                "phase21_v7_route",
                "unknown",
            )
        )

        self.phase21_v8_last_replan_route = route
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
                "[Phase21-v8.1 planner failure]",
                f"step={self.phase21_v8_step}",
                f"before={margin_before:.4f}",
                f"reason={self.phase21_v8_last_replan_reason}",
            )

            return False

        # 两阶段安全提交：
        # 规划结果不能立即写入环境。
        candidate_margin = (
            self._phase21_v81_candidate_margin(
                result.active_path,
                request,
            )
        )

        self.phase21_v81_last_candidate_margin = float(
            candidate_margin
        )

        self.phase21_v8_last_margin_after_replan = float(
            candidate_margin
        )

        if (
            not np.isfinite(candidate_margin)
            or candidate_margin
            < self.REVALIDATE_THRESHOLD
        ):
            self.phase21_v81_candidate_reject_count += 1
            self.phase21_v8_replan_failure_count += 1

            self.phase21_v8_last_replan_reason = (
                "candidate_runtime_margin_"
                "below_threshold"
            )

            print(
                "[Phase21-v8.1 candidate rejected]",
                f"step={self.phase21_v8_step}",
                f"before={margin_before:.4f}",
                f"candidate={candidate_margin:.4f}",
                f"threshold={self.REVALIDATE_THRESHOLD:.4f}",
                f"route={route}",
                f"family={result.candidate_family}",
            )

            return False

        # 只有运行时复核通过后才替换活动路径。
        self._phase21_write_planner_result(
            result
        )

        self.phase21_v8_replan_success_count += 1
        self.phase21_v8_last_replan_step = (
            self.phase21_v8_step
        )

        self.phase21_v8_last_replan_reason = "none"

        self.phase21_v7_takeover_count += 1
        self.phase21_v7_last_route = route
        self.phase21_v7_last_family = str(
            result.candidate_family
        )

        if route == "primary_success":
            self.phase21_v7_primary_count += 1

        elif route == "fallback_success":
            self.phase21_v7_hermite_count += 1

        elif route == "cluster_bspline_success":
            self.phase21_v7_bspline_count += 1

        print(
            "[Phase21-v8.1 runtime-safe replan]",
            f"step={self.phase21_v8_step}",
            f"before={margin_before:.4f}",
            f"candidate={candidate_margin:.4f}",
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
        result = super().step(
            action
        )

        if (
            isinstance(result, tuple)
            and len(result) >= 4
            and isinstance(result[-1], dict)
        ):
            result[-1].update({
                "phase21_v81_candidate_reject_count":
                    int(
                        self.phase21_v81_candidate_reject_count
                    ),
                "phase21_v81_last_candidate_margin":
                    float(
                        self.phase21_v81_last_candidate_margin
                    ),
                "phase21_v81_uses_local_astar":
                    False,
            })

        return result


MkMiniPhase21RiskSwitchFusionSACEnv = (
    MkMiniPhase21V81RuntimeSafeRevalidateEnv
)


__all__ = [
    "MkMiniPhase21V81RuntimeSafeRevalidateEnv",
    "MkMiniPhase21RiskSwitchFusionSACEnv",
]
