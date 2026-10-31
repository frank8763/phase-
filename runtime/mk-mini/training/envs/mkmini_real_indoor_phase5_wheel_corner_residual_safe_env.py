import numpy as np
import math

from training.envs.mkmini_real_indoor_phase5_wheel_residual_safe_astar_sac_env import (
    MkMiniRealIndoorPhase5WheelResidualSafeAStarSACEnv,
)


class MkMiniRealIndoorPhase5WheelCornerResidualSafeEnv(
    MkMiniRealIndoorPhase5WheelResidualSafeAStarSACEnv
):
    """
    Phase5 Corner:
    解决直角弯问题：
    1. A* 折线路径改成圆滑路径
    2. 转弯提前减速
    3. 大角度转弯时允许更低速、更大转向
    """

    def __init__(self):
        super().__init__()

        self.lookahead = 0.35
        self.path_step = 0.04

        # 直角弯速度更低
        self.base_wheel_norm = 0.38
        self.min_forward_norm = 0.08

        # 直角弯圆滑半径
        self.corner_cut_dist = 0.45
        self.corner_points = 12

    def _smooth_corners(self, path):
        path = np.array(path, dtype=np.float32)

        if len(path) < 3:
            return path

        new_path = [path[0]]

        for i in range(1, len(path) - 1):
            p_prev = path[i - 1]
            p = path[i]
            p_next = path[i + 1]

            v1 = p - p_prev
            v2 = p_next - p

            d1 = float(np.linalg.norm(v1))
            d2 = float(np.linalg.norm(v2))

            if d1 < 1e-6 or d2 < 1e-6:
                new_path.append(p)
                continue

            u1 = v1 / d1
            u2 = v2 / d2

            angle = math.acos(float(np.clip(np.dot(u1, u2), -1.0, 1.0)))

            # 只有明显拐角才圆滑
            if angle < 0.35:
                new_path.append(p)
                continue

            cut = min(self.corner_cut_dist, d1 * 0.45, d2 * 0.45)

            p_a = p - u1 * cut
            p_b = p + u2 * cut

            # 二次贝塞尔圆角：p_a -> p -> p_b
            for k in range(1, self.corner_points + 1):
                t = k / self.corner_points
                q = (1 - t) * (1 - t) * p_a + 2 * (1 - t) * t * p + t * t * p_b
                new_path.append(q.astype(np.float32))

        new_path.append(path[-1])
        return np.array(new_path, dtype=np.float32)

    def reset(self, *args, **kwargs):
        obs, info = super().reset(*args, **kwargs)

        # 原始 A* 路径先圆角化，再加密
        smooth_path = self._smooth_corners(self.path_world)
        self.dense_path = self._densify_path(smooth_path, step=self.path_step)

        # reset 后重新朝向圆滑路径方向
        if self.dense_path is not None and len(self.dense_path) >= 2:
            p0 = self.dense_path[0]
            p1 = self.dense_path[min(6, len(self.dense_path) - 1)]

            yaw = math.atan2(float(p1[1] - p0[1]), float(p1[0] - p0[0]))

            self.robot_xy[:] = p0
            self.robot_yaw = yaw

            self.data.qpos[0] = float(p0[0])
            self.data.qpos[1] = float(p0[1])
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

    def _base_pursuit_action(self):
        steer_norm, wheel_norm, steer, target, alpha = super()._base_pursuit_action()

        # 直角/大角度转弯：提前降速
        if abs(alpha) > 0.95:
            wheel_norm *= 0.28
        elif abs(alpha) > 0.70:
            wheel_norm *= 0.38
        elif abs(alpha) > 0.45:
            wheel_norm *= 0.55

        wheel_norm = float(np.clip(wheel_norm, self.min_forward_norm, 0.65))

        return steer_norm, wheel_norm, steer, target, alpha
