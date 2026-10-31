import numpy as np
import mujoco
from gymnasium import spaces

from training.envs.mkmini_real_indoor_phase2_astar_sac_env import (
    MkMiniRealIndoorPhase2AStarSACEnv,
)


class MkMiniRealIndoorPhase3DepthAStarSACEnv(MkMiniRealIndoorPhase2AStarSACEnv):
    """
    phase3:
    - 继承 phase2 的真实室内 A* + SAC 环境
    - 原始观测 42 维
    - 增加 D435i depth 24 维特征
    - 总观测 66 维
    - 动作仍然是 [v, w]
    """

    def __init__(self):
        super().__init__()

        self.depth_max_range = 5.0
        self.depth_feature_dim = 24

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(66,),
            dtype=np.float32,
        )

        self.depth_camera_name = "d435i_depth"
        self.depth_camera_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_CAMERA,
            self.depth_camera_name,
        )

        self.renderer = mujoco.Renderer(
            self.model,
            height=64,
            width=64,
        )

    def _get_depth_features(self):
        if self.depth_camera_id < 0:
            return np.ones(self.depth_feature_dim, dtype=np.float32)

        try:
            self.renderer.update_scene(self.data, camera=self.depth_camera_name)
            self.renderer.enable_depth_rendering()
            depth = self.renderer.render()
            self.renderer.disable_depth_rendering()
        except Exception:
            return np.ones(self.depth_feature_dim, dtype=np.float32)

        if depth.ndim == 3:
            depth = depth[:, :, 0]

        depth = np.nan_to_num(
            depth,
            nan=self.depth_max_range,
            posinf=self.depth_max_range,
            neginf=0.0,
        )

        depth = np.clip(depth, 0.0, self.depth_max_range)

        h, w = depth.shape

        row_centers = [
            int(h * 0.30),
            int(h * 0.50),
            int(h * 0.70),
        ]

        col_edges = np.linspace(0, w, 9).astype(int)

        feats = []

        for r in row_centers:
            r0 = max(0, r - 3)
            r1 = min(h, r + 4)

            for i in range(8):
                c0 = col_edges[i]
                c1 = col_edges[i + 1]
                patch = depth[r0:r1, c0:c1]

                if patch.size == 0:
                    value = self.depth_max_range
                else:
                    value = float(np.mean(patch))

                feats.append(value / self.depth_max_range)

        return np.array(feats, dtype=np.float32)

    def _get_obs(self):
        obs42 = super()._get_obs().astype(np.float32)
        depth24 = self._get_depth_features()

        obs66 = np.concatenate([obs42, depth24], axis=0).astype(np.float32)

        return obs66

    def close(self):
        try:
            self.renderer.close()
        except Exception:
            pass
