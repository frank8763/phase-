from __future__ import annotations

from typing import Any

from envs.phase21.mkmini_phase21_v8_1_runtime_safe_revalidate_env import (
    MkMiniPhase21V81RuntimeSafeRevalidateEnv,
)


RECOVERY_PRESETS = {
    "conservative": {
        "offsets": (
            0.30,
            0.34,
            0.44,
            0.54,
            0.64,
            0.76,
        ),
        "approach_distances": (
            0.35,
            0.45,
            0.70,
            0.95,
            1.20,
        ),
        "rejoin_distances": (
            1.00,
            1.20,
            1.60,
            2.00,
            2.40,
            2.90,
        ),
    },
    "balanced": {
        "offsets": (
            0.26,
            0.34,
            0.42,
            0.52,
            0.64,
            0.78,
            0.94,
        ),
        "approach_distances": (
            0.30,
            0.45,
            0.65,
            0.90,
            1.20,
            1.50,
        ),
        "rejoin_distances": (
            0.90,
            1.20,
            1.50,
            1.90,
            2.40,
            3.00,
            3.60,
        ),
    },
    "wide": {
        "offsets": (
            0.22,
            0.30,
            0.38,
            0.48,
            0.60,
            0.74,
            0.90,
            1.08,
        ),
        "approach_distances": (
            0.25,
            0.40,
            0.60,
            0.85,
            1.15,
            1.50,
            1.90,
        ),
        "rejoin_distances": (
            0.80,
            1.05,
            1.35,
            1.70,
            2.15,
            2.70,
            3.40,
            4.20,
        ),
    },
}


class MkMiniPhase21V11CandidateRecoveryEnv(
    MkMiniPhase21V81RuntimeSafeRevalidateEnv
):
    """
    Phase21 v11：两级候选路径搜索。

    第一级：
        完整保留v8.1默认候选集合。

    第二级：
        仅在第一级返回no_feasible_candidate时，
        使用更大的offset/approach/rejoin候选集合重新搜索。

    不修改：
        SAC策略；
        底层控制器；
        已知地图；
        传感器输入；
        安全阈值；
        路径曲率与航向约束。
    """

    def __init__(
        self,
        *,
        phase21_v11_recovery_offsets=(
            0.26,
            0.34,
            0.42,
            0.52,
            0.64,
            0.78,
            0.94,
        ),
        phase21_v11_recovery_approach_distances=(
            0.30,
            0.45,
            0.65,
            0.90,
            1.20,
            1.50,
        ),
        phase21_v11_recovery_rejoin_distances=(
            0.90,
            1.20,
            1.50,
            1.90,
            2.40,
            3.00,
            3.60,
        ),
        phase21_v11_preset_name: str = "balanced",
        **kwargs: Any,
    ) -> None:
        self.phase21_v11_preset_name = str(
            phase21_v11_preset_name
        )

        self.phase21_v11_recovery_offsets = tuple(
            float(value)
            for value in phase21_v11_recovery_offsets
        )

        self.phase21_v11_recovery_approach_distances = tuple(
            float(value)
            for value
            in phase21_v11_recovery_approach_distances
        )

        self.phase21_v11_recovery_rejoin_distances = tuple(
            float(value)
            for value
            in phase21_v11_recovery_rejoin_distances
        )

        self._phase21_v11_clear_telemetry()

        super().__init__(**kwargs)

    def _phase21_v11_clear_telemetry(
        self,
    ) -> None:
        self.phase21_v11_recovery_attempted = False
        self.phase21_v11_recovery_success = False
        self.phase21_v11_recovery_attempt_count = 0
        self.phase21_v11_recovery_success_count = 0

        self.phase21_v11_base_candidate_count = 0
        self.phase21_v11_base_feasible_count = 0

        self.phase21_v11_recovery_candidate_count = 0
        self.phase21_v11_recovery_feasible_count = 0

    def reset(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self._phase21_v11_clear_telemetry()

        return super().reset(
            *args,
            **kwargs,
        )

    def _phase21_v3_build_detour(
        self,
    ) -> bool:
        failure_count_before = int(
            getattr(
                self,
                "phase21_v4_failed_attempt_count",
                0,
            )
        )

        # 第一级：原始v8.1路径生成。
        first_result = bool(
            super()._phase21_v3_build_detour()
        )

        self.phase21_v11_base_candidate_count = int(
            getattr(
                self,
                "phase21_v4_candidate_count",
                0,
            )
        )

        self.phase21_v11_base_feasible_count = int(
            getattr(
                self,
                "phase21_v4_feasible_count",
                0,
            )
        )

        if first_result:
            return True

        reason = str(
            getattr(
                self,
                "phase21_v3_failure_reason",
                "none",
            )
        )

        # 只处理候选集合不足，不掩盖其他错误。
        if reason != "no_feasible_candidate":
            return False

        self.phase21_v11_recovery_attempted = True
        self.phase21_v11_recovery_attempt_count += 1

        original_offsets = tuple(
            self.phase21_v4_offsets
        )

        original_approach = tuple(
            self.phase21_v4_approach_distances
        )

        original_rejoin = tuple(
            self.phase21_v4_rejoin_distances
        )

        self.phase21_v4_offsets = (
            self.phase21_v11_recovery_offsets
        )

        self.phase21_v4_approach_distances = (
            self
            .phase21_v11_recovery_approach_distances
        )

        self.phase21_v4_rejoin_distances = (
            self
            .phase21_v11_recovery_rejoin_distances
        )

        second_result = False

        try:
            second_result = bool(
                super()._phase21_v3_build_detour()
            )

            self.phase21_v11_recovery_candidate_count = int(
                getattr(
                    self,
                    "phase21_v4_candidate_count",
                    0,
                )
            )

            self.phase21_v11_recovery_feasible_count = int(
                getattr(
                    self,
                    "phase21_v4_feasible_count",
                    0,
                )
            )

            if second_result:
                self.phase21_v11_recovery_success = True
                self.phase21_v11_recovery_success_count += 1

                # 恢复成功不计为一次持续失败。
                if hasattr(
                    self,
                    "phase21_v4_failed_attempt_count",
                ):
                    self.phase21_v4_failed_attempt_count = (
                        failure_count_before
                    )

            else:
                # 两级搜索都失败，只记录一次失败。
                if hasattr(
                    self,
                    "phase21_v4_failed_attempt_count",
                ):
                    self.phase21_v4_failed_attempt_count = (
                        failure_count_before + 1
                    )

            return second_result

        finally:
            self.phase21_v4_offsets = (
                original_offsets
            )

            self.phase21_v4_approach_distances = (
                original_approach
            )

            self.phase21_v4_rejoin_distances = (
                original_rejoin
            )

    def _phase21_v3_fill_info(
        self,
        info,
    ):
        info = super()._phase21_v3_fill_info(
            info
        )

        info.update({
            "phase21_v11_preset_name":
                self.phase21_v11_preset_name,
            "phase21_v11_recovery_attempted":
                bool(
                    self
                    .phase21_v11_recovery_attempted
                ),
            "phase21_v11_recovery_success":
                bool(
                    self
                    .phase21_v11_recovery_success
                ),
            "phase21_v11_recovery_attempt_count":
                int(
                    self
                    .phase21_v11_recovery_attempt_count
                ),
            "phase21_v11_recovery_success_count":
                int(
                    self
                    .phase21_v11_recovery_success_count
                ),
            "phase21_v11_base_candidate_count":
                int(
                    self
                    .phase21_v11_base_candidate_count
                ),
            "phase21_v11_base_feasible_count":
                int(
                    self
                    .phase21_v11_base_feasible_count
                ),
            "phase21_v11_recovery_candidate_count":
                int(
                    self
                    .phase21_v11_recovery_candidate_count
                ),
            "phase21_v11_recovery_feasible_count":
                int(
                    self
                    .phase21_v11_recovery_feasible_count
                ),
        })

        return info


__all__ = [
    "MkMiniPhase21V11CandidateRecoveryEnv",
    "RECOVERY_PRESETS",
]
