"""Pure input-only forward Hybrid-A* development baseline; no simulator access."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import heapq
import math
import time
import numpy as np


@dataclass(frozen=True)
class Config:
    lower: float = -5.0
    upper: float = 5.0
    resolution: float = 0.05
    search_resolution: float = 0.10
    heading_bins: int = 72
    primitive_length: float = 0.25
    sample_gap: float = 0.05
    margin: float = 0.05
    goal_tolerance: float = 0.20
    max_expansions: int = 30000
    max_seconds: float = 10.0


class ObservedMap:
    def __init__(self, rectangles, circles, sensor_points, robot_radius, sensor_radius,
                 config=Config()):
        self.config = config
        self.rectangles = np.asarray(rectangles, dtype=float).reshape(-1, 4)
        self.circles = np.asarray(circles, dtype=float).reshape(-1, 3)
        self.sensor_points = np.asarray(sensor_points, dtype=float).reshape(-1, 2)
        if not all(np.isfinite(a).all() for a in
                   (self.rectangles, self.circles, self.sensor_points)):
            raise ValueError('Nonfinite map input')
        self.robot_radius = float(robot_radius)
        self.sensor_radius = float(sensor_radius)
        n = round((config.upper-config.lower)/config.resolution)+1
        self.axis = config.lower+np.arange(n)*config.resolution
        xx, yy = np.meshgrid(self.axis, self.axis, indexing='ij')
        positions = np.stack((xx.ravel(), yy.ravel()), axis=1)
        self.clearance = self.exact_clearance(positions).reshape(n, n)
        # Nearest-cell distance field may overestimate distance by <= half diagonal.
        self.guard = config.margin+config.resolution/math.sqrt(2)
        self.free = self.clearance >= self.guard

    def exact_clearance(self, positions):
        p = np.asarray(positions, dtype=float).reshape(-1, 2)
        cfg = self.config
        result = np.minimum(p.min(axis=1)-cfg.lower, cfg.upper-p.max(axis=1))-self.robot_radius
        for cx, cy, hx, hy in self.rectangles:
            outside = np.maximum(np.abs(p-[cx, cy])-[hx, hy], 0)
            distance = np.linalg.norm(outside, axis=1)-self.robot_radius
            result = np.minimum(result, distance)
        for cx, cy, radius in self.circles:
            result = np.minimum(result, np.linalg.norm(p-[cx, cy], axis=1)
                                -radius-self.robot_radius)
        for point in self.sensor_points:
            result = np.minimum(result, np.linalg.norm(p-point, axis=1)-self.sensor_radius)
        return result

    def indices(self, positions):
        p = np.asarray(positions)
        return np.rint((p-self.config.lower)/self.config.resolution).astype(int)

    def values(self, positions):
        indices = self.indices(positions)
        valid = ((indices >= 0) & (indices < len(self.axis))).all(axis=1)
        result = np.full(len(indices), -np.inf)
        result[valid] = self.clearance[indices[valid, 0], indices[valid, 1]]
        return result


def _heuristic_grid(observed, goal):
    """Obstacle-aware 2D guide; no relocation of an occupied goal."""
    n = len(observed.axis)
    end = tuple(observed.indices([goal])[0])
    if not (0 <= end[0] < n and 0 <= end[1] < n and observed.free[end]):
        return None
    distances = np.full((n, n), np.inf)
    distances[end] = 0.0
    queue = [(0.0, end)]
    moves = [(dx, dy, math.hypot(dx, dy)*observed.config.resolution)
             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                            (1, 1), (-1, 1), (1, -1), (-1, -1))]
    while queue:
        cost, (x, y) = heapq.heappop(queue)
        if cost > distances[x, y]+1e-12:
            continue
        for dx, dy, length in moves:
            a, b = x+dx, y+dy
            if not (0 <= a < n and 0 <= b < n and observed.free[a, b]):
                continue
            if dx and dy and not (observed.free[x+dx, y] and observed.free[x, y+dy]):
                continue
            new = cost+length
            if new < distances[a, b]:
                distances[a, b] = new
                heapq.heappush(queue, (new, (a, b)))
    return distances


def plan(observed, start, goal, wheel_base, max_steer):
    cfg = observed.config
    begin = time.monotonic()
    start = np.asarray(start, dtype=float).reshape(3)
    goal = np.asarray(goal, dtype=float).reshape(2)
    stats = {'config': asdict(cfg), 'expanded': 0, 'status': 'unstarted',
             'initial_clearance_m': float(observed.exact_clearance([start[:2]])[0]),
             'min_turning_radius_m': float(wheel_base/math.tan(max_steer)),
             'model_scope': 'forward kinematics, disk envelope, no dynamic safety certificate'}

    def finish(path, status):
        stats['status'] = status
        stats['wall_seconds'] = time.monotonic()-begin
        if path is not None:
            stats['path_length_m'] = float(np.linalg.norm(np.diff(path[:, :2], axis=0), axis=1).sum())
            stats['min_exact_clearance_m'] = float(observed.exact_clearance(path[:, :2]).min())
            stats['goal_distance_m'] = float(np.linalg.norm(path[-1, :2]-goal))
        return path, stats

    if observed.values([start[:2]])[0] < observed.guard:
        return finish(None, 'start_occupied_no_teleport')
    heuristic = _heuristic_grid(observed, goal)
    if heuristic is None:
        return finish(None, 'goal_occupied_no_teleport')
    sx, sy = observed.indices([start[:2]])[0]
    if not math.isfinite(heuristic[sx, sy]):
        return finish(None, 'disconnected_observed_map')

    def key(pose):
        return (round((pose[0]-cfg.lower)/cfg.search_resolution),
                round((pose[1]-cfg.lower)/cfg.search_resolution),
                round((pose[2] % (2*math.pi))*cfg.heading_bins/(2*math.pi)) % cfg.heading_bins)

    steers = np.linspace(-max_steer, max_steer, 5)
    curvatures = np.tan(steers)/wheel_base
    samples = np.linspace(cfg.sample_gap, cfg.primitive_length,
                          round(cfg.primitive_length/cfg.sample_gap))
    root = key(start)
    nodes = [(start, None, None, 0.0)]
    best = {root: 0.0}
    serial = 0
    queue = [(float(heuristic[sx, sy]), serial, 0)]
    while queue:
        if stats['expanded'] >= cfg.max_expansions:
            return finish(None, 'expansion_budget')
        if time.monotonic()-begin > cfg.max_seconds:
            return finish(None, 'wall_budget')
        _, _, index = heapq.heappop(queue)
        pose, parent, segment, cost = nodes[index]
        if cost > best.get(key(pose), math.inf)+1e-10:
            continue
        stats['expanded'] += 1
        if np.linalg.norm(pose[:2]-goal) <= cfg.goal_tolerance:
            pieces = []
            while index:
                state, previous, piece, _ = nodes[index]
                pieces.append(piece)
                index = previous
            path = np.concatenate([start[None, :]]+pieces[::-1], axis=0)
            if observed.exact_clearance(path[:, :2]).min() < cfg.margin-1e-8:
                raise RuntimeError('Final continuous samples fail map margin')
            return finish(path, 'found')
        x, y, yaw = pose
        for steering, curvature in zip(steers, curvatures):
            angles = yaw+curvature*samples
            if abs(curvature) < 1e-12:
                xs, ys = x+samples*math.cos(yaw), y+samples*math.sin(yaw)
            else:
                xs = x+(np.sin(angles)-math.sin(yaw))/curvature
                ys = y-(np.cos(angles)-math.cos(yaw))/curvature
            piece = np.stack((xs, ys, angles), axis=1)
            clearance = observed.values(piece[:, :2])
            if np.min(clearance) < observed.guard:
                continue
            nxt = piece[-1]
            identifier = key(nxt)
            new = cost+cfg.primitive_length*(1+0.10*abs(steering/max_steer)
                    +0.10/(0.10+float(np.min(clearance))))
            if new >= best.get(identifier, math.inf)-1e-10:
                continue
            gx, gy = observed.indices([nxt[:2]])[0]
            estimate = heuristic[gx, gy]
            if not math.isfinite(estimate):
                continue
            best[identifier] = new
            nodes.append((nxt, index, piece, new))
            serial += 1
            heapq.heappush(queue, (new+1.15*estimate, serial, len(nodes)-1))
    return finish(None, 'search_exhausted')
