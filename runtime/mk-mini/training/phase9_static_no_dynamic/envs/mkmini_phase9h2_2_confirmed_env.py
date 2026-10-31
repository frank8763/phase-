import math
import numpy as np

from training.phase9_static_no_dynamic.envs.mkmini_phase9h2_1_confirmed_env import (
    MkMiniPhase9H2SteerFirstNoDiffEnv as H21BaseEnv,
)


class MkMiniPhase9H22YawRateClosedLoopEnv(H21BaseEnv):
    """
    Phase9-H2.2

    基于 H2.1 confirmed：
    1. 不继承 G4/G5
    2. 不污染前面目录
    3. 不改 qpos/yaw
    4. 只增加 yaw-rate 闭环限速
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.h22_yaw_ratio_min = 0.62
        self.h22_min_speed_scale = 0.30
        self.h22_yaw_check_steer = 0.16
        self.h22_yaw_check_wheel = 0.25

        print(
            "[Phase9-H2.2 yaw-rate closed-loop] enabled: "
            "based on H2.1 confirmed, yaw-lag adaptive speed limit"
        )

    def _expected_yaw_rate(self, steer, wheel_speed):
        wheel_radius = float(getattr(self, "wheel_radius", 0.075))
        wheel_base = float(getattr(self, "wheel_base", 0.42))

        v = wheel_speed * wheel_radius
        return v / max(wheel_base, 1e-4) * math.tan(steer)

    def _apply_wheel_ctrl(self, lf, rf, lr, rr):
        steer = 0.5 * (float(lf) + float(rf))
        wheel = 0.5 * (float(lr) + float(rr))

        steer_abs = abs(steer)

        if steer_abs > self.h22_yaw_check_steer and abs(wheel) > self.h22_yaw_check_wheel:
            expected_yaw = self._expected_yaw_rate(steer, wheel)

            actual_yaw = 0.0
            if self.data.qvel.shape[0] > 5:
                actual_yaw = float(self.data.qvel[5])

            if abs(expected_yaw) > 1e-4:
                same_dir = actual_yaw * expected_yaw > 0.0
                ratio = abs(actual_yaw) / abs(expected_yaw)

                if (not same_dir) or ratio < self.h22_yaw_ratio_min:
                    ratio = float(np.clip(ratio, 0.0, self.h22_yaw_ratio_min))
                    scale = float(
                        np.interp(
                            ratio,
                            [0.0, self.h22_yaw_ratio_min],
                            [self.h22_min_speed_scale, 1.0],
                        )
                    )

                    wheel = wheel * scale
                    lr = wheel
                    rr = wheel

        return super()._apply_wheel_ctrl(lf, rf, lr, rr)
