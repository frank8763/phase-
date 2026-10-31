from __future__ import annotations

from typing import Any

import numpy as np

from envs.phase21.mkmini_phase21_v4_shadow_compare_env import (
    build_planner_request_from_env,
    phase21_v4_config_from_env,
)
from navigation.phase21.local_planners.phase21_v4_fallback_planner import (
    Phase21V4FallbackPlanner,
)
from navigation.phase21.local_planners.phase21_v4_safe_detour import (
    MkMiniPhase21RiskSwitchFusionSACEnv as FormalPhase21V4Env,
)


class MkMiniPhase21V4FallbackTakeoverEnv(
    FormalPhase21V4Env
):
    """
    候选测试环境。

    原v4纯规划器优先；
    只有no_feasible_candidate时才使用Hermite-C2。
    不修改正式v4文件。
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

        self._phase21_fallback_planner = (
            Phase21V4FallbackPlanner(
                phase21_v4_config_from_env(
                    self
                )
            )
        )

        self.phase21_fallback_takeover_count = 0
        self.phase21_fallback_primary_count = 0
        self.phase21_fallback_success_count = 0
        self.phase21_fallback_failure_count = 0
        self.phase21_fallback_last_route = "none"
        self.phase21_fallback_last_family = "none"

    def _phase21_write_planner_result(
        self,
        result,
    ) -> None:
        active_path = np.asarray(
            result.active_path,
            dtype=np.float32,
        ).reshape(-1, 2)

        self._phase21_v3_apply_path(
            active_path
        )

        self.phase21_v3_active_path = (
            active_path.copy()
        )

        self.phase21_v3_detour_applied = True
        self.phase21_v3_chosen_side = str(
            result.chosen_side
        )

        self.phase21_v3_failure_reason = "none"
        self.phase21_v3_last_attempt_reason = "none"
        self.phase21_v3_persistent_failure_reason = (
            "none"
        )

        self.phase21_v4_candidate_count = int(
            result.candidate_count
        )

        self.phase21_v4_feasible_count = int(
            result.feasible_count
        )

        self.phase21_v4_selected_score = float(
            result.score
        )

        self.phase21_v4_selected_known_margin = (
            float(result.known_margin)
        )

        self.phase21_v4_selected_sensor_margin = (
            float(result.sensor_margin)
        )

        self.phase21_v4_selected_p95_curvature = (
            float(result.p95_curvature)
        )

        self.phase21_v4_selected_max_heading_delta = (
            float(result.max_heading_delta)
        )

        if result.approach_point is not None:
            self.phase21_v3_approach_point = (
                np.asarray(
                    result.approach_point,
                    dtype=np.float32,
                ).copy()
            )

        if result.detour_point is not None:
            self.phase21_v3_detour_point = (
                np.asarray(
                    result.detour_point,
                    dtype=np.float32,
                ).copy()
            )

        if result.rejoin_point is not None:
            self.phase21_v3_rejoin_point = (
                np.asarray(
                    result.rejoin_point,
                    dtype=np.float32,
                ).copy()
            )

        conflict_center = (
            result.diagnostics.get(
                "conflict_center"
            )
        )

        if conflict_center is not None:
            self.phase21_v3_conflict_center = (
                np.asarray(
                    conflict_center,
                    dtype=np.float32,
                ).copy()
            )

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        try:
            request = (
                build_planner_request_from_env(
                    self
                )
            )

            result = (
                self._phase21_fallback_planner
                .plan(request)
            )

        except Exception:
            # 候选实现异常时退回原正式v4。
            return bool(
                super()
                ._phase21_v3_build_detour()
            )

        route = str(
            result.diagnostics.get(
                "planner_route",
                "unknown",
            )
        )

        self.phase21_fallback_last_route = route
        self.phase21_fallback_last_family = str(
            result.candidate_family
        )

        if not result.success:
            self.phase21_fallback_failure_count += 1

            return bool(
                super()
                ._phase21_v3_build_detour()
            )

        self._phase21_write_planner_result(
            result
        )

        self.phase21_fallback_takeover_count += 1

        if route == "primary_success":
            self.phase21_fallback_primary_count += 1

        elif route == "fallback_success":
            self.phase21_fallback_success_count += 1

        return True

    def _phase21_v3_fill_info(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        info = super()._phase21_v3_fill_info(
            info
        )

        info.update({
            "phase21_fallback_takeover_count":
                int(
                    self.phase21_fallback_takeover_count
                ),
            "phase21_fallback_primary_count":
                int(
                    self.phase21_fallback_primary_count
                ),
            "phase21_fallback_success_count":
                int(
                    self.phase21_fallback_success_count
                ),
            "phase21_fallback_failure_count":
                int(
                    self.phase21_fallback_failure_count
                ),
            "phase21_fallback_last_route":
                str(
                    self.phase21_fallback_last_route
                ),
            "phase21_fallback_last_family":
                str(
                    self.phase21_fallback_last_family
                ),
        })

        return info


MkMiniPhase21RiskSwitchFusionSACEnv = (
    MkMiniPhase21V4FallbackTakeoverEnv
)


__all__ = [
    "MkMiniPhase21V4FallbackTakeoverEnv",
    "MkMiniPhase21RiskSwitchFusionSACEnv",
]
