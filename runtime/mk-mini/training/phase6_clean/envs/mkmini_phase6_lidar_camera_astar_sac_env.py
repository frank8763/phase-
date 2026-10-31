import numpy as np

try:
    from gymnasium import spaces
except Exception:
    from gym import spaces

from training.final_envs.mkmini_real_indoor_phase5_wheel_fast_corner_env_final_diff import (
    MkMiniRealIndoorPhase5WheelFastCornerEnv,
)

from training.phase6_clean.envs.sensor_utils import (
    get_lidar_features,
    get_camera_goal_features,
)


class MkMiniPhase6LidarCameraAstarSacEnv(MkMiniRealIndoorPhase5WheelFastCornerEnv):
    """
    Phase6_clean:
    LiDAR-dominant camera-assisted A*-guided SAC residual planner.

    中文创新点：
    雷达主导探索避障 + 相机辅助目标方向感知 + A* 引导 + SAC 残差局部控制。

    基础：
    - 保留 Phase5 final 的 A* + Pure Pursuit + SAC residual 控制结构
    - 不修改 Phase5 final 文件
    - 扩展 observation，不改变 action space

    observation:
    base_obs:       66维，来自 Phase5 final
    lidar_obs:      32维，360°雷达距离，主避障
    camera_goal:     5维，相机/前视目标方向辅助
    safety_feat:     4维，雷达安全摘要
    total:         107维

    action:
    action[0] = steer residual
    action[1] = speed residual
    """

    def __init__(
        self,
        lidar_num_rays=32,
        lidar_max_range=3.0,
        camera_fov_deg=90.0,
        camera_goal_max_range=6.0,
    ):
        super().__init__()

        self.lidar_num_rays = int(lidar_num_rays)
        self.lidar_max_range = float(lidar_max_range)
        self.camera_fov_deg = float(camera_fov_deg)
        self.camera_goal_max_range = float(camera_goal_max_range)

        self.base_obs_dim = int(np.prod(self.observation_space.shape))
        self.camera_dim = 5
        self.safety_dim = 4
        self.phase6_obs_dim = (
            self.base_obs_dim
            + self.lidar_num_rays
            + self.camera_dim
            + self.safety_dim
        )

        self.observation_space = spaces.Box(
            low=-10.0,
            high=10.0,
            shape=(self.phase6_obs_dim,),
            dtype=np.float32,
        )

        self.last_lidar = np.ones(self.lidar_num_rays, dtype=np.float32)
        self.last_camera_goal = np.zeros(self.camera_dim, dtype=np.float32)
        self.last_safety = np.ones(self.safety_dim, dtype=np.float32)

    def _get_lidar(self):
        lidar = get_lidar_features(
            self,
            num_rays=self.lidar_num_rays,
            max_range=self.lidar_max_range,
        )
        lidar = np.asarray(lidar, dtype=np.float32).reshape(-1)
        lidar = np.clip(lidar, 0.0, 1.0)
        return lidar

    def _get_camera_goal(self):
        camera_goal = get_camera_goal_features(
            self,
            fov_deg=self.camera_fov_deg,
            max_range=self.camera_goal_max_range,
        )
        camera_goal = np.asarray(camera_goal, dtype=np.float32).reshape(-1)
        camera_goal = np.clip(camera_goal, -1.0, 1.0)
        return camera_goal

    def _get_safety_feat(self, lidar):
        n = len(lidar)

        front = float(lidar[0])
        left = float(lidar[n // 4])
        rear = float(lidar[n // 2])
        right = float(lidar[(3 * n) // 4])
        min_lidar = float(np.min(lidar))

        return np.asarray(
            [
                min_lidar,
                front,
                left,
                right,
            ],
            dtype=np.float32,
        )

    def _build_phase6_obs(self, base_obs):
        base_obs = np.asarray(base_obs, dtype=np.float32).reshape(-1)

        lidar = self._get_lidar()
        camera_goal = self._get_camera_goal()
        safety = self._get_safety_feat(lidar)

        self.last_lidar = lidar
        self.last_camera_goal = camera_goal
        self.last_safety = safety

        obs = np.concatenate(
            [
                base_obs,
                lidar,
                camera_goal,
                safety,
            ],
            axis=0,
        ).astype(np.float32)

        obs = np.nan_to_num(obs, nan=0.0, posinf=10.0, neginf=-10.0)
        obs = np.clip(obs, -10.0, 10.0)

        return obs

    def reset(self, *args, **kwargs):
        out = super().reset(*args, **kwargs)

        if isinstance(out, tuple):
            base_obs, info = out
            return self._build_phase6_obs(base_obs), info

        base_obs = out
        return self._build_phase6_obs(base_obs)

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            base_obs, reward, terminated, truncated, info = out
            done = bool(terminated or truncated)
            new_reward, info = self._shape_reward(float(reward), info)
            obs = self._build_phase6_obs(base_obs)
            return obs, new_reward, terminated, truncated, info

        base_obs, reward, done, info = out
        new_reward, info = self._shape_reward(float(reward), info)
        obs = self._build_phase6_obs(base_obs)
        return obs, new_reward, done, info

    def _shape_reward(self, reward, info):
        if info is None:
            info = {}

        lidar = self.last_lidar
        camera_goal = self.last_camera_goal
        safety = self.last_safety

        min_lidar = float(safety[0])
        front_lidar = float(safety[1])
        camera_visible = float(camera_goal[3])
        camera_align = float(camera_goal[4])

        # LiDAR 主导避障：距离越近惩罚越强
        danger = max(0.0, (0.28 - min_lidar) / 0.28)
        front_danger = max(0.0, (0.32 - front_lidar) / 0.32)

        lidar_penalty = -2.0 * danger - 1.0 * front_danger

        # camera 只作为目标方向辅助，不主导避障
        camera_goal_bonus = 0.15 * camera_visible * camera_align

        # 路径跟踪保持 Phase5 思路
        try:
            path_error = float(self._nearest_path_error())
        except Exception:
            path_error = 0.0

        path_penalty = -0.10 * path_error

        reward = reward + lidar_penalty + camera_goal_bonus + path_penalty

        collision = bool(info.get("collision", False))
        if collision:
            reward -= 30.0

        info["phase6_min_lidar"] = min_lidar
        info["phase6_front_lidar"] = front_lidar
        info["phase6_camera_visible"] = camera_visible
        info["phase6_camera_align"] = camera_align
        info["phase6_lidar_danger"] = danger
        info["phase6_front_danger"] = front_danger
        info["phase6_path_error"] = path_error

        return float(reward), info
