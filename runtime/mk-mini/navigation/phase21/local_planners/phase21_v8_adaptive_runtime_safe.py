from __future__ import annotations

from navigation.phase21.interfaces import (
    PlannerRequest,
    PlannerResult,
)
from navigation.phase21.local_planners.phase21_v4_config import (
    Phase21V4Config,
)
from navigation.phase21.local_planners.phase21_v4_fallback_planner import (
    Phase21V4FallbackPlanner,
)
from navigation.phase21.local_planners.phase21_v8_cluster_bspline_runtime_safe import (
    Phase21V8ClusterBSplineRuntimeSafe,
)


class Phase21V8AdaptiveRuntimeSafePlanner:
    """
    Phase21 v8.1全传感器约束非栅格局部规划器。

    1. 原v4快速规划；
    2. 单段Hermite-C2；
    3. 障碍簇驱动多控制点B样条。

    不调用局部A*。
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

        self.v4_and_hermite = (
            Phase21V4FallbackPlanner(
                self.config
            )
        )

        self.cluster_bspline = (
            Phase21V8ClusterBSplineRuntimeSafe(
                self.config
            )
        )

    def plan(
        self,
        request: PlannerRequest,
    ) -> PlannerResult:
        prior_result = (
            self.v4_and_hermite.plan(
                request
            )
        )

        if prior_result.success:
            diagnostics = dict(
                prior_result.diagnostics
            )

            diagnostics.update({
                "phase21_v7_route":
                    diagnostics.get(
                        "planner_route",
                        "prior_success",
                    ),
                "cluster_bspline_used":
                    False,
                "uses_local_astar":
                    False,
            })

            prior_result.diagnostics = (
                diagnostics
            )

            return prior_result

        if (
            prior_result.failure_reason
            != "fallback_no_feasible_candidate"
        ):
            diagnostics = dict(
                prior_result.diagnostics
            )

            diagnostics.update({
                "phase21_v7_route":
                    "prior_failure_not_eligible",
                "cluster_bspline_used":
                    False,
                "uses_local_astar":
                    False,
            })

            prior_result.diagnostics = (
                diagnostics
            )

            return prior_result

        bspline_result = (
            self.cluster_bspline.plan(
                request,
                prior_result=prior_result,
            )
        )

        diagnostics = dict(
            bspline_result.diagnostics
        )

        diagnostics.update({
            "phase21_v7_route":
                (
                    "cluster_bspline_success"
                    if bspline_result.success
                    else "cluster_bspline_failure"
                ),
            "cluster_bspline_used":
                True,
            "uses_local_astar":
                False,
            "prior_failure_reason":
                prior_result.failure_reason,
            "prior_candidate_count":
                prior_result.candidate_count,
            "prior_feasible_count":
                prior_result.feasible_count,
            "cluster_bspline_candidate_count":
                bspline_result.candidate_count,
            "cluster_bspline_feasible_count":
                bspline_result.feasible_count,
        })

        bspline_result.diagnostics = (
            diagnostics
        )

        bspline_result.candidate_count = (
            int(
                prior_result.candidate_count
            )
            + int(
                bspline_result.candidate_count
            )
        )

        bspline_result.feasible_count = (
            int(
                prior_result.feasible_count
            )
            + int(
                bspline_result.feasible_count
            )
        )

        return bspline_result


__all__ = [
    "Phase21V8AdaptiveRuntimeSafePlanner",
]
