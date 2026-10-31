import math
import numpy as np

from training.phase6_clean.envs.sensor_utils import ray_cast_distance


def get_front_depth_camera_features(env, num_rays=9, fov_deg=90.0, max_range=3.5):
    yaw = float(env.robot_yaw)
    fov = math.radians(float(fov_deg))
    half = fov * 0.5

    rays = []

    for i in range(num_rays):
        if num_rays == 1:
            angle = yaw
        else:
            ratio = i / (num_rays - 1)
            angle = yaw - half + ratio * fov

        dist = ray_cast_distance(
            env,
            angle=angle,
            max_range=max_range,
            step=0.06,
        )
        rays.append(dist / max_range)

    return np.asarray(rays, dtype=np.float32)


def get_front_depth_summary(depth):
    depth = np.asarray(depth, dtype=np.float32).reshape(-1)

    n = len(depth)
    center = float(depth[n // 2])
    left = float(np.mean(depth[: max(1, n // 3)]))
    right = float(np.mean(depth[max(0, 2 * n // 3):]))
    min_depth = float(np.min(depth))
    mean_depth = float(np.mean(depth))

    return np.asarray(
        [
            min_depth,
            center,
            left,
            right,
            mean_depth,
        ],
        dtype=np.float32,
    )
