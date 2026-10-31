from __future__ import annotations

from typing import Protocol, runtime_checkable

from navigation.phase21.interfaces import (
    PlannerRequest,
    PlannerResult,
)


@runtime_checkable
class LocalPlanner(Protocol):
    """
    Phase21 独立局部规划器统一接口。

    实现类不得直接依赖 MuJoCo env、model 或 data。
    """

    def plan(
        self,
        request: PlannerRequest,
    ) -> PlannerResult:
        ...


__all__ = ["LocalPlanner"]
