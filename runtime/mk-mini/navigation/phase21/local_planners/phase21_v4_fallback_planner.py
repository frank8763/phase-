from __future__ import annotations

from navigation.phase21.interfaces import (
    PlannerRequest,
    PlannerResult,
)
from navigation.phase21.local_planners.phase21_v4_config import (
    Phase21V4Config,
)
from navigation.phase21.local_planners.phase21_v4_hermite_fallback import (
    Phase21V4HermiteFallback,
)
from navigation.phase21.local_planners.phase21_v4_planner import (
    Phase21V4Planner,
)


class Phase21V4FallbackPlanner:
    """
    原v4优先，Hermite-C2仅作为失败回退。

    primary成功时绝不运行fallback。
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

        self.primary = Phase21V4Planner(
            self.config
        )

        self.fallback = (
            Phase21V4HermiteFallback(
                self.config
            )
        )

    def plan(
        self,
        request: PlannerRequest,
    ) -> PlannerResult:
        primary_result = self.primary.plan(
            request
        )

        if primary_result.success:
            diagnostics = dict(
                primary_result.diagnostics
            )

            diagnostics.update({
                "fallback_used": False,
                "planner_route":
                    "primary_success",
            })

            primary_result.diagnostics = (
                diagnostics
            )

            return primary_result

        if (
            primary_result.failure_reason
            != "no_feasible_candidate"
        ):
            diagnostics = dict(
                primary_result.diagnostics
            )

            diagnostics.update({
                "fallback_used": False,
                "planner_route":
                    "primary_failure_not_eligible",
            })

            primary_result.diagnostics = (
                diagnostics
            )

            return primary_result

        fallback_result = (
            self.fallback.plan(
                request,
                primary_result=primary_result,
            )
        )

        diagnostics = dict(
            fallback_result.diagnostics
        )

        diagnostics.update({
            "planner_route":
                (
                    "fallback_success"
                    if fallback_result.success
                    else "fallback_failure"
                ),
            "primary_candidate_count":
                primary_result.candidate_count,
            "fallback_candidate_count":
                fallback_result.candidate_count,
            "primary_feasible_count":
                primary_result.feasible_count,
            "fallback_feasible_count":
                fallback_result.feasible_count,
        })

        fallback_result.diagnostics = (
            diagnostics
        )

        fallback_result.candidate_count = (
            primary_result.candidate_count
            + fallback_result.candidate_count
        )

        return fallback_result


__all__ = [
    "Phase21V4FallbackPlanner",
]
