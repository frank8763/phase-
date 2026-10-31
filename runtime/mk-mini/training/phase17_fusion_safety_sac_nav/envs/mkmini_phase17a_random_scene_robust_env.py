import numpy as np

from training.phase14_lidar_depth_nav.envs.mkmini_phase14_phase9_yawsync_fast_nav_env import (
    MkMiniPhase14Phase9YawSyncFastNavEnv,
)


class MkMiniPhase17ARandomSceneRobustEnv(MkMiniPhase14Phase9YawSyncFastNavEnv):
    """
    Phase17-A:
    Robust navigation environment based on confirmed Phase14-F.

    Keep:
        A* global guidance
        yaw-sync fast car-like control
        SAC residual action scaling

    Add:
        randomized controller parameters
        randomized observation noise
        randomized action disturbance

    This does not modify old Phase1-14 files.
    """

    def __init__(
        self,
        obs_noise_std=0.015,
        action_noise_std=0.025,
        control_random_ratio=0.10,
        enable_domain_randomization=True,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.phase17_name = "phase17a_random_scene_robust"
        self.phase17_obs_noise_std = float(obs_noise_std)
        self.phase17_action_noise_std = float(action_noise_std)
        self.phase17_control_random_ratio = float(control_random_ratio)
        self.phase17_enable_domain_randomization = bool(enable_domain_randomization)

        self._phase17_rng = np.random.default_rng()
        self._phase17_episode_id = 0

        self._phase17_nominal = {
            "goal_capture_speed": float(self.phase14_p10_goal_capture_speed),
            "min_wheel": float(self.phase14_p10_min_wheel),
            "steer_gain": float(self.phase14_p10_steer_gain),
            "yaw_gain": float(self.phase14_p10_bicycle_yaw_gain),
            "speed_gain": float(self.phase14_p10_bicycle_speed_gain),
            "straight_wheel": float(self.phase14_p10_straight_wheel),
            "curve_wheel": float(self.phase14_p10_curve_wheel),
        }

    def _phase17_rand_scale(self):
        r = self.phase17_control_random_ratio
        return float(self._phase17_rng.uniform(1.0 - r, 1.0 + r))

    def _phase17_apply_domain_randomization(self):
        if not self.phase17_enable_domain_randomization:
            return

        n = self._phase17_nominal

        self.phase14_p10_goal_capture_speed = n["goal_capture_speed"] * self._phase17_rand_scale()
        self.phase14_p10_min_wheel = n["min_wheel"] * self._phase17_rand_scale()
        self.phase14_p10_steer_gain = n["steer_gain"] * self._phase17_rand_scale()
        self.phase14_p10_bicycle_yaw_gain = n["yaw_gain"] * self._phase17_rand_scale()
        self.phase14_p10_bicycle_speed_gain = n["speed_gain"] * self._phase17_rand_scale()
        self.phase14_p10_straight_wheel = n["straight_wheel"] * self._phase17_rand_scale()
        self.phase14_p10_curve_wheel = n["curve_wheel"] * self._phase17_rand_scale()

        self._phase14_apply_p10p11_params()

    def _phase17_add_obs_noise(self, obs):
        if self.phase17_obs_noise_std <= 0:
            return obs

        arr = np.asarray(obs, dtype=np.float32).copy()
        noise = self._phase17_rng.normal(
            loc=0.0,
            scale=self.phase17_obs_noise_std,
            size=arr.shape,
        ).astype(np.float32)

        arr = arr + noise

        try:
            low = self.observation_space.low
            high = self.observation_space.high
            arr = np.clip(arr, low, high).astype(np.float32)
        except Exception:
            arr = arr.astype(np.float32)

        return arr

    def _phase17_action_disturb(self, action):
        arr = np.asarray(action, dtype=np.float32).copy()

        if self.phase17_action_noise_std > 0:
            arr += self._phase17_rng.normal(
                loc=0.0,
                scale=self.phase17_action_noise_std,
                size=arr.shape,
            ).astype(np.float32)

        return np.clip(arr, -1.0, 1.0).astype(np.float32)

    def reset(self, **kwargs):
        self._phase17_episode_id += 1

        out = super().reset(**kwargs)

        self._phase17_apply_domain_randomization()

        if isinstance(out, tuple):
            obs, info = out
            obs = self._phase17_add_obs_noise(obs)
            if info is None:
                info = {}
            info["phase17_env"] = self.phase17_name
            return obs, info

        obs = self._phase17_add_obs_noise(out)
        return obs

    def step(self, action):
        robust_action = self._phase17_action_disturb(action)

        out = super().step(robust_action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            obs = self._phase17_add_obs_noise(obs)
            info = self._phase17_fill_info(info)
            return obs, reward, terminated, truncated, info

        obs, reward, done, info = out
        obs = self._phase17_add_obs_noise(obs)
        info = self._phase17_fill_info(info)
        return obs, reward, done, info

    def _phase17_fill_info(self, info):
        if info is None:
            info = {}

        info["phase17_env"] = self.phase17_name
        info["phase17_episode_id"] = int(self._phase17_episode_id)
        info["phase17_obs_noise_std"] = float(self.phase17_obs_noise_std)
        info["phase17_action_noise_std"] = float(self.phase17_action_noise_std)
        info["phase17_control_random_ratio"] = float(self.phase17_control_random_ratio)
        info["phase17_goal_capture_speed"] = float(self.phase14_p10_goal_capture_speed)
        info["phase17_min_wheel"] = float(self.phase14_p10_min_wheel)
        info["phase17_steer_gain"] = float(self.phase14_p10_steer_gain)
        info["phase17_yaw_gain"] = float(self.phase14_p10_bicycle_yaw_gain)
        info["phase17_speed_gain"] = float(self.phase14_p10_bicycle_speed_gain)

        return info
