import math
import numpy as np
import mujoco
from gymnasium import spaces

from training.envs.mkmini_real_indoor_phase4_recovery_sac_env import (
    MkMiniRealIndoorPhase4RecoverySACEnv,
)


class MkMiniRealIndoorPhase5WheelAStarSACEnv(MkMiniRealIndoorPhase4RecoverySACEnv):
    """
    Phase5:
    真实车轮动力学 + A* 路径 + LiDAR + SAC

    action:
        action[0] -> steer command, normalized [-1, 1]
        action[1] -> wheel speed command, normalized [-1, 1]

    实际控制:
        left_front_steer_act
        right_front_steer_act
        left_rear_wheel_act
        right_rear_wheel_act
    """

    def __init__(self):
        super().__init__()

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        self.goal_threshold = 0.90
        self.max_steps = 1800

        # 真实车轮控制参数
        self.max_steer = 0.36
        self.max_wheel_speed = 8.0

        self.wheel_radius = 0.12
        self.wheel_base = 0.60
        self.track_width = 0.54

        self.diff_gain = 2.5

        # 控制平滑
        self.max_steer_delta = 0.020
        self.max_wheel_delta = 0.18

        self.last_lf_steer = 0.0
        self.last_rf_steer = 0.0
        self.last_lr_wheel = 0.0
        self.last_rr_wheel = 0.0

        # actuator id
        self.id_lf_steer = self._aid("left_front_steer_act")
        self.id_rf_steer = self._aid("right_front_steer_act")
        self.id_lr_wheel = self._aid("left_rear_wheel_act")
        self.id_rr_wheel = self._aid("right_rear_wheel_act")

        self.sim_dt = float(self.model.opt.timestep)
        self.substeps = max(1, int(round(self.dt / self.sim_dt)))

    def _aid(self, name):
        idx = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
        if idx < 0:
            raise RuntimeError(f"actuator not found: {name}")
        return idx

    def _quat_to_yaw(self, q):
        w, x, y, z = q
        return math.atan2(
            2.0 * (w * z + x * y),
            1.0 - 2.0 * (y * y + z * z),
        )

    def _update_pose_from_mujoco(self):
        self.robot_xy[:] = self.data.qpos[0:2]
        self.robot_yaw = self._quat_to_yaw(self.data.qpos[3:7])

    def _rate_limit(self, x, last_x, max_delta):
        return float(np.clip(x, last_x - max_delta, last_x + max_delta))

    def _ackermann_from_steer_speed(self, steer, wheel_speed):
        steer = float(np.clip(steer, -self.max_steer, self.max_steer))
        wheel_speed = float(np.clip(wheel_speed, -self.max_wheel_speed, self.max_wheel_speed))

        v = wheel_speed * self.wheel_radius

        if abs(steer) < 1e-4:
            lf = 0.0
            rf = 0.0
            lr = wheel_speed
            rr = wheel_speed
            return lf, rf, lr, rr

        # 修正 Ackermann 符号：
        # steer > 0 左转，左右前轮都应为正
        # steer < 0 右转，左右前轮都应为负
        sign = 1.0 if steer > 0.0 else -1.0
        abs_steer = abs(steer)

        R = self.wheel_base / math.tan(abs_steer)
        yaw_rate = sign * v / R if abs(R) > 1e-6 else 0.0

        left_v = v - self.diff_gain * yaw_rate * self.track_width / 2.0
        right_v = v + self.diff_gain * yaw_rate * self.track_width / 2.0

        inner = math.atan2(self.wheel_base, max(R - self.track_width / 2.0, 1e-4))
        outer = math.atan2(self.wheel_base, R + self.track_width / 2.0)

        if sign > 0:
            # 左转：左轮内侧，右轮外侧
            lf = inner
            rf = outer
        else:
            # 右转：右轮内侧，左轮外侧，符号必须为负
            lf = -outer
            rf = -inner

        lf = float(np.clip(lf, -self.max_steer, self.max_steer))
        rf = float(np.clip(rf, -self.max_steer, self.max_steer))

        lr = float(np.clip(left_v / self.wheel_radius, -self.max_wheel_speed, self.max_wheel_speed))
        rr = float(np.clip(right_v / self.wheel_radius, -self.max_wheel_speed, self.max_wheel_speed))

        return lf, rf, lr, rr

    def _apply_wheel_ctrl(self, lf, rf, lr, rr):
        lf = self._rate_limit(lf, self.last_lf_steer, self.max_steer_delta)
        rf = self._rate_limit(rf, self.last_rf_steer, self.max_steer_delta)
        lr = self._rate_limit(lr, self.last_lr_wheel, self.max_wheel_delta)
        rr = self._rate_limit(rr, self.last_rr_wheel, self.max_wheel_delta)

        self.last_lf_steer = lf
        self.last_rf_steer = rf
        self.last_lr_wheel = lr
        self.last_rr_wheel = rr

        self.data.ctrl[:] = 0.0
        self.data.ctrl[self.id_lf_steer] = lf
        self.data.ctrl[self.id_rf_steer] = rf
        self.data.ctrl[self.id_lr_wheel] = lr
        self.data.ctrl[self.id_rr_wheel] = rr

        # 机械臂保持为 0
        if self.model.nu > 4:
            self.data.ctrl[4:] = 0.0

    def reset(self, *args, **kwargs):
        obs, info = super().reset(*args, **kwargs)

        self.last_lf_steer = 0.0
        self.last_rf_steer = 0.0
        self.last_lr_wheel = 0.0
        self.last_rr_wheel = 0.0

        self.data.ctrl[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

        self._update_pose_from_mujoco()

        return self._get_obs(), info

    def _nearest_path_error(self):
        if not hasattr(self, "path_world") or len(self.path_world) == 0:
            return 0.0

        path = np.array(self.path_world, dtype=np.float32)
        pos = np.array(self.robot_xy, dtype=np.float32)

        d = np.linalg.norm(path - pos[None, :], axis=1)
        return float(np.min(d))

    def step(self, action):
        action = np.asarray(action, dtype=np.float32)

        old_goal_dist = float(self._goal_distance())
        old_wp_dist = float(self._waypoint_distance())

        steer_cmd = float(np.clip(action[0], -1.0, 1.0)) * self.max_steer

        # 允许低速倒车，但主要范围仍偏向前进
        wheel_norm = float(np.clip(action[1], -1.0, 1.0))
        wheel_speed = wheel_norm * self.max_wheel_speed

        lf, rf, lr, rr = self._ackermann_from_steer_speed(steer_cmd, wheel_speed)
        self._apply_wheel_ctrl(lf, rf, lr, rr)

        for _ in range(self.substeps):
            mujoco.mj_step(self.model, self.data)

        self._update_pose_from_mujoco()
        self.step_count += 1
        self._update_waypoint()

        goal_dist = float(self._goal_distance())
        wp_dist = float(self._waypoint_distance())
        path_error = self._nearest_path_error()

        lidar = self._simulate_lidar()
        min_lidar = float(np.min(lidar))

        collision = bool(self._check_collision())
        reach_goal = bool(goal_dist < self.goal_threshold)
        timeout = bool(self.step_count >= self.max_steps)

        goal_progress = old_goal_dist - goal_dist
        wp_progress = old_wp_dist - wp_dist

        reward = 0.0

        # 到目标和 waypoint 的进步
        reward += 12.0 * goal_progress
        reward += 6.0 * wp_progress

        # 贴近 A* 路径
        reward -= 0.8 * path_error

        # 时间惩罚
        reward -= 0.05

        # 鼓励前进，但不要高速倒退
        if wheel_speed > 0:
            reward += 0.02 * wheel_speed
        else:
            reward -= 0.03 * abs(wheel_speed)

        # 离障碍物太近惩罚
        if min_lidar < 0.45:
            reward -= 4.0 * (0.45 - min_lidar)

        # 动作平滑惩罚
        reward -= 0.02 * abs(steer_cmd)
        reward -= 0.003 * abs(wheel_speed)

        if reach_goal:
            reward += 500.0

        if collision:
            reward -= 500.0

        if timeout and not reach_goal:
            reward -= 30.0

        terminated = bool(reach_goal or collision)
        truncated = bool(timeout and not terminated)

        self.prev_action = np.array([steer_cmd, wheel_speed], dtype=np.float32)

        info = {
            "reach_goal": reach_goal,
            "collision": collision,
            "goal_dist": goal_dist,
            "wp_dist": wp_dist,
            "path_error": path_error,
            "min_lidar": min_lidar,
            "steer_cmd": steer_cmd,
            "wheel_speed": wheel_speed,
            "lf_steer": lf,
            "rf_steer": rf,
            "lr_wheel": lr,
            "rr_wheel": rr,
            "path_len": len(self.path_world),
            "wp_index": self.wp_index,
        }

        return self._get_obs(), float(reward), terminated, truncated, info
