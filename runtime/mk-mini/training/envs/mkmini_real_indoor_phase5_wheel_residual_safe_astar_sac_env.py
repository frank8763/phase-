import math
import numpy as np
from gymnasium import spaces

from training.envs.mkmini_real_indoor_phase5_wheel_safe_astar_sac_env import (
    MkMiniRealIndoorPhase5WheelSafeAStarSACEnv,
)


class MkMiniRealIndoorPhase5WheelResidualSafeAStarSACEnv(
    MkMiniRealIndoorPhase5WheelSafeAStarSACEnv
):
    """
    Phase5 Residual Safe Wheel:

    基础控制器：
        A* + Pure Pursuit -> base_steer, base_wheel_norm

    SAC 只学习修正量：
        action[0] -> steer residual
        action[1] -> speed residual

    安全层：
        靠近障碍物后退
        拉开距离后转向
        再重新前进
    """

    def __init__(self):
        super().__init__()

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        self.lookahead = 0.70
        self.path_step = 0.05

        self.base_wheel_norm = 0.48
        self.min_forward_norm = 0.12

        self.steer_residual_scale = 0.20
        self.speed_residual_scale = 0.12

        self.dense_path = None

        # 偏离路径恢复
        self.path_stuck_counter = 0
        self.prev_goal_dist_residual = None
        self.path_error_trigger = 0.55
        self.path_stuck_trigger_steps = 25

    def _wrap_angle_local(self, a):
        return (a + math.pi) % (2.0 * math.pi) - math.pi

    def _densify_path(self, path, step=0.05):
        path = np.array(path, dtype=np.float32)

        if len(path) < 2:
            return path

        dense = [path[0]]

        for i in range(len(path) - 1):
            p0 = path[i]
            p1 = path[i + 1]
            vec = p1 - p0
            dist = float(np.linalg.norm(vec))

            if dist < 1e-6:
                continue

            n = max(1, int(dist / step))

            for k in range(1, n + 1):
                dense.append(p0 + vec * (k / n))

        return np.array(dense, dtype=np.float32)

    def _select_lookahead_point(self):
        if self.dense_path is None or len(self.dense_path) == 0:
            return np.array(self.goal_xy, dtype=np.float32)

        pos = np.array(self.robot_xy, dtype=np.float32)
        path = self.dense_path

        d = np.linalg.norm(path - pos[None, :], axis=1)
        nearest = int(np.argmin(d))

        acc = 0.0

        for i in range(nearest, len(path) - 1):
            seg = float(np.linalg.norm(path[i + 1] - path[i]))
            acc += seg

            if acc >= self.lookahead:
                return path[i + 1]

        return path[-1]

    def _base_pursuit_action(self):
        self._update_pose_from_mujoco()

        target = self._select_lookahead_point()

        dx = float(target[0] - self.robot_xy[0])
        dy = float(target[1] - self.robot_xy[1])

        target_yaw = math.atan2(dy, dx)
        alpha = self._wrap_angle_local(target_yaw - self.robot_yaw)

        steer = math.atan2(
            2.0 * self.wheel_base * math.sin(alpha),
            max(self.lookahead, 1e-3),
        )
        steer = float(np.clip(steer, -self.max_steer, self.max_steer))

        goal_dist = float(self._goal_distance())

        wheel_norm = self.base_wheel_norm

        # 转弯自动减速，减少切弯
        if abs(steer) > 0.30:
            wheel_norm *= 0.50
        elif abs(steer) > 0.20:
            wheel_norm *= 0.68
        elif abs(steer) > 0.12:
            wheel_norm *= 0.82

        # 接近目标减速
        if goal_dist < 1.5:
            wheel_norm *= max(0.45, goal_dist / 1.5)

        wheel_norm = float(np.clip(wheel_norm, self.min_forward_norm, 0.65))

        steer_norm = steer / self.max_steer

        return steer_norm, wheel_norm, steer, target, alpha

    def reset(self, *args, **kwargs):
        obs, info = super().reset(*args, **kwargs)

        self.dense_path = self._densify_path(self.path_world, step=self.path_step)

        self.path_stuck_counter = 0
        self.prev_goal_dist_residual = float(self._goal_distance())

        # Ackermann 车不能原地横移，reset 后必须让车头大致朝向 A* 路径方向
        if self.dense_path is not None and len(self.dense_path) >= 2:
            p0 = self.dense_path[0]
            p1 = self.dense_path[min(6, len(self.dense_path) - 1)]

            yaw = math.atan2(float(p1[1] - p0[1]), float(p1[0] - p0[0]))

            self.robot_xy[:] = p0
            self.robot_yaw = yaw

            self.data.qpos[0] = float(p0[0])
            self.data.qpos[1] = float(p0[1])

            # 保持原高度，只修正 yaw
            self.data.qpos[3] = math.cos(yaw / 2.0)
            self.data.qpos[4] = 0.0
            self.data.qpos[5] = 0.0
            self.data.qpos[6] = math.sin(yaw / 2.0)

            self.data.qvel[:] = 0.0
            self.data.ctrl[:] = 0.0

            import mujoco
            mujoco.mj_forward(self.model, self.data)

            self._update_pose_from_mujoco()

        return self._get_obs(), info

    def step(self, action):
        action = np.asarray(action, dtype=np.float32)

        # 如果已经明显偏离蓝色路径，并且目标距离没有继续下降，
        # 说明车正在离开路径或卡在错误方向，需要主动恢复。
        current_goal_dist = float(self._goal_distance())
        current_path_error = float(self._nearest_path_error())

        if self.prev_goal_dist_residual is None:
            self.prev_goal_dist_residual = current_goal_dist

        progress = self.prev_goal_dist_residual - current_goal_dist

        if (
            self.recovery_stage == "NORMAL"
            and current_path_error > self.path_error_trigger
            and progress < 0.001
            and current_goal_dist > 1.0
        ):
            self.path_stuck_counter += 1
        else:
            self.path_stuck_counter = max(0, self.path_stuck_counter - 2)

        if self.path_stuck_counter > self.path_stuck_trigger_steps:
            c = self._lidar_clearance()
            self._start_recovery(c)
            self.path_stuck_counter = 0

        base_steer_norm, base_wheel_norm, base_steer, target, alpha = self._base_pursuit_action()

        steer_norm = base_steer_norm + self.steer_residual_scale * float(action[0])
        wheel_norm = base_wheel_norm + self.speed_residual_scale * float(action[1])

        steer_norm = float(np.clip(steer_norm, -1.0, 1.0))

        # 正常情况下不让策略频繁倒车，倒车交给 safety recovery
        wheel_norm = float(np.clip(wheel_norm, 0.05, 0.75))

        final_action = np.array([steer_norm, wheel_norm], dtype=np.float32)

        obs, reward, terminated, truncated, info = super().step(final_action)

        # 额外奖励：贴近路径、减少无意义大修正
        path_error = info.get("path_error", 0.0)
        reward -= 0.4 * path_error
        reward -= 0.03 * abs(float(action[0]))
        reward -= 0.02 * abs(float(action[1]))

        info["base_steer"] = base_steer
        info["base_steer_norm"] = base_steer_norm
        info["base_wheel_norm"] = base_wheel_norm
        info["final_steer_norm"] = steer_norm
        info["final_wheel_norm"] = wheel_norm
        info["target_x"] = float(target[0])
        info["target_y"] = float(target[1])
        info["alpha"] = alpha
        info["path_stuck_counter"] = self.path_stuck_counter

        self.prev_goal_dist_residual = float(info.get("goal_dist", current_goal_dist))

        return obs, float(reward), terminated, truncated, info
