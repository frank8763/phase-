from __future__ import annotations

from typing import Any

from envs.phase21.mkmini_phase21_v4_fallback_takeover_env import (
    MkMiniPhase21V4FallbackTakeoverEnv,
)
from envs.phase21.mkmini_phase21_v4_shadow_compare_env import (
    build_planner_request_from_env,
    phase21_v4_config_from_env,
)
from navigation.phase21.local_planners.phase21_v4_safe_detour import (
    MkMiniPhase21RiskSwitchFusionSACEnv as FormalPhase21V4Env,
)
from navigation.phase21.local_planners.phase21_v7_adaptive_planner import (
    Phase21V7AdaptivePlanner,
)


class MkMiniPhase21V7AdaptiveTakeoverEnv(
    MkMiniPhase21V4FallbackTakeoverEnv
):
    """
    Phase21 v7候选接管环境。

    路由：
    1. 原v4；
    2. 单段Hermite-C2；
    3. 障碍簇驱动多控制点B样条。

    不调用局部A*。
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

        self._phase21_v7_planner = (
            Phase21V7AdaptivePlanner(
                phase21_v4_config_from_env(
                    self
                )
            )
        )

        self.phase21_v7_takeover_count = 0
        self.phase21_v7_primary_count = 0
        self.phase21_v7_hermite_count = 0
        self.phase21_v7_bspline_count = 0
        self.phase21_v7_failure_count = 0
        self.phase21_v7_exception_count = 0

        self.phase21_v7_last_route = "none"
        self.phase21_v7_last_family = "none"
        self.phase21_v7_last_exception = "none"

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
                self._phase21_v7_planner
                .plan(request)
            )

        except Exception as exc:
            self.phase21_v7_exception_count += 1

            self.phase21_v7_last_exception = (
                f"{type(exc).__name__}: {exc}"
            )

            # v7异常时退回正式v4，避免破坏控制。
            return bool(
                FormalPhase21V4Env
                ._phase21_v3_build_detour(
                    self
                )
            )

        route = str(
            result.diagnostics.get(
                "phase21_v7_route",
                "unknown",
            )
        )

        self.phase21_v7_last_route = route
        self.phase21_v7_last_family = str(
            result.candidate_family
        )
        self.phase21_v7_last_exception = "none"

        if not result.success:
            self.phase21_v7_failure_count += 1

            # 所有v7候选失败时退回正式v4。
            return bool(
                FormalPhase21V4Env
                ._phase21_v3_build_detour(
                    self
                )
            )

        self._phase21_write_planner_result(
            result
        )

        self.phase21_v7_takeover_count += 1

        if route == "primary_success":
            self.phase21_v7_primary_count += 1

        elif route == "fallback_success":
            self.phase21_v7_hermite_count += 1

        elif route == "cluster_bspline_success":
            self.phase21_v7_bspline_count += 1

            print(
                "[Phase21-v7 cluster-bspline]",
                f"side={result.chosen_side}",
                f"known={result.known_margin:.4f}",
                f"sensor={result.sensor_margin:.4f}",
                f"p95={result.p95_curvature:.4f}",
                f"feasible={result.diagnostics.get('cluster_bspline_feasible_count')}",
            )

        return True

    def _phase21_v3_fill_info(
        self,
        info: dict[str, Any],
    ) -> dict[str, Any]:
        info = super()._phase21_v3_fill_info(
            info
        )

        info.update({
            "phase21_v7_takeover_count":
                int(
                    self.phase21_v7_takeover_count
                ),
            "phase21_v7_primary_count":
                int(
                    self.phase21_v7_primary_count
                ),
            "phase21_v7_hermite_count":
                int(
                    self.phase21_v7_hermite_count
                ),
            "phase21_v7_bspline_count":
                int(
                    self.phase21_v7_bspline_count
                ),
            "phase21_v7_failure_count":
                int(
                    self.phase21_v7_failure_count
                ),
            "phase21_v7_exception_count":
                int(
                    self.phase21_v7_exception_count
                ),
            "phase21_v7_last_route":
                str(
                    self.phase21_v7_last_route
                ),
            "phase21_v7_last_family":
                str(
                    self.phase21_v7_last_family
                ),
            "phase21_v7_last_exception":
                str(
                    self.phase21_v7_last_exception
                ),
            "phase21_v7_uses_local_astar":
                False,
        })

        return info


MkMiniPhase21RiskSwitchFusionSACEnv = (
    MkMiniPhase21V7AdaptiveTakeoverEnv
)


__all__ = [
    "MkMiniPhase21V7AdaptiveTakeoverEnv",
    "MkMiniPhase21RiskSwitchFusionSACEnv",
]
