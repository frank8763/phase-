import math
import numpy as np
import mujoco

from training.phase9_static_no_dynamic.envs.mkmini_phase9h2_2_confirmed_env import (
    MkMiniPhase9H22YawRateClosedLoopEnv as H22BaseEnv,
)


class MkMiniPhase9H3KinematicYawSyncEnv(H22BaseEnv):
    """
    Phase9-H3.1: yaw sync + velocity direction sync.

    解决：
    1. 前轮转了，车身 yaw 跟得不够
    2. 车头转了，但车身速度方向还往前滑
    3. 不继承 G4/G5
    4. 只在 Phase9 内生效
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.h3_kinematic_gain = 0.66
        self.h3_min_steer = 0.08
        self.h3_min_wheel = 0.15
        self.h3_max_extra_dyaw = 0.020

        # 新增：速度方向同步，解决“车头转了但车身还往旧方向滑”
        self.h3_velocity_align_gain = 0.24
        self.h3_velocity_align_max = 0.30

        print(
            "[Phase9-H3.1-plus yaw+velocity sync] enabled: "
            "yaw compensation + planar velocity alignment"
        )

    def _yaw_from_qpos(self):
        q = self.data.qpos[3:7]
        return math.atan2(
            2.0 * (q[0] * q[3] + q[1] * q[2]),
            1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3]),
        )

    def _set_yaw_keep_pos(self, yaw):
        self.data.qpos[3] = math.cos(yaw * 0.5)
        self.data.qpos[4] = 0.0
        self.data.qpos[5] = 0.0
        self.data.qpos[6] = math.sin(yaw * 0.5)

    def _expected_yaw_rate_h3(self, steer, wheel):
        wheel_radius = float(getattr(self, "wheel_radius", 0.075))
        wheel_base = float(getattr(self, "wheel_base", 0.42))

        v = wheel * wheel_radius
        return v / max(wheel_base, 1e-4) * math.tan(steer)

    def _get_h2_filtered_cmd(self):
        steer = 0.5 * (
            float(getattr(self, "_h2_lf", 0.0)) +
            float(getattr(self, "_h2_rf", 0.0))
        )
        wheel = 0.5 * (
            float(getattr(self, "_h2_lr", 0.0)) +
            float(getattr(self, "_h2_rr", 0.0))
        )
        return steer, wheel

    def _h3_kinematic_yaw_sync(self):
        steer, wheel = self._get_h2_filtered_cmd()

        if abs(steer) < self.h3_min_steer or abs(wheel) < self.h3_min_wheel:
            return

        expected_yaw_rate = self._expected_yaw_rate_h3(steer, wheel)

        actual_yaw_rate = 0.0
        if self.data.qvel.shape[0] > 5:
            actual_yaw_rate = float(self.data.qvel[5])

        missing_yaw_rate = expected_yaw_rate - actual_yaw_rate

        dt = float(getattr(self, "dt", self.model.opt.timestep))

        extra_dyaw = self.h3_kinematic_gain * missing_yaw_rate * dt
        extra_dyaw = float(
            np.clip(
                extra_dyaw,
                -self.h3_max_extra_dyaw,
                self.h3_max_extra_dyaw,
            )
        )

        if abs(extra_dyaw) < 1e-6:
            return

        yaw = self._yaw_from_qpos()
        yaw_new = yaw + extra_dyaw

        self._set_yaw_keep_pos(yaw_new)

        if self.data.qvel.shape[0] > 5:
            self.data.qvel[5] += extra_dyaw / max(dt, 1e-4)

        mujoco.mj_forward(self.model, self.data)

    def _h3_velocity_direction_sync(self):
        steer, wheel = self._get_h2_filtered_cmd()

        if abs(steer) < self.h3_min_steer or abs(wheel) < self.h3_min_wheel:
            return

        if self.data.qvel.shape[0] < 2:
            return

        vx = float(self.data.qvel[0])
        vy = float(self.data.qvel[1])
        speed = math.hypot(vx, vy)

        if speed < 1e-4:
            return

        yaw = self._yaw_from_qpos()

        # 根据后轮方向判断前进/后退
        sign = 1.0 if wheel >= 0.0 else -1.0

        desired_vx = sign * speed * math.cos(yaw)
        desired_vy = sign * speed * math.sin(yaw)

        steer_abs = abs(steer)
        align = float(
            np.interp(
                steer_abs,
                [self.h3_min_steer, 0.52],
                [0.04, self.h3_velocity_align_gain],
            )
        )
        align = float(np.clip(align, 0.0, self.h3_velocity_align_max))

        self.data.qvel[0] = (1.0 - align) * vx + align * desired_vx
        self.data.qvel[1] = (1.0 - align) * vy + align * desired_vy

        mujoco.mj_forward(self.model, self.data)

    def step(self, action):
        out = super().step(action)

        # 先补 yaw，再同步速度方向
        self._h3_kinematic_yaw_sync()
        self._h3_velocity_direction_sync()

        return out
