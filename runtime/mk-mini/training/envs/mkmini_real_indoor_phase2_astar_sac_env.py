import math
import numpy as np
import gymnasium as gym

from training.envs.mkmini_real_indoor_curriculum_astar_sac_env import MkMiniRealIndoorCurriculumAStarSACEnv


class MkMiniRealIndoorPhase2AStarSACEnv(MkMiniRealIndoorCurriculumAStarSACEnv):
    def __init__(self):
        super().__init__()

        self.max_steps = 420
        self.goal_threshold = 0.60

    def reset(self, seed=None, options=None):
        gym.Env.reset(self, seed=seed)

        self.step_count = 0
        self.prev_action[:] = 0.0

        for _ in range(4000):
            start = self._sample_free_xy()
            goal = self._sample_free_xy()
            dist = np.linalg.norm(goal - start)

            if dist < 1.2 or dist > 3.8:
                continue

            path = self._plan_astar(start, goal)

            if len(path) < 5 or len(path) > 42:
                continue

            self.robot_xy = start.astype(np.float32)
            self.goal_xy = goal.astype(np.float32)
            self.robot_yaw = float(self.np_random.uniform(-math.pi, math.pi))

            self.path_world = path
            self.wp_index = min(2, len(self.path_world) - 1)
            break
        else:
            self.robot_xy = np.array([0.5, 1.5], dtype=np.float32)
            self.goal_xy = np.array([2.0, -0.8], dtype=np.float32)
            self.robot_yaw = -1.57
            self.path_world = self._plan_astar(self.robot_xy, self.goal_xy)
            self.wp_index = min(2, len(self.path_world) - 1)

        self.prev_goal_dist = self._goal_distance()
        self.prev_wp_dist = self._waypoint_distance()
        self._sync_mujoco()

        return self._get_obs(), {}

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).copy()

        # phase2：比 safe 版本速度稍高
        action[0] = np.clip(action[0], 0.0, 0.48)
        action[1] = np.clip(action[1], -1.0, 1.0)

        lidar = self._simulate_lidar()
        min_lidar = float(np.min(lidar))
        wp_angle = self._waypoint_angle()

        # 安全层减弱：只有很近时才强制干预
        if min_lidar < 0.55:
            action[0] = min(action[0], 0.16)

            if abs(action[1]) < 0.20:
                action[1] = 0.55 if wp_angle >= 0 else -0.55

        if min_lidar < 0.35:
            action[0] = 0.0
            action[1] = 0.70 if wp_angle >= 0 else -0.70

        old_goal_dist = self._goal_distance()

        obs, reward, terminated, truncated, info = super().step(action)

        new_goal_dist = float(info.get("goal_dist", old_goal_dist))
        progress = old_goal_dist - new_goal_dist
        min_lidar_after = float(info.get("min_lidar", 5.0))

        # phase2：重点奖励接近目标
        reward += 35.0 * progress

        # 目标奖励更强
        if bool(info.get("reach_goal", False)):
            reward += 400.0

        # 碰撞仍然重罚
        if bool(info.get("collision", False)):
            reward -= 500.0

        # 近障碍惩罚保留，但不再过强
        if min_lidar_after < 0.60:
            reward -= 10.0 * (0.60 - min_lidar_after)

        # 鼓励别一直原地拖时间
        reward -= 0.01

        return obs, reward, terminated, truncated, info
