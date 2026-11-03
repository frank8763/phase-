"""Known-geometry-only finite scene construction. No simulator or navigation import."""
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
PARENT = REPO / 'experiments/v706_global_field_qualification'
sys.path.insert(0, str(REPO / 'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0, str(PARENT))
from exact_footprint import build
from task_planner import search, wrap
from task_preflight import certify

def load_footprint():
    spec = importlib.util.spec_from_file_location('v708_frozen_footprint', REPO / 'current/footprint_map_b70_v513.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert 'mujoco' not in sys.modules, 'SIMULATOR_IMPORTED_IN_GEOMETRY_STAGE'
    return module

def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False, default=lambda x: x.tolist() if hasattr(x, 'tolist') else x) + '\n')

def world(known, anchor=None):
    return dict(rectangles=known['known_rectangles'], circles=[*known['known_circles'], *([] if anchor is None else [[*anchor, .35]])],
                sensor_points=[], robot_radius=.28, sensor_radius=.36, footprint_bounds=[-.44, -.375, .44, .375])

def point_clearance(points, known):
    p = np.asarray(points)
    result = np.min(5. - np.abs(p), axis=1)
    for x, y, hx, hy in known['known_rectangles']:
        result = np.minimum(result, np.linalg.norm(np.maximum(np.abs(p - [x, y]) - [hx, hy], 0), axis=1))
    for x, y, r in known['known_circles']:
        result = np.minimum(result, np.linalg.norm(p - [x, y], axis=1) - r)
    return result

def project(points, route):
    a, b = route[:-1, :2], route[1:, :2]
    delta = b - a
    lengths = np.linalg.norm(delta, axis=1)
    arc = np.r_[0., np.cumsum(lengths)]
    t = np.clip(np.sum((points[:, None, :] - a) * delta, axis=2) / np.maximum(lengths ** 2, 1e-30), 0., 1.)
    projected = a + t[:, :, None] * delta
    distance = np.linalg.norm(points[:, None, :] - projected, axis=2)
    j = distance.argmin(axis=1)
    i = np.arange(len(points))
    yaw = route[j, 2] + t[i, j] * np.asarray([wrap(v) for v in route[1:, 2] - route[:-1, 2]])[j]
    return distance[i, j], arc[j] + t[i, j] * lengths[j], j, t[i, j], yaw, float(arc[-1])

def construct(case, known, output):
    output.mkdir()
    F = load_footprint()
    w = world(known)
    field = build(F, w)
    field.base_heuristic = F.base._heuristic_grid
    start = [*case['start_xy'], case['yaw']]
    route, stats = search(field, start, case['goal_xy'], .6, .42722137342572125, guard=.155,
                          resolution=.05, heading_bins=144, dense_requested_guard=True, work_limit=16000)
    write(output / 'KNOWN_REFERENCE.json', dict(stats=stats, path=None if route is None else route.tolist()))
    result = dict(case_id=case['id'], eligible=False, status='KNOWN_REFERENCE_NOT_ACCEPTED', navigation_integrations=0)
    if route is None or stats['status'] != 'GLOBAL_GOAL_PATH':
        write(output / 'RESULT.json', result)
        return result
    axis = np.arange(-45, 46, dtype=float) / 10.
    xx, yy = np.meshgrid(axis, axis, indexing='ij')
    points = np.c_[xx.ravel(), yy.ravel()]
    distance, arc, segment, fraction, yaw, total = project(points, route)
    clearance = point_clearance(points, known)
    tests = dict(near_known_reference=distance <= .50 + 1e-12, after_start_arc=arc >= 1.8,
                 before_goal_arc=arc <= total - 1.4, known_clearance=clearance >= .90,
                 initially_outside_range=np.linalg.norm(points - case['start_xy'], axis=1) >= 3.60,
                 away_from_goal=np.linalg.norm(points - case['goal_xy'], axis=1) >= 1.4,
                 protected_junction=np.linalg.norm(np.maximum(np.abs(points) - .8, 0), axis=1) >= .40)
    eligible = np.logical_and.reduce(list(tests.values()))
    ids = np.flatnonzero(eligible)
    ranked = sorted(ids, key=lambda i: (float(distance[i]), -float(clearance[i]), float(points[i, 0]), float(points[i, 1])))
    write(output / 'CANDIDATE_GRID.json', dict(points=points, tests={k: v.tolist() for k, v in tests.items()},
        nearest_reference_distance=distance, nearest_reference_arc=arc, known_point_clearance=clearance,
        total_arc=total, ranked_eligible_ids=[int(i) for i in ranked], checked_ids=[int(i) for i in ranked[:8]]))
    result.update(status='NO_JOINT_CANDIDATE', necessary_candidate_count=len(ranked), attempts=[])
    for rank, i in enumerate(ranked[:8]):
        anchor = points[i]
        swept = world(known, anchor)
        sf = build(F, swept)
        initial = float(sf.pose_values([start])[0])
        certificate = certify(swept, start, case['goal_xy'], .6, .42722137342572125, F, initial)
        record = dict(rank=rank, grid_index=int(i), anchor_xy=anchor, axis_xy=[-math.sin(yaw[i]), math.cos(yaw[i])],
                      nearest_reference_distance_m=float(distance[i]), nearest_reference_arc_m=float(arc[i]),
                      segment=int(segment[i]), segment_fraction=float(fraction[i]), point_clearance_m=float(clearance[i]),
                      swept_radius_m=.35, initial_distance_m=float(np.linalg.norm(anchor - case['start_xy'])), certificate=certificate)
        write(output / ('CANDIDATE_%02d.json' % rank), record)
        result['attempts'].append(dict(rank=rank, grid_index=int(i), status=certificate['status'], eligible=certificate['eligible']))
        write(output / 'RESULT.json', result)
        if certificate['eligible']:
            result.update(status='JOINT_GEOMETRY_CANDIDATE_CERTIFIED', eligible=True, selection=record)
            break
    write(output / 'RESULT.json', result)
    return result
