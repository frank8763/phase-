"""Vectorized B69 footprint checks; geometry, margins and search are unchanged."""
from pathlib import Path
import sys
import importlib.util
import numpy as np
source = Path(__file__).resolve().parent/'footprint_map_b69_v513.py'
spec = importlib.util.spec_from_file_location('b69_footprint_support', source)
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)
base, extract_self_envelope = old.base, old.extract_self_envelope


class FootprintMap(old.FootprintMap):
    def pose_values(self, poses):
        poses = np.asarray(poses, dtype=float).reshape(-1, 3)
        c, s = np.cos(poses[:, 2]), np.sin(poses[:, 2])
        centers = poses[:, :2]+np.stack((c*self.center_local[0]-s*self.center_local[1],
                                        s*self.center_local[0]+c*self.center_local[1]), axis=1)
        hx, hy = self.half
        ax, ay = np.abs(c), np.abs(s)
        ex, ey = ax*hx+ay*hy, ay*hx+ax*hy
        cfg = self.config
        result = np.minimum.reduce((centers[:, 0]-ex-cfg.lower,
            cfg.upper-centers[:, 0]-ex, centers[:, 1]-ey-cfg.lower,
            cfg.upper-centers[:, 1]-ey))
        if len(self.rectangles):
            delta = self.rectangles[None, :, :2]-centers[:, None, :]
            rx, ry = self.rectangles[:, 2], self.rectangles[:, 3]
            gap_x = np.abs(delta[:, :, 0])-rx[None, :]-ex[:, None]
            gap_y = np.abs(delta[:, :, 1])-ry[None, :]-ey[:, None]
            gap_lx = (np.abs(delta[:, :, 0]*c[:, None]+delta[:, :, 1]*s[:, None])
                -hx-rx[None, :]*ax[:, None]-ry[None, :]*ay[:, None])
            gap_ly = (np.abs(-delta[:, :, 0]*s[:, None]+delta[:, :, 1]*c[:, None])
                -hy-rx[None, :]*ay[:, None]-ry[None, :]*ax[:, None])
            separated = np.maximum.reduce((gap_x, gap_y, gap_lx, gap_ly))
            result = np.minimum(result, separated.min(axis=1))
        for points, extra in ((self.circles, 0.0), (self.sensor_points, self.sensor_extra)):
            if len(points) == 0:
                continue
            delta = points[None, :, :2]-centers[:, None, :]
            local = np.stack((delta[:, :, 0]*c[:, None]+delta[:, :, 1]*s[:, None],
                              -delta[:, :, 0]*s[:, None]+delta[:, :, 1]*c[:, None]), axis=2)
            residual = np.abs(local)-self.half
            distance = np.linalg.norm(np.maximum(residual, 0), axis=2)
            inside = residual.max(axis=2)
            signed = np.where(inside <= 0, inside, distance)
            radii = points[None, :, 2] if points.shape[1] == 3 else extra
            result = np.minimum(result, (signed-radii).min(axis=1))
        return result


def search(inputs):
    field = FootprintMap(inputs)
    path, stats = old.plan(field, inputs['start'], inputs['goal'], inputs['wheel_base'], inputs['max_steer'])
    return field, path, stats
