import math
import numpy as np

from training.envs.mkmini_real_indoor_phase4_pursuit_residual_sac_env import (
    MkMiniRealIndoorPhase4PursuitResidualSACEnv,
)


class MkMiniRealIndoorPhase4RecoverySACEnv(MkMiniRealIndoorPhase4PursuitResidualSACEnv):
    """
    phase4 + LiDAR recovery

    正常:
        A* + Pure Pursuit + SAC residual

    卡住/贴墙:
        根据 LiDAR 判断障碍物在哪边
        然后倒车并向远离障碍物的一侧转弯
    """

    def __init__(self):
        super().__init__()

        self.recovery_enabled = True

        self.recovery_steps = 45
        self.recovery_v = -0.10
        self.recovery_w = 0.65

        self.recovery_steps_left = 0
        self.recovery_turn_dir = 1.0
        self.recovery_cooldown = 0

        self.stuck_counter = 0
        self.stuck_trigger_steps = 18
        self.min_progress = 0.002
        self.min_move = 0.012

        self.prev_xy_for_stuck = None
        self.prev_goal_dist_for_stuck = None

        # LiDAR 安全阈值
        self.front_danger_dist = 0.55
        self.side_danger_dist = 0.60
        self.rear_danger_dist = 0.35

    def reset(self, *args, **kwargs):
        obs, info = super().reset(*args, **kwargs)

        self.recovery_steps_left = 0
        self.recovery_turn_dir = 1.0
        self.recovery_cooldown = 0
        self.stuck_counter = 0

        self.prev_xy_for_stuck = np.array(self.robot_xy, dtype=np.float32)
        self.prev_goal_dist_for_stuck = float(self._goal_distance())

        return obs, info

    def _sector_min(self, lidar, indices):
        n = len(lidar)
        vals = [float(lidar[i % n]) for i in indices]
        return min(vals)

    def _lidar_clearance_info(self):
        """
        LiDAR 编号假设:
            0              正前方
            n/4            左侧
            n/2            后方
            3n/4 或 -n/4   右侧
        """
        lidar = self._simulate_lidar()
        n = len(lidar)

        front_ids = list(range(-3, 4))
        front_left_ids = list(range(2, 10))
        front_right_ids = list(range(n - 9, n - 1))

        left_ids = list(range(n // 4 - 4, n // 4 + 5))
        right_ids = list(range(3 * n // 4 - 4, 3 * n // 4 + 5))

        rear_ids = list(range(n // 2 - 4, n // 2 + 5))
        rear_left_ids = list(range(n // 2 + 2, n // 2 + 9))
        rear_right_ids = list(range(n // 2 - 8, n // 2 - 1))

        info = {
            "front": self._sector_min(lidar, front_ids),
            "front_left": self._sector_min(lidar, front_left_ids),
            "front_right": self._sector_min(lidar, front_right_ids),
            "left": self._sector_min(lidar, left_ids),
            "right": self._sector_min(lidar, right_ids),
            "rear": self._sector_min(lidar, rear_ids),
            "rear_left": self._sector_min(lidar, rear_left_ids),
            "rear_right": self._sector_min(lidar, rear_right_ids),
            "min_lidar": float(np.min(lidar)),
        }
        return info

    def _choose_recovery_action_from_lidar(self):
        c = self._lidar_clearance_info()

        # 比较前左/左侧 和 前右/右侧空间
        left_clear = min(c["front_left"], c["left"])
        right_clear = min(c["front_right"], c["right"])

        # 哪边空间大，就往哪边转
        if right_clear > left_clear:
            turn_dir = -1.0   # 右侧更空，向右转
        else:
            turn_dir = 1.0    # 左侧更空，向左转

        # 如果后方太近，不能继续倒车，改成小幅前进转向脱困
        rear_clear = min(c["rear"], c["rear_left"], c["rear_right"])

        if rear_clear < self.rear_danger_dist:
            v = 0.08
            w = turn_dir * self.recovery_w
            mode = "forward_escape"
        else:
            v = self.recovery_v
            w = turn_dir * self.recovery_w
            mode = "backward_escape"

        self.recovery_turn_dir = turn_dir

        return float(v), float(w), mode, c

    def _update_stuck_detector(self, info, w_base, alpha):
        if not self.recovery_enabled:
            return

        if self.recovery_cooldown > 0:
            self.recovery_cooldown -= 1
            return

        xy = np.array(self.robot_xy, dtype=np.float32)
        goal_dist = float(info.get("goal_dist", 999.0))
        min_lidar = float(info.get("min_lidar", 5.0))

        if self.prev_xy_for_stuck is None:
            self.prev_xy_for_stuck = xy.copy()
            self.prev_goal_dist_for_stuck = goal_dist
            return

        move = float(np.linalg.norm(xy - self.prev_xy_for_stuck))
        progress = float(self.prev_goal_dist_for_stuck - goal_dist)

        turning = abs(w_base) > 0.25 or abs(alpha) > 0.45
        far_from_goal = goal_dist > 0.85
        near_obstacle = min_lidar < self.side_danger_dist

        stuck_like = far_from_goal and turning and near_obstacle and (
            move < self.min_move or progress < self.min_progress
        )

        if stuck_like:
            self.stuck_counter += 1
        else:
            self.stuck_counter = max(0, self.stuck_counter - 2)

        self.prev_xy_for_stuck = xy.copy()
        self.prev_goal_dist_for_stuck = goal_dist

        if self.stuck_counter >= self.stuck_trigger_steps:
            self.recovery_steps_left = self.recovery_steps
            self.stuck_counter = 0
            self.recovery_cooldown = 35

    def _raw_step_allow_reverse(self, v, w, recovery_mode):
        """
        直接执行 [v,w]，允许 v < 0。
        不走父类 step，避免负速度被裁剪成 0。
        """
        v = float(np.clip(v, -0.16, 0.16))
        w = float(np.clip(w, -0.9, 0.9))

        old_goal_dist = self._goal_distance()
        old_wp_dist = self._waypoint_distance()

        self.robot_yaw = self._wrap_angle(self.robot_yaw + w * self.dt)
        self.robot_xy[0] += v * math.cos(self.robot_yaw) * self.dt
        self.robot_xy[1] += v * math.sin(self.robot_yaw) * self.dt

        self.step_count += 1
        self._update_waypoint()
        self._sync_mujoco()

        lidar = self._simulate_lidar()
        min_lidar = float(np.min(lidar))

        goal_dist = self._goal_distance()
        wp_dist = self._waypoint_distance()

        collision = self._check_collision()
        reach_goal = goal_dist < self.goal_threshold
        timeout = self.step_count >= self.max_steps

        goal_progress = old_goal_dist - goal_dist
        wp_progress = old_wp_dist - wp_dist

        reward = (
            8.0 * goal_progress
            + 4.0 * wp_progress
            - 0.10
            - 0.20 * abs(w)
        )

        if reach_goal:
            reward += 350.0
        if collision:
            reward -= 400.0
        if min_lidar < 0.35:
            reward -= 5.0 * (0.35 - min_lidar)

        self.prev_action = np.array([v, w], dtype=np.float32)

        terminated = bool(reach_goal or collision)
        truncated = bool(timeout and not terminated)

        info = {
            "reach_goal": reach_goal,
            "collision": collision,
            "goal_dist": goal_dist,
            "wp_dist": wp_dist,
            "min_lidar": min_lidar,
            "path_len": len(self.path_world),
            "wp_index": self.wp_index,
            "recovery": True,
            "recovery_mode": recovery_mode,
            "v_final": v,
            "w_final": w,
        }

        return self._get_obs(), float(reward), terminated, truncated, info

    def step(self, residual_action):
        # recovery 阶段：每一步都重新看 LiDAR，动态选择远离障碍物方向
        if self.recovery_steps_left > 0:
            self.recovery_steps_left -= 1

            v, w, mode, c = self._choose_recovery_action_from_lidar()

            obs, reward, terminated, truncated, info = self._raw_step_allow_reverse(
                v=v,
                w=w,
                recovery_mode=mode,
            )

            info.update({
                "front_clear": c["front"],
                "left_clear": c["left"],
                "right_clear": c["right"],
                "rear_clear": c["rear"],
            })

            return obs, reward, terminated, truncated, info

        # 正常 phase4 控制
        v_base, w_base, alpha, goal_dist_before = self._pure_pursuit_action()

        obs, reward, terminated, truncated, info = super().step(residual_action)

        info["recovery"] = False

        self._update_stuck_detector(
            info=info,
            w_base=w_base,
            alpha=alpha,
        )

        return obs, reward, terminated, truncated, info
