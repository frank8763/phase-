import math
import numpy as np


def wrap_angle(a):
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def point_in_obstacle(env, p):
    x = float(p[0])
    y = float(p[1])

    if x < float(env.map_min) or x > float(env.map_max):
        return True
    if y < float(env.map_min) or y > float(env.map_max):
        return True

    if hasattr(env, "rect_obstacles"):
        rects = np.asarray(env.rect_obstacles, dtype=np.float32).reshape(-1, 4)
        for cx, cy, hx, hy in rects:
            if abs(x - float(cx)) <= float(hx) and abs(y - float(cy)) <= float(hy):
                return True

    if hasattr(env, "circle_obstacles"):
        circles = np.asarray(env.circle_obstacles, dtype=np.float32).reshape(-1, 3)
        for ox, oy, r in circles:
            if (x - float(ox)) ** 2 + (y - float(oy)) ** 2 <= float(r) ** 2:
                return True

    return False


def ray_cast_distance(env, angle, max_range=3.0, step=0.08):
    origin = np.asarray(env.robot_xy, dtype=np.float32)
    direction = np.asarray([math.cos(angle), math.sin(angle)], dtype=np.float32)

    d = 0.0
    while d <= max_range:
        p = origin + d * direction
        if point_in_obstacle(env, p):
            return float(d)
        d += step

    return float(max_range)


def get_lidar_features(env, num_rays=16, max_range=3.0):
    """
    LiDAR 主导避障：
    360° 距离射线，输出归一化距离 [0,1]。
    """
    yaw = float(env.robot_yaw)
    rays = []

    for i in range(num_rays):
        angle = yaw + 2.0 * math.pi * i / num_rays
        dist = ray_cast_distance(env, angle, max_range=max_range)
        rays.append(dist / max_range)

    return np.asarray(rays, dtype=np.float32)


def get_camera_goal_features(env, fov_deg=90.0, max_range=6.0):
    """
    camera 辅助找目标：
    不负责主要避障，只判断目标是否在前方视野内、目标方向偏差。
    """
    robot_xy = np.asarray(env.robot_xy, dtype=np.float32)
    goal_xy = np.asarray(env.goal_xy, dtype=np.float32)

    rel = goal_xy - robot_xy
    dist = float(np.linalg.norm(rel))

    goal_angle = math.atan2(float(rel[1]), float(rel[0]))
    yaw = float(env.robot_yaw)
    heading_err = wrap_angle(goal_angle - yaw)

    half_fov = math.radians(fov_deg) * 0.5
    visible = 1.0 if abs(heading_err) <= half_fov and dist <= max_range else 0.0

    # 越接近正前方，score 越大
    align_score = max(0.0, 1.0 - abs(heading_err) / half_fov)

    return np.asarray([
        dist / max_range,
        math.sin(heading_err),
        math.cos(heading_err),
        visible,
        align_score,
    ], dtype=np.float32)
