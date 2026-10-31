import numpy as np
try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:
    import gym
    from gym import spaces
from stable_baselines3 import SAC

from training.phase7_camera_depth.envs.mkmini_phase7_depth_camera_aux_env import (
    MkMiniPhase7DepthCameraAuxEnv,
)


class MkMiniPhase7ResidualCameraAuxEnv(gym.Env):
    def __init__(
        self,
        base_model_path="training/phase6_clean/confirmed/phase6_v1_lidar_main_camera_goal_55k_confirmed.zip",
        residual_scale=0.18,
        residual_penalty=0.04,
        path_error_penalty=0.25,
        depth_rays=15,
        depth_range=3.5,
        depth_fov=90.0,
    ):
        super().__init__()

        self.inner = MkMiniPhase7DepthCameraAuxEnv(
            depth_rays=depth_rays,
            depth_range=depth_range,
            depth_fov=depth_fov,
        )

        self.base_model = SAC.load(base_model_path, device="cpu")

        self.residual_scale = float(residual_scale)
        self.residual_penalty = float(residual_penalty)
        self.path_error_penalty = float(path_error_penalty)

        self.phase6_obs_dim = 107
        self.raw_obs_dim = int(self.inner.observation_space.shape[0])

        low = np.concatenate(
            [
                self.inner.observation_space.low.astype(np.float32),
                np.array([-1.0, -1.0], dtype=np.float32),
            ]
        )

        high = np.concatenate(
            [
                self.inner.observation_space.high.astype(np.float32),
                np.array([1.0, 1.0], dtype=np.float32),
            ]
        )

        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(2,),
            dtype=np.float32,
        )

        self.last_raw_obs = None
        self.last_base_action = np.zeros(2, dtype=np.float32)
        self.last_residual_action = np.zeros(2, dtype=np.float32)
        self.last_final_action = np.zeros(2, dtype=np.float32)

    def __getattr__(self, name):
        if name != "inner" and "inner" in self.__dict__:
            return getattr(self.__dict__["inner"], name)
        raise AttributeError(name)

    def _base_action(self, raw_obs):
        phase6_obs = np.asarray(raw_obs[: self.phase6_obs_dim], dtype=np.float32)
        action, _ = self.base_model.predict(phase6_obs, deterministic=True)
        action = np.asarray(action, dtype=np.float32).reshape(2)
        return np.clip(action, -1.0, 1.0)

    def _make_obs(self, raw_obs):
        base_action = self._base_action(raw_obs)
        self.last_base_action = base_action.astype(np.float32)
        obs = np.concatenate(
            [
                np.asarray(raw_obs, dtype=np.float32),
                self.last_base_action,
            ]
        ).astype(np.float32)
        return obs

    def reset(self, **kwargs):
        out = self.inner.reset(**kwargs)

        if isinstance(out, tuple):
            raw_obs, info = out
            self.last_raw_obs = np.asarray(raw_obs, dtype=np.float32)
            return self._make_obs(self.last_raw_obs), info

        self.last_raw_obs = np.asarray(out, dtype=np.float32)
        return self._make_obs(self.last_raw_obs)

    def step(self, action):
        action = np.asarray(action, dtype=np.float32).reshape(2)
        action = np.clip(action, -1.0, 1.0)

        base_action = self._base_action(self.last_raw_obs)
        residual_action = self.residual_scale * action
        final_action = np.clip(base_action + residual_action, -1.0, 1.0)

        self.last_base_action = base_action.astype(np.float32)
        self.last_residual_action = residual_action.astype(np.float32)
        self.last_final_action = final_action.astype(np.float32)

        out = self.inner.step(final_action)

        if len(out) == 5:
            raw_obs, reward, terminated, truncated, info = out
            done = bool(terminated or truncated)
            is_gymnasium = True
        else:
            raw_obs, reward, done, info = out
            terminated = bool(done)
            truncated = False
            is_gymnasium = False

        self.last_raw_obs = np.asarray(raw_obs, dtype=np.float32)

        path_error = float(self.inner._nearest_path_error())
        residual_norm = float(np.linalg.norm(residual_action))

        shaped_reward = float(reward)
        shaped_reward -= self.residual_penalty * residual_norm
        shaped_reward -= self.path_error_penalty * max(0.0, path_error - 0.22)

        obs = self._make_obs(self.last_raw_obs)

        if isinstance(info, dict):
            info["base_action"] = self.last_base_action.copy()
            info["residual_action"] = self.last_residual_action.copy()
            info["final_action"] = self.last_final_action.copy()

        if is_gymnasium:
            return obs, shaped_reward, terminated, truncated, info

        return obs, shaped_reward, bool(done), info

    def render(self, *args, **kwargs):
        return self.inner.render(*args, **kwargs)

    def close(self):
        return self.inner.close()
