import numpy as np

from training.phase17_fusion_safety_sac_nav.envs.mkmini_phase17_fusion_safety_env import (
    MkMiniPhase17BRandomObstacleEnv,
)


class MkMiniPhase17BSafetyShieldEnv(MkMiniPhase17BRandomObstacleEnv):
    """
    Phase17-B:
    No-global LiDAR/Camera fusion SAC + passive safety shield.

    不改变策略结构。
    只在近距离危险时限制速度，避免撞击。
    """

    def __init__(
        self,
        *args,
        shield_front_stop=0.28,
        shield_front_slow=0.45,
        shield_side_near=0.32,
        shield_min_speed=-0.15,
        shield_slow_speed=0.18,
        shield_turn_gain=0.35,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.shield_front_stop = float(shield_front_stop)
        self.shield_front_slow = float(shield_front_slow)
        self.shield_side_near = float(shield_side_near)
        self.shield_min_speed = float(shield_min_speed)
        self.shield_slow_speed = float(shield_slow_speed)
        self.shield_turn_gain = float(shield_turn_gain)

        self.phase17_shield_active = False
        self.phase17_shield_reason = "none"
        self.phase17_front_min = 10.0
        self.phase17_left_min = 10.0
        self.phase17_right_min = 10.0

    def _phase17_try_get_lidar(self):
        """
        兼容不同阶段的 LiDAR 获取函数。
        如果拿不到 LiDAR，则安全层不介入。
        """
        method_names = [
            "_phase18h_get_lidar",
            "_phase16_get_lidar",
            "_phase15_get_lidar",
            "_phase14_get_lidar",
            "_get_lidar",
            "get_lidar",
        ]

        for name in method_names:
            fn = getattr(self, name, None)
            if callable(fn):
                try:
                    lidar = fn()
                    if lidar is not None:
                        lidar = np.asarray(lidar, dtype=np.float32).reshape(-1)
                        if lidar.size >= 8:
                            return lidar
                except Exception:
                    pass

        attr_names = [
            "lidar",
            "last_lidar",
            "phase14_lidar",
            "phase15_lidar",
            "phase16_lidar",
            "scan",
            "last_scan",
        ]

        for name in attr_names:
            if hasattr(self, name):
                try:
                    lidar = getattr(self, name)
                    if lidar is not None:
                        lidar = np.asarray(lidar, dtype=np.float32).reshape(-1)
                        if lidar.size >= 8:
                            return lidar
                except Exception:
                    pass

        return None

    def _phase17_lidar_sectors(self, lidar):
        """
        默认 LiDAR 中间为正前方。
        若原环境角度定义不同，后续再按实际可视化调整。
        """
        lidar = np.asarray(lidar, dtype=np.float32).reshape(-1)
        lidar = np.nan_to_num(lidar, nan=10.0, posinf=10.0, neginf=0.0)
        lidar = np.clip(lidar, 0.0, 10.0)

        n = lidar.size
        c = n // 2

        fw = max(2, n // 18)
        sw = max(3, n // 12)

        front = lidar[max(0, c - fw):min(n, c + fw + 1)]

        left = lidar[min(n, c + fw):min(n, c + fw + sw)]
        right = lidar[max(0, c - fw - sw):max(0, c - fw)]

        if left.size == 0:
            left = front
        if right.size == 0:
            right = front

        return float(front.min()), float(left.min()), float(right.min())

    def _phase17_apply_safety_shield(self, action):
        action = np.asarray(action, dtype=np.float32).copy().reshape(-1)

        self.phase17_shield_active = False
        self.phase17_shield_reason = "none"

        lidar = self._phase17_try_get_lidar()
        if lidar is None or action.size < 2:
            return action

        front_min, left_min, right_min = self._phase17_lidar_sectors(lidar)

        self.phase17_front_min = float(front_min)
        self.phase17_left_min = float(left_min)
        self.phase17_right_min = float(right_min)

        # action[0] 默认速度，action[1] 默认转向
        if front_min < self.shield_front_stop:
            action[0] = min(action[0], self.shield_min_speed)

            # 哪边更空往哪边转
            if left_min > right_min:
                action[1] = abs(action[1]) + self.shield_turn_gain
            else:
                action[1] = -abs(action[1]) - self.shield_turn_gain

            self.phase17_shield_active = True
            self.phase17_shield_reason = "front_stop"

        elif front_min < self.shield_front_slow:
            action[0] = min(action[0], self.shield_slow_speed)

            if left_min < self.shield_side_near and right_min > left_min:
                action[1] = -abs(action[1]) - 0.20
                self.phase17_shield_active = True
                self.phase17_shield_reason = "left_near"
            elif right_min < self.shield_side_near and left_min > right_min:
                action[1] = abs(action[1]) + 0.20
                self.phase17_shield_active = True
                self.phase17_shield_reason = "right_near"
            else:
                self.phase17_shield_active = True
                self.phase17_shield_reason = "front_slow"

        try:
            action = np.clip(action, self.action_space.low, self.action_space.high)
        except Exception:
            action = np.clip(action, -1.0, 1.0)

        return action

    def step(self, action):
        safe_action = self._phase17_apply_safety_shield(action)
        out = super().step(safe_action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            if isinstance(info, dict):
                info["phase17_shield_active"] = bool(self.phase17_shield_active)
                info["phase17_shield_reason"] = str(self.phase17_shield_reason)
                info["phase17_front_min"] = float(self.phase17_front_min)
                info["phase17_left_min"] = float(self.phase17_left_min)
                info["phase17_right_min"] = float(self.phase17_right_min)
            return obs, reward, terminated, truncated, info

        obs, reward, done, info = out
        if isinstance(info, dict):
            info["phase17_shield_active"] = bool(self.phase17_shield_active)
            info["phase17_shield_reason"] = str(self.phase17_shield_reason)
            info["phase17_front_min"] = float(self.phase17_front_min)
            info["phase17_left_min"] = float(self.phase17_left_min)
            info["phase17_right_min"] = float(self.phase17_right_min)

        return obs, reward, done, info
