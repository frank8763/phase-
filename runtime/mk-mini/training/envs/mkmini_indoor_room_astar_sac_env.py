import math
import heapq
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco


class MkMiniIndoorRoomAStarSACEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()

        self.dt = 0.08
        self.max_steps = 500

        self.map_min = -5.0
        self.map_max = 5.0
        self.map_size = self.map_max - self.map_min

        self.grid_res = 0.20
        self.grid_n = int(self.map_size / self.grid_res) + 1

        self.robot_radius = 0.25
        self.goal_threshold = 0.35

        self.lidar_num = 36
        self.lidar_range = 5.0

        # 圆形障碍：椅子、柱子、小障碍
        self.circle_obstacles = np.array([
            [-3.20,  3.35, 0.22],
            [-2.55,  3.35, 0.22],
            [-3.20,  2.55, 0.22],
            [-2.55,  2.55, 0.22],

            [ 2.55,  2.85, 0.22],
            [ 3.15,  2.85, 0.22],
            [ 2.55,  2.20, 0.22],
            [ 3.15,  2.20, 0.22],

            [-3.60, -2.90, 0.28],
            [ 0.90, -3.10, 0.25],
            [ 3.60, -0.80, 0.25],
        ], dtype=np.float32)

        # 矩形障碍：墙、门洞墙段、桌子、柜子、沙发
        # 格式：cx, cy, hx, hy
        self.rect_obstacles = np.array([
            # 内部竖墙，中央留门洞
            [ 0.00,  3.25, 0.08, 1.75],
            [ 0.00, -3.25, 0.08, 1.75],

            # 内部横墙，左右留通道
            [-3.15, 0.00, 1.85, 0.08],
            [ 3.15, 0.00, 1.85, 0.08],

            # 家具：桌子
            [-2.90,  2.95, 0.55, 0.35],
            [ 2.85,  2.50, 0.55, 0.35],

            # 家具：柜子 / 书柜 / 沙发
            [-4.15,  1.10, 0.30, 0.95],
            [ 4.05, -3.10, 0.35, 1.10],
            [-2.20, -3.80, 0.85, 0.28],
            [ 2.20, -1.85, 0.75, 0.30],
        ], dtype=np.float32)

        self.action_space = spaces.Box(
            low=np.array([0.0, -1.2], dtype=np.float32),
            high=np.array([0.6,  1.2], dtype=np.float32),
            dtype=np.float32,
        )

        # 36 lidar + goal_dist + goal_angle + wp_dist + wp_angle + last_v + last_w = 42
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(42,),
            dtype=np.float32,
        )

        self.model = mujoco.MjModel.from_xml_string(self._build_mujoco_xml())
        self.data = mujoco.MjData(self.model)

        self.robot_xy = np.zeros(2, dtype=np.float32)
        self.robot_yaw = 0.0
        self.goal_xy = np.zeros(2, dtype=np.float32)

        self.path_world = []
        self.wp_index = 0

        self.prev_goal_dist = 0.0
        self.prev_wp_dist = 0.0
        self.prev_action = np.zeros(2, dtype=np.float32)
        self.step_count = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.step_count = 0
        self.prev_action[:] = 0.0

        for _ in range(3000):
            start = self._sample_free_xy()
            goal = self._sample_free_xy()
            dist = np.linalg.norm(goal - start)

            if dist < 3.0 or dist > 7.0:
                continue

            path = self._plan_astar(start, goal)

            if len(path) < 8:
                continue

            self.robot_xy = start.astype(np.float32)
            self.goal_xy = goal.astype(np.float32)
            self.robot_yaw = float(self.np_random.uniform(-math.pi, math.pi))

            self.path_world = path
            self.wp_index = min(2, len(self.path_world) - 1)
            break
        else:
            self.robot_xy = np.array([-4.2, -4.2], dtype=np.float32)
            self.goal_xy = np.array([4.2, 4.2], dtype=np.float32)
            self.robot_yaw = 0.0
            self.path_world = self._plan_astar(self.robot_xy, self.goal_xy)
            self.wp_index = min(2, len(self.path_world) - 1)

        self.prev_goal_dist = self._goal_distance()
        self.prev_wp_dist = self._waypoint_distance()
        self._sync_mujoco()

        return self._get_obs(), {}

    def step(self, action):
        action = np.asarray(action, dtype=np.float32)
        v = float(np.clip(action[0], 0.0, 0.6))
        w = float(np.clip(action[1], -1.2, 1.2))

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
        wp_angle = self._waypoint_angle()

        collision = self._check_collision()
        reach_goal = goal_dist < self.goal_threshold
        timeout = self.step_count >= self.max_steps

        goal_progress = old_goal_dist - goal_dist
        wp_progress = old_wp_dist - wp_dist

        r_goal_progress = 15.0 * goal_progress
        r_wp_progress = 12.0 * wp_progress
        r_reach = 350.0 if reach_goal else 0.0
        r_collision = -300.0 if collision else 0.0
        r_time = -0.02

        r_heading = 0.10 * math.cos(abs(wp_angle))
        r_speed = 0.06 * v if abs(wp_angle) < 0.7 else -0.04 * v
        r_smooth = -0.01 * abs(w)
        r_action_change = -0.02 * float(np.linalg.norm(action - self.prev_action))

        r_near = 0.0
        if min_lidar < 0.45:
            r_near = -4.0 * (0.45 - min_lidar)

        reward = (
            r_goal_progress
            + r_wp_progress
            + r_reach
            + r_collision
            + r_time
            + r_heading
            + r_speed
            + r_smooth
            + r_action_change
            + r_near
        )

        self.prev_action = np.array([v, w], dtype=np.float32)
        self.prev_goal_dist = goal_dist
        self.prev_wp_dist = wp_dist

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
        }

        return self._get_obs(), float(reward), terminated, truncated, info

    def _get_obs(self):
        lidar = self._simulate_lidar() / self.lidar_range

        goal_dist = np.array([self._goal_distance() / 10.0], dtype=np.float32)
        goal_angle = np.array([self._goal_angle() / math.pi], dtype=np.float32)

        wp_dist = np.array([self._waypoint_distance() / 10.0], dtype=np.float32)
        wp_angle = np.array([self._waypoint_angle() / math.pi], dtype=np.float32)

        last_action = self.prev_action.astype(np.float32)

        obs = np.concatenate([
            lidar.astype(np.float32),
            goal_dist,
            goal_angle,
            wp_dist,
            wp_angle,
            last_action,
        ])

        return obs.astype(np.float32)

    def _goal_distance(self):
        return float(np.linalg.norm(self.goal_xy - self.robot_xy))

    def _goal_angle(self):
        dx = float(self.goal_xy[0] - self.robot_xy[0])
        dy = float(self.goal_xy[1] - self.robot_xy[1])
        target_yaw = math.atan2(dy, dx)
        return self._wrap_angle(target_yaw - self.robot_yaw)

    def _waypoint_xy(self):
        if len(self.path_world) == 0:
            return self.goal_xy
        idx = int(np.clip(self.wp_index, 0, len(self.path_world) - 1))
        return np.array(self.path_world[idx], dtype=np.float32)

    def _waypoint_distance(self):
        wp = self._waypoint_xy()
        return float(np.linalg.norm(wp - self.robot_xy))

    def _waypoint_angle(self):
        wp = self._waypoint_xy()
        dx = float(wp[0] - self.robot_xy[0])
        dy = float(wp[1] - self.robot_xy[1])
        target_yaw = math.atan2(dy, dx)
        return self._wrap_angle(target_yaw - self.robot_yaw)

    def _update_waypoint(self):
        if len(self.path_world) == 0:
            return

        while self.wp_index < len(self.path_world) - 1:
            wp = np.array(self.path_world[self.wp_index], dtype=np.float32)
            if np.linalg.norm(wp - self.robot_xy) < 0.45:
                self.wp_index += 1
            else:
                break

    def _sample_free_xy(self):
        for _ in range(2000):
            xy = self.np_random.uniform(self.map_min + 0.6, self.map_max - 0.6, size=2)
            if self._is_free(xy, margin=0.20):
                return xy.astype(np.float32)
        return np.array([0.0, 0.0], dtype=np.float32)

    def _is_free(self, xy, margin=0.0):
        x, y = float(xy[0]), float(xy[1])

        if x < self.map_min + self.robot_radius + margin:
            return False
        if x > self.map_max - self.robot_radius - margin:
            return False
        if y < self.map_min + self.robot_radius + margin:
            return False
        if y > self.map_max - self.robot_radius - margin:
            return False

        for ox, oy, r in self.circle_obstacles:
            if math.hypot(x - ox, y - oy) < float(r) + self.robot_radius + margin:
                return False

        for cx, cy, hx, hy in self.rect_obstacles:
            if self._rect_collision(x, y, cx, cy, hx, hy, self.robot_radius + margin):
                return False

        return True

    def _check_collision(self):
        return not self._is_free(self.robot_xy, margin=0.0)

    @staticmethod
    def _rect_collision(x, y, cx, cy, hx, hy, radius):
        dx = max(abs(x - float(cx)) - float(hx), 0.0)
        dy = max(abs(y - float(cy)) - float(hy), 0.0)

        inside = abs(x - float(cx)) <= float(hx) and abs(y - float(cy)) <= float(hy)
        if inside:
            return True

        return math.hypot(dx, dy) < radius

    def _point_hits_obstacle(self, x, y):
        if x <= self.map_min or x >= self.map_max or y <= self.map_min or y >= self.map_max:
            return True

        for ox, oy, r in self.circle_obstacles:
            if math.hypot(x - ox, y - oy) <= float(r):
                return True

        for cx, cy, hx, hy in self.rect_obstacles:
            if abs(x - float(cx)) <= float(hx) and abs(y - float(cy)) <= float(hy):
                return True

        return False

    def _simulate_lidar(self):
        lidar = np.full(self.lidar_num, self.lidar_range, dtype=np.float32)

        for i in range(self.lidar_num):
            angle = self.robot_yaw + 2.0 * math.pi * i / self.lidar_num

            for j in range(1, 121):
                d = self.lidar_range * j / 120.0
                x = float(self.robot_xy[0]) + d * math.cos(angle)
                y = float(self.robot_xy[1]) + d * math.sin(angle)

                if self._point_hits_obstacle(x, y):
                    lidar[i] = d
                    break

        return lidar

    def _make_grid(self):
        grid = np.zeros((self.grid_n, self.grid_n), dtype=np.uint8)

        for gy in range(self.grid_n):
            for gx in range(self.grid_n):
                xy = self._grid_to_world((gy, gx))
                if not self._is_free(xy, margin=0.05):
                    grid[gy, gx] = 1

        return grid

    def _world_to_grid(self, xy):
        gx = int(round((float(xy[0]) - self.map_min) / self.grid_res))
        gy = int(round((float(xy[1]) - self.map_min) / self.grid_res))
        gx = int(np.clip(gx, 0, self.grid_n - 1))
        gy = int(np.clip(gy, 0, self.grid_n - 1))
        return gy, gx

    def _grid_to_world(self, cell):
        gy, gx = cell
        x = self.map_min + gx * self.grid_res
        y = self.map_min + gy * self.grid_res
        return np.array([x, y], dtype=np.float32)

    def _plan_astar(self, start_xy, goal_xy):
        grid = self._make_grid()
        start = self._world_to_grid(start_xy)
        goal = self._world_to_grid(goal_xy)

        if grid[start] == 1 or grid[goal] == 1:
            return []

        path_cells = self._astar_grid(grid, start, goal)

        if len(path_cells) == 0:
            return []

        path_world = [self._grid_to_world(c) for c in path_cells]
        return path_world

    @staticmethod
    def _astar_grid(grid, start, goal):
        h, w = grid.shape

        def heuristic(a, b):
            return math.hypot(a[0] - b[0], a[1] - b[1])

        neighbors = [
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)
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

            for dy, dx, step_cost in neighbors:
                ny = current[0] + dy
                nx = current[1] + dx

                if ny < 0 or ny >= h or nx < 0 or nx >= w:
                    continue
                if grid[ny, nx] == 1:
                    continue

                nxt = (ny, nx)
                new_cost = cost + step_cost

                if nxt not in g_score or new_cost < g_score[nxt]:
                    g_score[nxt] = new_cost
                    priority = new_cost + heuristic(nxt, goal)
                    came_from[nxt] = current
                    heapq.heappush(open_set, (priority, new_cost, nxt))

        return []

    def _sync_mujoco(self):
        self.data.qpos[0] = float(self.robot_xy[0])
        self.data.qpos[1] = float(self.robot_xy[1])
        self.data.qpos[2] = 0.15

        cy = math.cos(self.robot_yaw * 0.5)
        sy = math.sin(self.robot_yaw * 0.5)

        self.data.qpos[3] = cy
        self.data.qpos[4] = 0.0
        self.data.qpos[5] = 0.0
        self.data.qpos[6] = sy

        mujoco.mj_forward(self.model, self.data)

    @staticmethod
    def _wrap_angle(a):
        return (a + math.pi) % (2.0 * math.pi) - math.pi

    def _build_mujoco_xml(self):
        circle_xml = ""
        for i, (x, y, r) in enumerate(self.circle_obstacles):
            circle_xml += f'''
            <geom name="circle_obs_{i}" type="cylinder"
                  pos="{x} {y} 0.25"
                  size="{r} 0.25"
                  rgba="0.75 0.05 0.05 1"/>
            '''

        rect_xml = ""
        for i, (cx, cy, hx, hy) in enumerate(self.rect_obstacles):
            rect_xml += f'''
            <geom name="rect_obs_{i}" type="box"
                  pos="{cx} {cy} 0.25"
                  size="{hx} {hy} 0.25"
                  rgba="0.35 0.25 0.15 1"/>
            '''

        xml = f'''
<mujoco model="mkmini_indoor_room_astar_sac">
    <option timestep="0.02" gravity="0 0 0"/>

    <visual>
        <quality shadowsize="2048"/>
    </visual>

    <worldbody>
        <light pos="0 0 8" dir="0 0 -1" diffuse="1 1 1"/>

        <geom name="floor" type="plane" pos="0 0 0"
              size="6 6 0.1"
              rgba="0.65 0.65 0.65 1"/>

        <geom name="wall_n" type="box" pos="0 5.1 0.3"
              size="5.2 0.1 0.3"
              rgba="0.05 0.05 0.05 1"/>
        <geom name="wall_s" type="box" pos="0 -5.1 0.3"
              size="5.2 0.1 0.3"
              rgba="0.05 0.05 0.05 1"/>
        <geom name="wall_e" type="box" pos="5.1 0 0.3"
              size="0.1 5.2 0.3"
              rgba="0.05 0.05 0.05 1"/>
        <geom name="wall_w" type="box" pos="-5.1 0 0.3"
              size="0.1 5.2 0.3"
              rgba="0.05 0.05 0.05 1"/>

        {rect_xml}
        {circle_xml}

        <body name="robot" pos="0 0 0.15">
            <freejoint name="root"/>
            <geom name="robot_body" type="box"
                  size="0.22 0.16 0.12"
                  rgba="0.05 0.15 0.9 1"/>
            <geom name="robot_front" type="sphere"
                  pos="0.18 0 0"
                  size="0.045"
                  rgba="0 1 0 1"/>
        </body>
    </worldbody>
</mujoco>
'''
        return xml

    def close(self):
        pass
