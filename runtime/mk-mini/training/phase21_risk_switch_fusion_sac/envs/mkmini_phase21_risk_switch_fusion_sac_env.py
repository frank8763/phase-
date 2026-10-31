"""
Phase21仿真环境入口。

正式局部规划器：
Phase21 v4 safe detour

训练策略：
Phase20 SAC 325000步
"""

from navigation.phase21.local_planners.phase21_v4_safe_detour import (
    MkMiniPhase21RiskSwitchFusionSACEnv,
)

__all__ = [
    "MkMiniPhase21RiskSwitchFusionSACEnv",
]
