import math
import numpy as np
import gymnasium as gym

from training.envs.mkmini_real_indoor_astar_sac_env import MkMiniRealIndoorAStarSACEnv


class MkMiniRealIndoorCurriculumAStarSACEnv(MkMiniRealIndoorAStarSACEnv):
    def __init__(self):
        super().__init__()

        self.max_steps = 450
        self.goal_threshold = 0.45

    def reset(self, seed=None, options=None):
        gym.Env.reset(self, seed=seed)

        self.step_count = 0
        self.prev_action[:] = 0.0

        # curriculum：先训练短距离路径
        for _ in range(3000):
            start = self._sample_free_xy()
            goal = self._sample_free_xy()
            dist = np.linalg.norm(goal - start)

            if dist < 2.0 or dist > 4.5:
                continue

            path = self._plan_astar(start, goal)

            if len(path) < 6:
                continue

            self.robot_xy = start.astype(np.float32)
            self.goal_xy = goal.astype(np.float32)
            self.robot_yaw = float(self.np_random.uniform(-math.pi, math.pi))

            self.path_world = path
            self.wp_index = min(2, len(self.path_world) - 1)
            break
        else:
            self.robot_xy = np.array([-3.5, -3.5], dtype=np.float32)
            self.goal_xy = np.array([0.5, 0.5], dtype=np.float32)
            self.robot_yaw = 0.0
            self.path_world = self._plan_astar(self.robot_xy, self.goal_xy)
            self.wp_index = min(2, len(self.path_world) - 1)

        self.prev_goal_dist = self._goal_distance()
        self.prev_wp_dist = self._waypoint_distance()
        self._sync_mujoco()

        return self._get_obs(), {}

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).copy()

        # curriculum：先限制速度，减少撞墙
        action[0] = np.clip(action[0], 0.0, 0.45)
        action[1] = np.clip(action[1], -0.9, 0.9)

        obs, reward, terminated, truncated, info = super().step(action)

        min_lidar = float(info.get("min_lidar", 5.0))

        # 强化避障惩罚
        if min_lidar < 0.75:
            reward -= 8.0 * (0.75 - min_lidar)

        if bool(info.get("collision", False)):
            reward -= 250.0

        if bool(info.get("reach_goal", False)):
            reward += 120.0

        return obs, reward, terminated, truncated, info
