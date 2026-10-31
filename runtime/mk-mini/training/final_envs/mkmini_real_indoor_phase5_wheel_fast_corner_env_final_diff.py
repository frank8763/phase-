import numpy as np

from training.envs.mkmini_real_indoor_phase5_wheel_corner_residual_safe_env import (
    MkMiniRealIndoorPhase5WheelCornerResidualSafeEnv,
)


class MkMiniRealIndoorPhase5WheelFastCornerEnv(
    MkMiniRealIndoorPhase5WheelCornerResidualSafeEnv
):
    """
    Phase5 v2:
    高速直线 + 圆角路径 + 强差速转向 + 防止前进后退抖动
    """

    def __init__(self):
        super().__init__()

        # 速度提高：原来 max_wheel_speed=8，这里提高到 12
        # base_wheel_norm 提高后，直线速度约为原来的 2 倍
        self.max_wheel_speed = 24.0
        self.base_wheel_norm = 0.95
        self.min_forward_norm = 0.28

        # 转向能力增强
        self.max_steer = 0.45
        self.diff_gain = 8.0

        # 圆角路径更明显，避免硬拐 90 度
        self.lookahead = 0.90
        self.path_step = 0.03
        self.corner_cut_dist = 1.05
        self.corner_points = 42

        # residual 不要太大，防止破坏基础跟踪
        self.steer_residual_scale = 0.12
        self.speed_residual_scale = 0.08

        # recovery 不要频繁触发
        self.front_danger_dist = 0.40
        self.side_danger_dist = 0.24
        self.safe_front_dist = 0.65
        self.safe_side_dist = 0.45
        self.rear_stop_dist = 0.22

        # 偏离路径恢复放宽，避免来回倒车
        self.path_error_trigger = 0.90
        self.path_stuck_trigger_steps = 70

        self.recovery_cooldown = 0

        # 连续拐弯防抖：限制左右转向快速切换
        self.preview_steer_smooth = 0.35
        self.preview_steer_max_delta = 0.08
        self.prev_preview_steer_norm = 0.0

        # 平滑控制，减少前轮跳变
        self.max_steer_delta = 0.010
        self.max_wheel_delta = 0.25
        self.backup_steps = 55
        self.turn_steps = 75
        self.rejoin_steps = 0

    def _is_danger_close(self, c):
        # recovery 冷却期内不再反复触发，防止前进/后退抖动
        if self.recovery_cooldown > 0:
            self.recovery_cooldown -= 1
            return False

        front_blocked = (
            c["front"] < self.front_danger_dist
            or c["front_left"] < self.front_danger_dist
            or c["front_right"] < self.front_danger_dist
        )

        emergency = c["min"] < 0.22

        # 侧边近但前方安全，不倒车
        return front_blocked or emergency

    def _recovery_action(self, c):
        # 1. 先直线后退，不边退边乱转
        if self.recovery_stage == "BACKUP":
            self.recovery_timer -= 1

            steer_norm = 0.0
            wheel_norm = -0.55

            if c["rear"] < self.rear_stop_dist:
                self.recovery_stage = "TURN_AWAY"
                self.recovery_timer = self.turn_steps

            if self.recovery_timer <= 0:
                self.recovery_stage = "TURN_AWAY"
                self.recovery_timer = self.turn_steps

            return np.array([steer_norm, wheel_norm], dtype=np.float32)

        # 2. 后退完成后，只向空旷方向低速前进转向
        if self.recovery_stage == "TURN_AWAY":
            self.recovery_timer -= 1

            steer_norm = 0.95 * self.recovery_turn_dir
            wheel_norm = 0.30

            if self.recovery_timer <= 0:
                self.recovery_stage = "NORMAL"
                self.recovery_timer = 0
                self.recovery_cooldown = 90

            return np.array([steer_norm, wheel_norm], dtype=np.float32)

        self.recovery_stage = "NORMAL"
        self.recovery_timer = 0
        return None

    def _base_pursuit_action(self):
        steer_norm, wheel_norm, steer, target, alpha = super()._base_pursuit_action()

        # 直线速度快，转弯自动降速
        if abs(alpha) > 1.00:
            wheel_norm *= 0.25
        elif abs(alpha) > 0.75:
            wheel_norm *= 0.58
        elif abs(alpha) > 0.50:
            wheel_norm *= 0.50
        elif abs(alpha) > 0.30:
            wheel_norm *= 0.70

        # 小角度直线回正，减少轮子偏角
        if abs(alpha) < 0.08 and self._nearest_path_error() < 0.25:
            steer_norm = 0.0
            steer = 0.0

        wheel_norm = float(np.clip(wheel_norm, self.min_forward_norm, 0.95))

        return steer_norm, wheel_norm, steer, target, alpha
