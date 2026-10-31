import numpy as np
from gymnasium import spaces

from training.phase17_fusion_safety_sac_nav.envs.mkmini_phase17b_safety_shield_env import (
    MkMiniPhase17BSafetyShieldEnv,
)

from training.phase14_lidar_depth_nav.envs.phase14_sensor_utils import (
    get_lidar_features,
    get_camera_goal_features,
)


class MkMiniPhase17CLidarCameraFusionEnv(MkMiniPhase17BSafetyShieldEnv):
    """
    Phase17-C:
    LiDAR + camera/depth feature fusion observation.

    注意：
    observation 维度会变，旧 Phase15/17B 模型不能直接加载。
    这里只先 smoke test，确认融合观测能跑。
    """

    def __init__(
        self,
        *args,
        lidar_num_rays=32,
        lidar_max_range=3.0,
        camera_fov_deg=90.0,
        camera_goal_max_range=6.0,
        depth_num_rays=15,
        depth_max_range=3.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.phase17c_lidar_num_rays = int(lidar_num_rays)
        self.phase17c_lidar_max_range = float(lidar_max_range)
        self.phase17c_camera_fov_deg = float(camera_fov_deg)
        self.phase17c_camera_goal_max_range = float(camera_goal_max_range)
        self.phase17c_depth_num_rays = int(depth_num_rays)
        self.phase17c_depth_max_range = float(depth_max_range)

        self.phase17c_base_obs_dim = int(np.prod(self.observation_space.shape))

        self.phase17c_lidar_dim = self.phase17c_lidar_num_rays
        self.phase17c_camera_dim = 5
        self.phase17c_depth_dim = self.phase17c_depth_num_rays
        self.phase17c_depth_summary_dim = 5

        self.phase17c_obs_dim = (
            self.phase17c_base_obs_dim
            + self.phase17c_lidar_dim
            + self.phase17c_camera_dim
            + self.phase17c_depth_dim
            + self.phase17c_depth_summary_dim
        )

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.phase17c_obs_dim,),
            dtype=np.float32,
        )

        self.phase17c_last_lidar = np.ones(self.phase17c_lidar_dim, dtype=np.float32)
        self.phase17c_last_camera = np.zeros(self.phase17c_camera_dim, dtype=np.float32)
        self.phase17c_last_depth = np.ones(self.phase17c_depth_dim, dtype=np.float32)
        self.phase17c_last_depth_summary = np.ones(self.phase17c_depth_summary_dim, dtype=np.float32)

    def _phase17c_get_lidar(self):
        lidar = get_lidar_features(
            self,
            num_rays=self.phase17c_lidar_num_rays,
            max_range=self.phase17c_lidar_max_range,
        )
        lidar = np.asarray(lidar, dtype=np.float32).reshape(-1)
        lidar = np.nan_to_num(lidar, nan=1.0, posinf=1.0, neginf=0.0)
        return np.clip(lidar, 0.0, 1.0)

    def _phase17c_get_camera_goal(self):
        camera = get_camera_goal_features(
            self,
            fov_deg=self.phase17c_camera_fov_deg,
            max_range=self.phase17c_camera_goal_max_range,
        )
        camera = np.asarray(camera, dtype=np.float32).reshape(-1)
        camera = np.nan_to_num(camera, nan=0.0, posinf=1.0, neginf=-1.0)
        return np.clip(camera, -1.0, 1.0)

    def _phase17c_get_depth(self):
        """
        简化 depth：
        用前方 FOV 内的 ray-cast 距离模拟 depth camera。
        输出归一化距离 [0,1]。
        """
        import math
        from training.phase14_lidar_depth_nav.envs.phase14_sensor_utils import ray_cast_distance

        yaw = float(self.robot_yaw)
        half_fov = math.radians(70.0) * 0.5

        rays = []
        n = self.phase17c_depth_num_rays
        for i in range(n):
            if n <= 1:
                rel = 0.0
            else:
                rel = -half_fov + 2.0 * half_fov * i / (n - 1)
            d = ray_cast_distance(
                self,
                yaw + rel,
                max_range=self.phase17c_depth_max_range,
                step=0.08,
            )
            rays.append(float(d) / self.phase17c_depth_max_range)

        depth = np.asarray(rays, dtype=np.float32)
        depth = np.nan_to_num(depth, nan=1.0, posinf=1.0, neginf=0.0)
        return np.clip(depth, 0.0, 1.0)

    def _phase17c_depth_summary(self, depth):
        d = np.asarray(depth, dtype=np.float32).reshape(-1)
        if d.size == 0:
            return np.ones(5, dtype=np.float32)

        left = d[: max(1, d.size // 3)]
        mid = d[max(0, d.size // 3): min(d.size, 2 * d.size // 3)]
        right = d[min(d.size, 2 * d.size // 3):]

        if mid.size == 0:
            mid = d
        if right.size == 0:
            right = d

        return np.asarray(
            [
                float(np.min(d)),
                float(np.mean(d)),
                float(np.min(left)),
                float(np.min(mid)),
                float(np.min(right)),
            ],
            dtype=np.float32,
        )

    def _phase17c_build_obs(self, base_obs):
        base_obs = np.asarray(base_obs, dtype=np.float32).reshape(-1)

        lidar = self._phase17c_get_lidar()
        camera = self._phase17c_get_camera_goal()
        depth = self._phase17c_get_depth()
        depth_summary = self._phase17c_depth_summary(depth)

        self.phase17c_last_lidar = lidar
        self.phase17c_last_camera = camera
        self.phase17c_last_depth = depth
        self.phase17c_last_depth_summary = depth_summary

        obs = np.concatenate(
            [
                base_obs,
                lidar,
                camera,
                depth,
                depth_summary,
            ],
            dtype=np.float32,
        )

        return obs.astype(np.float32)

    def reset(self, **kwargs):
        out = super().reset(**kwargs)
        if isinstance(out, tuple) and len(out) == 2:
            obs, info = out
            return self._phase17c_build_obs(obs), info
        return self._phase17c_build_obs(out)

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            obs = self._phase17c_build_obs(obs)
            if isinstance(info, dict):
                info["phase17c_obs_dim"] = int(self.phase17c_obs_dim)
                info["phase17c_base_obs_dim"] = int(self.phase17c_base_obs_dim)
                info["phase17c_lidar_min"] = float(np.min(self.phase17c_last_lidar))
                info["phase17c_camera_visible"] = float(self.phase17c_last_camera[3])
                info["phase17c_camera_align"] = float(self.phase17c_last_camera[4])
                info["phase17c_depth_min"] = float(np.min(self.phase17c_last_depth))
            return obs, reward, terminated, truncated, info

        obs, reward, done, info = out
        obs = self._phase17c_build_obs(obs)
        if isinstance(info, dict):
            info["phase17c_obs_dim"] = int(self.phase17c_obs_dim)
            info["phase17c_base_obs_dim"] = int(self.phase17c_base_obs_dim)
            info["phase17c_lidar_min"] = float(np.min(self.phase17c_last_lidar))
            info["phase17c_camera_visible"] = float(self.phase17c_last_camera[3])
            info["phase17c_camera_align"] = float(self.phase17c_last_camera[4])
            info["phase17c_depth_min"] = float(np.min(self.phase17c_last_depth))
        return obs, reward, done, info
