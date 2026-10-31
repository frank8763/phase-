"""Input-only SE(2) rectangular-envelope map for the B69 development test."""
from __future__ import annotations
import sys
from pathlib import Path
import math
import heapq
import time
from dataclasses import asdict
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'phase_rpccr_p0b68_v1'))
import hybrid_planner as base


class FootprintMap(base.ObservedMap):
    def __init__(self, inputs):
        self.bounds = np.asarray(inputs['footprint_bounds'], dtype=float)
        self.center_local = (self.bounds[:2]+self.bounds[2:])/2
        self.half = (self.bounds[2:]-self.bounds[:2])/2
        self.sensor_extra = max(0.0, inputs['sensor_radius']-inputs['robot_radius'])
        # Relaxation for the center guide: largest centered disk contained in envelope.
        inner = float(min(-self.bounds[0], -self.bounds[1], self.bounds[2], self.bounds[3]))
        if inner <= 0:
            raise ValueError('Self envelope does not contain robot origin')
        super().__init__(inputs['rectangles'], inputs['circles'], inputs['sensor_points'],
                         inner, inner+self.sensor_extra)
        self.guard = self.config.margin
        self.free = self.clearance >= 0.0

    def pose_values(self, poses):
        poses = np.asarray(poses, dtype=float).reshape(-1, 3)
        c, s = np.cos(poses[:, 2]), np.sin(poses[:, 2])
        centers = poses[:, :2]+np.stack((c*self.center_local[0]-s*self.center_local[1],
                                        s*self.center_local[0]+c*self.center_local[1]), axis=1)
        hx, hy = self.half
        ax, ay = np.abs(c), np.abs(s)
        ex, ey = ax*hx+ay*hy, ay*hx+ax*hy
        cfg = self.config
        result = np.minimum.reduce([centers[:, 0]-ex-cfg.lower,
            cfg.upper-centers[:, 0]-ex, centers[:, 1]-ey-cfg.lower,
            cfg.upper-centers[:, 1]-ey])
        for ox, oy, rx, ry in self.rectangles:
            delta = np.array([ox, oy])-centers
            gaps = np.stack((np.abs(delta[:, 0])-rx-ex,
                np.abs(delta[:, 1])-ry-ey,
                np.abs(delta[:, 0]*c+delta[:, 1]*s)-hx-rx*ax-ry*ay,
                np.abs(-delta[:, 0]*s+delta[:, 1]*c)-hy-rx*ay-ry*ax), axis=1)
            result = np.minimum(result, gaps.max(axis=1))
        for source, extra in ((self.circles, 0.0), (self.sensor_points, self.sensor_extra)):
            for point in source:
                delta = point[:2]-centers
                local = np.stack((delta[:, 0]*c+delta[:, 1]*s,
                                  -delta[:, 0]*s+delta[:, 1]*c), axis=1)
                outside = np.maximum(np.abs(local)-self.half, 0)
                distance = np.linalg.norm(outside, axis=1)
                inside = (np.abs(local)-self.half).max(axis=1)
                signed = np.where(inside <= 0, inside, distance)
                radius = float(point[2]) if len(point) == 3 else extra
                result = np.minimum(result, signed-radius)
        return result


def extract_self_envelope(env, mj):
    """Only robot descendants are read; no world/obstacle pose or size access."""
    model, data = env.model, env.data
    root = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, 'mkmini_base')
    if root < 0:
        raise RuntimeError('Robot base absent')
    descendants = set()
    for bid in range(1, model.nbody):
        parent = bid
        while parent and parent != root:
            parent = int(model.body_parentid[parent])
        if parent == root:
            descendants.add(bid)
    q = data.qpos
    yaw = math.atan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
    c, s = math.cos(yaw), math.sin(yaw)
    inv = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    origin = np.asarray(data.xpos[root])
    entries = []
    for gid in range(model.ngeom):
        if int(model.geom_bodyid[gid]) not in descendants:
            continue
        if int(model.geom_contype[gid]) == 0 and int(model.geom_conaffinity[gid]) == 0:
            continue
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, gid) or f'unnamed_geom_{gid}'
        kind = int(model.geom_type[gid])
        size = np.asarray(model.geom_size[gid], dtype=float)
        rotation = inv@np.asarray(data.geom_xmat[gid]).reshape(3, 3)
        center = inv@(np.asarray(data.geom_xpos[gid])-origin)
        if kind == int(mj.mjtGeom.mjGEOM_BOX):
            extents = np.abs(rotation)@size
        elif kind == int(mj.mjtGeom.mjGEOM_SPHERE):
            extents = np.full(3, size[0])
        elif kind == int(mj.mjtGeom.mjGEOM_CAPSULE):
            extents = size[0]+size[1]*np.abs(rotation[:, 2])
        elif kind == int(mj.mjtGeom.mjGEOM_CYLINDER):
            # Rotation invariant circumsphere also covers the spinning/steering wheels.
            extents = np.full(3, math.hypot(size[0], size[1]))
        else:
            raise RuntimeError(f'Unaccounted active self geom {name}: {kind}')
        entries.append({'geom_id': gid, 'name': name, 'type': kind,
            'body_id': int(model.geom_bodyid[gid]), 'size': size.tolist(),
            'lower_xy': (center-extents)[:2].tolist(), 'upper_xy': (center+extents)[:2].tolist()})
    low = np.min([e['lower_xy'] for e in entries], axis=0)
    high = np.max([e['upper_xy'] for e in entries], axis=0)
    joints = []
    for jid in range(model.njnt):
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_JOINT, jid) or ''
        if 'steer' in name:
            joints.append({'name': name, 'range_rad': model.jnt_range[jid].tolist(),
                           'limited': bool(model.jnt_limited[jid])})
    return {'bounds_xy': np.r_[low, high].tolist(), 'active_robot_geoms': entries,
            'steering_joints': joints, 'max_steer_command_rad': float(env.inner.max_steer),
            'max_wheel_delta_per_public_step': float(env.inner.max_wheel_delta),
            'scope': 'current articulated configuration; cylinders rotation-enclosed; no obstacle truth'}


def search(inputs):
    field = FootprintMap(inputs)
    path, stats = plan(field, inputs['start'], inputs['goal'], inputs['wheel_base'], inputs['max_steer'])
    return field, path, stats


# Search loop adapted from the frozen B68 planner; only collision geometry differs.
def plan(observed, start, goal, wheel_base, max_steer):
    cfg = observed.config
    print('V619_ACTIVE_PLANNER', {
        'source': str(Path(__file__).resolve()),
        'guard_m': float(observed.guard),
        'config_margin_m': float(cfg.margin)
    }, flush=True)
    begin = time.monotonic()
    print('V513_B69_ACTIVE', 'base_budget_s=', float(observed.config.max_seconds), 'budget_multiplier=', 8, 'steering_samples=', 5, flush=True)
    start = np.asarray(start, dtype=float).reshape(3)
    goal = np.asarray(goal, dtype=float).reshape(2)
    start_clearance = float(observed.pose_values([start])[0])
    target_clearance = 0.30  # V577: align with outer full-footprint clearance gate
    # V609R: hard guard is the feasibility boundary.
    # Target clearance is not a mandatory rejection floor.
    clearance_floor = float(observed.guard)
    print('V619_SEARCH_POLICY', {
        'hard_floor_m': float(clearance_floor),
        'soft_target_m': 0.30,
        'policy': 'HARD_015_SOFT_030'
    }, flush=True)
    print('V572R3_CLEARANCE_FLOOR_POLICY', {
        'start_clearance_m': float(start_clearance),
        'target_clearance_m': float(target_clearance),
        'guard_m': float(observed.guard),
        'effective_floor_m': float(clearance_floor),
        'policy': 'V609R_HARD_GUARD_ONLY_FEASIBILITY',
    }, flush=True)
    stats = {'config': asdict(cfg), 'expanded': 0, 'status': 'unstarted',
             'initial_clearance_m': float(observed.pose_values([start])[0]),
             'min_turning_radius_m': float(wheel_base/math.tan(max_steer)),
             'model_scope': 'forward kinematics, current robot rectangle envelope, no dynamic safety certificate'}
    stats['v572_candidate_min_clearances'] = []
    stats['v612_candidate_eval_calls'] = 0
    stats['v612_clearance_eval_wall_s'] = 0.0
    stats['v612_heuristic_wall_s'] = 0.0

    def finish(path, status):
        stats['status'] = status
        stats['wall_seconds'] = time.monotonic()-begin
        _v572_values = np.asarray(
            stats.get('v572_candidate_min_clearances', []),
            dtype=float
        )

        _v612_expanded = int(stats.get('expanded', 0))
        _v612_calls = int(
            stats.get('v612_candidate_eval_calls', 0)
        )

        _v612_wall = time.monotonic() - begin
        _v612_clearance_wall = float(
            stats.get('v612_clearance_eval_wall_s', 0.0)
        )
        _v612_heuristic_wall = float(
            stats.get('v612_heuristic_wall_s', 0.0)
        )

        print('V612_SEARCH_PROFILE', {
            'status': status,
            'expanded': _v612_expanded,
            'steering_samples': 5,
            'candidate_eval_calls': _v612_calls,
            'candidate_records': int(_v572_values.size),
            'expected_candidate_upper_bound': (
                _v612_expanded * 5
            ),
            'candidate_counter_consistent': bool(
                _v612_calls == _v572_values.size
                and _v612_calls <= _v612_expanded * 5
            ),
            'wall_seconds': _v612_wall,
            'budget_seconds': float(cfg.max_seconds) * 8,
            'clearance_eval_seconds': _v612_clearance_wall,
            'heuristic_seconds': _v612_heuristic_wall,
            'other_seconds': max(
                0.0,
                _v612_wall
                - _v612_clearance_wall
                - _v612_heuristic_wall
            )
        }, flush=True)

        _v572_gate_counters = {
            k: v for k, v in stats.items()
            if k.startswith(('v571_', 'v40_', 'v38_', 'v2_'))
            and isinstance(v, (int, float, str, bool))
        }
        print('V572_SEARCH_DIAGNOSTICS', {
            'status': status,
            'expanded': int(stats.get('expanded', 0)),
            'start_clearance_m': float(start_clearance),
            'observed_guard_m': float(observed.guard),
            'effective_floor_m': float(clearance_floor),
            'candidate_samples': int(_v572_values.size),
            'candidate_min_clearance_m': (
                float(np.min(_v572_values))
                if _v572_values.size else None
            ),
            'candidate_below_floor_count': (
                int(np.sum(
                    _v572_values
                    < float(clearance_floor) - 1e-9
                ))
                if _v572_values.size else 0
            ),
            'gate_counters': _v572_gate_counters,
        }, flush=True)
        if path is not None:
            stats['path_length_m'] = float(np.linalg.norm(np.diff(path[:, :2], axis=0), axis=1).sum())
            stats['min_exact_clearance_m'] = float(observed.pose_values(path).min())
            stats['goal_distance_m'] = float(np.linalg.norm(path[-1, :2]-goal))
        return path, stats

    if observed.pose_values([start])[0] < observed.guard:
        return finish(None, 'start_occupied_no_teleport')
    _v612_h_begin = time.monotonic()
    heuristic = base._heuristic_grid(observed, goal)
    stats['v612_heuristic_wall_s'] = (
        time.monotonic() - _v612_h_begin
    )
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
    print('V619_RUNTIME_STEERING_GRID', {
        'count': int(steers.size),
        'values': [float(v) for v in steers]
    }, flush=True)
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
        if time.monotonic()-begin > (float(cfg.max_seconds)*8):
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
            _v619_min_clearance = float(observed.pose_values(path).min())
            print('V619_FINAL_PATH_CLEARANCE', {
                'minimum_m': _v619_min_clearance,
                'hard_floor_m': float(cfg.margin)
            }, flush=True)
            if observed.pose_values(path).min() < cfg.margin-1e-8:
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
            _v612_eval_begin = time.monotonic()

            clearance = observed.pose_values(piece)

            stats['v612_candidate_eval_calls'] += 1

            stats['v612_clearance_eval_wall_s'] += (
                time.monotonic() - _v612_eval_begin
            )
            stats['v572_candidate_min_clearances'].append(float(np.min(clearance)))
            if np.min(clearance) < clearance_floor - 1e-9:
                continue
            nxt = piece[-1]
            identifier = key(nxt)
            new = cost+cfg.primitive_length*(1+0.10*abs(steering/max_steer)
                    +0.35/(0.10+float(np.min(clearance))))
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
