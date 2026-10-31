import numpy as np

try:
    from gymnasium import spaces
except Exception:
    from gym import spaces

from training.phase6_clean.envs.mkmini_phase6_lidar_camera_astar_sac_env import (
    MkMiniPhase6LidarCameraAstarSacEnv,
)

from training.phase7_camera_depth.envs.camera_depth_utils import (
    get_front_depth_camera_features,
    get_front_depth_summary,
)


class MkMiniPhase7DepthCameraAuxEnv(MkMiniPhase6LidarCameraAstarSacEnv):
    def __init__(self, depth_rays=15, depth_range=3.5, depth_fov=90.0):
        super().__init__(
            lidar_num_rays=32,
            lidar_max_range=3.0,
            camera_fov_deg=90.0,
            camera_goal_max_range=6.0,
        )

        self.depth_rays = int(depth_rays)
        self.depth_range = float(depth_range)
        self.depth_fov = float(depth_fov)

        self.phase6_obs_dim = int(np.prod(self.observation_space.shape))
        self.depth_summary_dim = 5
        self.phase7_obs_dim = self.phase6_obs_dim + self.depth_rays + self.depth_summary_dim

        self.observation_space = spaces.Box(
            low=-10.0,
            high=10.0,
            shape=(self.phase7_obs_dim,),
            dtype=np.float32,
        )

        self.last_depth = np.ones(self.depth_rays, dtype=np.float32)
        self.last_depth_summary = np.ones(self.depth_summary_dim, dtype=np.float32)

    def _get_depth(self):
        depth = get_front_depth_camera_features(
            self,
            num_rays=self.depth_rays,
            fov_deg=self.depth_fov,
            max_range=self.depth_range,
        )
        return np.clip(np.asarray(depth, dtype=np.float32), 0.0, 1.0)

    def _build_phase7_obs(self, phase6_obs):
        phase6_obs = np.asarray(phase6_obs, dtype=np.float32).reshape(-1)

        depth = self._get_depth()
        depth_summary = get_front_depth_summary(depth)

        self.last_depth = depth
        self.last_depth_summary = depth_summary

        obs = np.concatenate([phase6_obs, depth, depth_summary]).astype(np.float32)
        obs = np.nan_to_num(obs, nan=0.0, posinf=10.0, neginf=-10.0)
        return np.clip(obs, -10.0, 10.0)

    def reset(self, *args, **kwargs):
        out = super().reset(*args, **kwargs)
        if isinstance(out, tuple):
            obs, info = out
            return self._build_phase7_obs(obs), info
        return self._build_phase7_obs(out)

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            return self._build_phase7_obs(obs), reward, terminated, truncated, info

        obs, reward, done, info = out
        return self._build_phase7_obs(obs), reward, done, info
