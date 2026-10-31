import math
import heapq
import numpy as np

from training.envs.mkmini_real_indoor_phase5_wheel_astar_sac_env import (
    MkMiniRealIndoorPhase5WheelAStarSACEnv,
)


class MkMiniRealIndoorPhase5WheelSafeAStarSACEnv(MkMiniRealIndoorPhase5WheelAStarSACEnv):
    """
    Phase5 Safe:
    真实车轮动力学 + A* 安全膨胀 + LiDAR 安全恢复层 + SAC

    正常：
        SAC 输出 steer + wheel_speed

    靠近障碍：
        安全层接管：
        1. BACKUP：先直线后退
        2. TURN_AWAY：距离拉开后，向空旷方向低速转向
        3. FORWARD_REJOIN：重新向前回到路径
    """

    def __init__(self):
        super().__init__()

        # 车身宽度安全距离
        # robot_radius 已经在父类 _is_free 中使用，这里额外增加安全边界
        self.astar_clearance = 0.18

        # LiDAR 安全阈值
        self.front_danger_dist = 0.45
        self.side_danger_dist = 0.28
        self.safe_front_dist = 0.68
        self.safe_side_dist = 0.48
        self.rear_stop_dist = 0.30

        # recovery 状态机
        self.recovery_stage = "NORMAL"
        self.recovery_timer = 0
        self.recovery_turn_dir = 1.0

        # recovery 动作
        self.backup_wheel_norm = -0.45
        self.turn_wheel_norm = 0.30
        self.rejoin_wheel_norm = 0.45

        self.backup_steps = 65
        self.turn_steps = 45
        self.rejoin_steps = 40

    # -------- A* 车身宽度安全膨胀 --------

    def _make_grid(self):
        grid = np.zeros((self.grid_n, self.grid_n), dtype=np.uint8)

        for gy in range(self.grid_n):
            for gx in range(self.grid_n):
                xy = self._grid_to_world((gy, gx))

                # 这里考虑车身宽度：障碍物额外膨胀 astar_clearance
                if not self._is_free(xy, margin=self.astar_clearance):
                    grid[gy, gx] = 1

        return grid

    @staticmethod
    def _astar_grid(grid, start, goal):
        h, w = grid.shape

        def heuristic(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        neighbors = [
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414),
        ]

        open_set = []
        heapq.heappush(open_set, (heuristic(start, goal), 0.0, start))

        came_from = {}
        g_score = {start: 0.0}
        visited = set()

        while open_set:
            _, cost, current = heapq.heappop(open_set)

            if current in visited:
                continue
            visited.add(current)

            if current == goal:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            cy, cx = current

            for dy, dx, step_cost in neighbors:
                ny = cy + dy
                nx = cx + dx

                if ny < 0 or ny >= h or nx < 0 or nx >= w:
                    continue
                if grid[ny, nx] == 1:
                    continue

                # 禁止对角线切墙角，防止车身擦障碍物
                if dy != 0 and dx != 0:
                    if grid[cy, nx] == 1 or grid[ny, cx] == 1:
                        continue

                nxt = (ny, nx)
                new_cost = cost + step_cost

                if nxt not in g_score or new_cost < g_score[nxt]:
                    g_score[nxt] = new_cost
                    priority = new_cost + heuristic(nxt, goal)
                    came_from[nxt] = current
                    heapq.heappush(open_set, (priority, new_cost, nxt))

        return []

    # -------- LiDAR 分区 --------

    def _sector_min(self, lidar, ids):
        n = len(lidar)
        return min(float(lidar[i % n]) for i in ids)

    def _lidar_clearance(self):
        lidar = self._simulate_lidar()
        n = len(lidar)

        front = self._sector_min(lidar, range(-4, 5))
        front_left = self._sector_min(lidar, range(4, n // 4 + 1))
        front_right = self._sector_min(lidar, range(3 * n // 4, n - 3))
        left = self._sector_min(lidar, range(n // 4 - 5, n // 4 + 6))
        right = self._sector_min(lidar, range(3 * n // 4 - 5, 3 * n // 4 + 6))
        rear = self._sector_min(lidar, range(n // 2 - 6, n // 2 + 7))

        return {
            "front": front,
            "front_left": front_left,
            "front_right": front_right,
            "left": left,
            "right": right,
            "rear": rear,
            "min": float(np.min(lidar)),
        }

    def _is_danger_close(self, c):
        # v3：中等安全层
        # 1. 前方/前侧危险：立即 recovery
        # 2. 侧边非常近：立即 recovery
        # 3. 侧边略近但前方安全：继续让 SAC 控制

        front_blocked = (
            c["front"] < self.front_danger_dist
            or c["front_left"] < self.front_danger_dist
            or c["front_right"] < self.front_danger_dist
        )

        side_critical = (
            c["left"] < self.side_danger_dist
            or c["right"] < self.side_danger_dist
        )

        # 非常近，强制安全接管
        emergency = c["min"] < 0.30

        return front_blocked or side_critical or emergency

    def _front_is_safe(self, c):
        return (
            c["front"] > self.safe_front_dist
            and c["front_left"] > self.safe_side_dist
            and c["front_right"] > self.safe_side_dist
        )

    def _start_recovery(self, c):
        left_space = min(c["front_left"], c["left"])
        right_space = min(c["front_right"], c["right"])

        # 哪边空间大，就往哪边转
        if right_space > left_space:
            self.recovery_turn_dir = -1.0
        else:
            self.recovery_turn_dir = 1.0

        self.recovery_stage = "BACKUP"
        self.recovery_timer = self.backup_steps

    def _recovery_action(self, c):
        """
        输出 SAC action 格式：
        action[0] = steer_norm
        action[1] = wheel_norm
        """

        # 1. 先后退，不急着转向
        if self.recovery_stage == "BACKUP":
            self.recovery_timer -= 1

            steer_norm = 0.0
            wheel_norm = self.backup_wheel_norm

            # 后方太近，停止继续倒车，进入转向阶段
            if c["rear"] < self.rear_stop_dist:
                self.recovery_stage = "TURN_AWAY"
                self.recovery_timer = self.turn_steps

            # 前方已经拉开距离，再开始转向
            if self.recovery_timer < self.backup_steps - 35 and self._front_is_safe(c):
                self.recovery_stage = "TURN_AWAY"
                self.recovery_timer = self.turn_steps

            if self.recovery_timer <= 0:
                self.recovery_stage = "TURN_AWAY"
                self.recovery_timer = self.turn_steps

            return np.array([steer_norm, wheel_norm], dtype=np.float32)

        # 2. 离障碍远一点后，向空旷方向低速转向
        if self.recovery_stage == "TURN_AWAY":
            self.recovery_timer -= 1

            steer_norm = 0.85 * self.recovery_turn_dir
            wheel_norm = self.turn_wheel_norm

            if self.recovery_timer <= 0:
                self.recovery_stage = "FORWARD_REJOIN"
                self.recovery_timer = self.rejoin_steps

            return np.array([steer_norm, wheel_norm], dtype=np.float32)

        # 3. 重新向前走，准备回到目标方向
        if self.recovery_stage == "FORWARD_REJOIN":
            self.recovery_timer -= 1

            steer_norm = 0.25 * self.recovery_turn_dir
            wheel_norm = self.rejoin_wheel_norm

            if self.recovery_timer <= 0:
                self.recovery_stage = "NORMAL"
                self.recovery_timer = 0

            return np.array([steer_norm, wheel_norm], dtype=np.float32)

        return None

    def reset(self, *args, **kwargs):
        obs, info = super().reset(*args, **kwargs)

        self.recovery_stage = "NORMAL"
        self.recovery_timer = 0
        self.recovery_turn_dir = 1.0

        return obs, info

    def step(self, action):
        self._update_pose_from_mujoco()
        c = self._lidar_clearance()

        recovery_active = False

        # 正常状态下，如果靠近障碍物，启动安全恢复
        if self.recovery_stage == "NORMAL":
            if self._is_danger_close(c):
                self._start_recovery(c)

        # recovery 状态下，安全层接管动作
        if self.recovery_stage != "NORMAL":
            safe_action = self._recovery_action(c)
            if safe_action is not None:
                action = safe_action
                recovery_active = True

        obs, reward, terminated, truncated, info = super().step(action)

        # recovery 阶段轻微惩罚，但不重罚，因为这是安全动作
        if recovery_active:
            reward -= 0.02

        # 离障碍物保持距离，鼓励更安全路线
        min_lidar = info.get("min_lidar", c["min"])
        if min_lidar < 0.70:
            reward -= 1.0 * (0.70 - min_lidar)

        info["recovery_active"] = recovery_active
        info["recovery_stage"] = self.recovery_stage
        info["recovery_turn_dir"] = self.recovery_turn_dir
        info["front_clearance"] = c["front"]
        info["left_clearance"] = c["left"]
        info["right_clearance"] = c["right"]
        info["rear_clearance"] = c["rear"]
        info["astar_clearance"] = self.astar_clearance

        return obs, float(reward), terminated, truncated, info
