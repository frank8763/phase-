import numpy as np

from training.phase19_unknown_obstacle_stress.envs.mkmini_phase19_offset_unknown_obstacle_env import (
    MkMiniPhase19OffsetUnknownObstacleEnv,
)

from training.phase18_ablation.scripts.eval_phase18_B2_true_no_lidar_fixed_seed import (
    MkMiniPhase18B2TrueNoLidarEnv,
)

from training.phase18_ablation.scripts.eval_phase18_C2_true_no_camera_depth_fixed_seed import (
    MkMiniPhase18C2TrueNoCameraDepthEnv,
)

from training.phase18_ablation.scripts.eval_phase18_D_no_safety_shield_fixed_seed import (
    MkMiniPhase18DNoSafetyShieldEnv,
)

from training.phase18_ablation.scripts.eval_phase18_G_no_sensors_no_shield_fixed_seed import (
    MkMiniPhase18GNoSensorsNoShieldEnv,
)


class _Phase19FormalGroupMixin:
    """
    Phase19正式分组公共包装层。

    功能：
    1. 保留Phase18已经验证的内部消融逻辑；
    2. 对最终交给SAC的186维观测再次强制掩码；
    3. D/G绕过Shield后，补回Phase19未知障碍统计；
    4. 不修改任何Phase18及更早阶段代码。
    """

    PHASE19_GROUP_NAME = "UNKNOWN"
    PHASE19_SHIELD_ENABLED = True
    PHASE19_FINAL_MASK_SLICES = ()
    PHASE19_OBS_DIM = 186

    def _phase19_apply_final_mask(self, obs):
        masked = np.asarray(
            obs,
            dtype=np.float32,
        ).reshape(-1).copy()

        if masked.size != self.PHASE19_OBS_DIM:
            raise RuntimeError(
                f"{self.PHASE19_GROUP_NAME}: "
                f"obs_dim={masked.size}, expected=186"
            )

        for start, end in self.PHASE19_FINAL_MASK_SLICES:
            masked[start:end] = 0.0

        return masked

    def _phase19_add_group_info(self, info):
        if info is None:
            info = {}

        # D/G的Phase18 step绕过了Phase19 step，
        # 因此必须在这里统一补回Phase19记录。
        info = self._phase19_fill_info(info)

        info["phase19_formal_group"] = (
            self.PHASE19_GROUP_NAME
        )
        info["phase19_safety_shield_enabled"] = bool(
            self.PHASE19_SHIELD_ENABLED
        )
        info["phase19_final_mask_slices"] = tuple(
            self.PHASE19_FINAL_MASK_SLICES
        )

        return info

    def reset(self, *args, **kwargs):
        out = super().reset(*args, **kwargs)

        if isinstance(out, tuple) and len(out) == 2:
            obs, info = out
            obs = self._phase19_apply_final_mask(obs)
            info = self._phase19_add_group_info(info)
            return obs, info

        return self._phase19_apply_final_mask(out)

    def step(self, action):
        out = super().step(action)

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            obs = self._phase19_apply_final_mask(obs)
            info = self._phase19_add_group_info(info)

            return (
                obs,
                reward,
                terminated,
                truncated,
                info,
            )

        obs, reward, done, info = out
        obs = self._phase19_apply_final_mask(obs)
        info = self._phase19_add_group_info(info)

        return obs, reward, done, info


class MkMiniPhase19AFullEnv(
    _Phase19FormalGroupMixin,
    MkMiniPhase19OffsetUnknownObstacleEnv,
):
    PHASE19_GROUP_NAME = "A_FULL"
    PHASE19_SHIELD_ENABLED = True
    PHASE19_FINAL_MASK_SLICES = ()


class MkMiniPhase19B2NoLidarEnv(
    _Phase19FormalGroupMixin,
    MkMiniPhase18B2TrueNoLidarEnv,
    MkMiniPhase19OffsetUnknownObstacleEnv,
):
    """
    无LiDAR策略观测，但Safety Shield继续使用物理LiDAR。

    清零：
    66:98   Phase6 LiDAR
    103:107 Phase6 LiDAR安全摘要
    129:161 Phase17 LiDAR
    """

    PHASE19_GROUP_NAME = "B2_NO_LIDAR"
    PHASE19_SHIELD_ENABLED = True
    PHASE19_FINAL_MASK_SLICES = (
        (66, 98),
        (103, 107),
        (129, 161),
    )


class MkMiniPhase19C2NoCameraDepthEnv(
    _Phase19FormalGroupMixin,
    MkMiniPhase18C2TrueNoCameraDepthEnv,
    MkMiniPhase19OffsetUnknownObstacleEnv,
):
    """
    无Camera/Depth策略观测，保留LiDAR和Safety Shield。

    清零：
    98:103  Phase6 Camera Goal
    107:127 Phase7 Depth及摘要
    161:186 Phase17 Camera/Depth及摘要
    """

    PHASE19_GROUP_NAME = "C2_NO_CAMERA_DEPTH"
    PHASE19_SHIELD_ENABLED = True
    PHASE19_FINAL_MASK_SLICES = (
        (98, 103),
        (107, 127),
        (161, 186),
    )


class MkMiniPhase19DNoShieldEnv(
    _Phase19FormalGroupMixin,
    MkMiniPhase18DNoSafetyShieldEnv,
    MkMiniPhase19OffsetUnknownObstacleEnv,
):
    PHASE19_GROUP_NAME = "D_NO_SHIELD"
    PHASE19_SHIELD_ENABLED = False
    PHASE19_FINAL_MASK_SLICES = ()


class MkMiniPhase19GNoPerceptionNoShieldEnv(
    _Phase19FormalGroupMixin,
    MkMiniPhase18GNoSensorsNoShieldEnv,
    MkMiniPhase19OffsetUnknownObstacleEnv,
):
    """
    无显式LiDAR、Camera、Depth观测，同时关闭Safety Shield。

    保留：
    0:66    状态、路径和控制特征
    127:129 基础策略动作

    清零：
    66:127  Phase6/Phase7全部显式感知
    129:186 Phase17全部显式感知
    """

    PHASE19_GROUP_NAME = "G_NO_PERCEPTION_NO_SHIELD"
    PHASE19_SHIELD_ENABLED = False
    PHASE19_FINAL_MASK_SLICES = (
        (66, 127),
        (129, 186),
    )


PHASE19_FORMAL_GROUPS = {
    "A": MkMiniPhase19AFullEnv,
    "B2": MkMiniPhase19B2NoLidarEnv,
    "C2": MkMiniPhase19C2NoCameraDepthEnv,
    "D": MkMiniPhase19DNoShieldEnv,
    "G": MkMiniPhase19GNoPerceptionNoShieldEnv,
}
