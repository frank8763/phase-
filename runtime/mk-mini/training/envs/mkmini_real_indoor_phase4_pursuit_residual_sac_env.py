import math
import numpy as np
from gymnasium import spaces

from training.envs.mkmini_real_indoor_phase3_depth_astar_sac_env import (
    MkMiniRealIndoorPhase3DepthAStarSACEnv,
)


class MkMiniRealIndoorPhase4PursuitResidualSACEnv(MkMiniRealIndoorPhase3DepthAStarSACEnv):
    """
    phase4:
    A* + Pure Pursuit + SAC residual

    SAC 不再直接输出完整 [v, w]
    SAC 输出 residual: [dv, dw]

    最终控制:
    v = v_base + dv
    w = w_base + dw
    """

    def __init__(self):
        super().__init__()

        self.goal_threshold = 0.70

        # A* 额外安全膨胀距离，防止蓝色路径贴障碍物
        self.astar_clearance = 0.25

        # residual 动作空间，注意不是完整速度
        self.max_dv = 0.15
        self.max_dw = 0.45

        self.action_space = spaces.Box(
            low=np.array([-self.max_dv, -self.max_dw], dtype=np.float32),
            high=np.array([ self.max_dv,  self.max_dw], dtype=np.float32),
            dtype=np.float32,
        )

        # Pure Pursuit 参数
        self.lookahead_dist = 0.40
        self.base_v_max = 0.28
        self.base_v_min = 0.12
        self.base_w_max = 0.90

        # 最终动作限制
        self.final_v_max = 0.35
        self.final_w_max = 1.10

    def _wrap_angle(self, a):
        return (a + math.pi) % (2.0 * math.pi) - math.pi

    def _get_robot_pose(self):
        x = float(self.robot_xy[0])
        y = float(self.robot_xy[1])
        yaw = float(self.robot_yaw)
        return x, y, yaw

    def _make_grid(self):
        """
        phase4 安全 A*：
        在原有 robot_radius 基础上增加 astar_clearance，
        让蓝色路径远离墙、桌子、柜子等障碍物。
        """
        grid = np.zeros((self.grid_n, self.grid_n), dtype=np.uint8)

        margin = float(getattr(self, "astar_clearance", 0.25))

        for gy in range(self.grid_n):
            for gx in range(self.grid_n):
                xy = self._grid_to_world((gy, gx))

                # _is_free 内部已经包含 robot_radius，这里额外增加安全距离
                if not self._is_free(xy, margin=margin):
                    grid[gy, gx] = 1

        return grid

    @staticmethod
    def _astar_grid(grid, start, goal):
        """
        phase4 安全 A*：
        允许 8 邻域，但禁止对角线穿过障碍物墙角。
        """
        import heapq
        import math

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

                # 禁止斜向切墙角
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

    def _select_lookahead_point(self):
        if not hasattr(self, "path_world") or len(self.path_world) == 0:
            return self.goal_xy.copy()

        pos = np.array(self.robot_xy, dtype=np.float32)

        start_i = int(getattr(self, "wp_index", 0))
        start_i = max(0, min(start_i, len(self.path_world) - 1))

        for i in range(start_i, len(self.path_world)):
            p = np.array(self.path_world[i], dtype=np.float32)
            if np.linalg.norm(p - pos) >= self.lookahead_dist:
                return p

        return np.array(self.goal_xy, dtype=np.float32)

    def _pure_pursuit_action(self):
        x, y, yaw = self._get_robot_pose()
        target = self._select_lookahead_point()

        dx = float(target[0] - x)
        dy = float(target[1] - y)

        target_angle = math.atan2(dy, dx)
        alpha = self._wrap_angle(target_angle - yaw)

        goal_dist = float(np.linalg.norm(np.array(self.goal_xy) - np.array(self.robot_xy)))

        # 离目标近时自动降速
        v_base = self.base_v_max
        if goal_dist < 1.5:
            v_base = max(self.base_v_min, 0.25 * goal_dist)

        # 转角大时降速
        if abs(alpha) > 1.0:
            v_base *= 0.45
        elif abs(alpha) > 0.6:
            v_base *= 0.65

        # Pure Pursuit 角速度
        w_base = 1.6 * alpha
        w_base = float(np.clip(w_base, -self.base_w_max, self.base_w_max))

        v_base = float(np.clip(v_base, 0.0, self.base_v_max))

        return v_base, w_base, alpha, goal_dist

    def step(self, residual_action):
        residual_action = np.asarray(residual_action, dtype=np.float32)

        dv = float(np.clip(residual_action[0], -self.max_dv, self.max_dv))
        dw = float(np.clip(residual_action[1], -self.max_dw, self.max_dw))

        v_base, w_base, alpha, goal_dist_before = self._pure_pursuit_action()

        v = float(np.clip(v_base + dv, 0.0, self.final_v_max))
        w = float(np.clip(w_base + dw, -self.final_w_max, self.final_w_max))

        full_action = np.array([v, w], dtype=np.float32)

        obs, reward, terminated, truncated, info = super().step(full_action)

        goal_dist = float(info.get("goal_dist", 999.0))
        collision = bool(info.get("collision", False))
        reach_goal = bool(info.get("reach_goal", False))

        # 奖励修正：鼓励沿 Pure Pursuit 方向走
        reward += 0.10 * math.cos(alpha)

        # 鼓励接近目标
        if not collision:
            reward += 2.0 * max(0.0, 2.0 - goal_dist)

        # 成功奖励增强
        if reach_goal:
            reward += 100.0

        # 靠近目标但超时时，少罚一些
        if truncated and (not reach_goal) and goal_dist < 1.0:
            reward += 100.0

        # residual 不要太大，避免 SAC 破坏基础跟踪器
        reward -= 0.02 * float(np.linalg.norm(residual_action))

        info["v_base"] = v_base
        info["w_base"] = w_base
        info["dv"] = dv
        info["dw"] = dw
        info["v_final"] = v
        info["w_final"] = w
        info["pure_pursuit_alpha"] = alpha

        return obs, float(reward), terminated, truncated, info
