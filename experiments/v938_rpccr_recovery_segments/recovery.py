"""Construct a connected risk-qualified recovery reference, never actuator commands."""
from pathlib import Path
import math
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/v936_rpccr_corridor_search'))
from corridor_search import (EDGE_N, GAP, K, REQUIRED, SPATIAL, STEP,
                             Geometry, primitive, search)

MAX_SEGMENT_M = 1.2
MIN_PROGRESS_M = .6


def dense_path(path, samples=EDGE_N):
    """Recover exact arc samples from the reference; reject non-Ackermann edges."""
    rows = [np.asarray(path[0], dtype=float)]
    for start, end in zip(path, path[1:]):
        start, end = np.asarray(start), np.asarray(end)
        offset = end[:2] - start[:2]
        direction = 1 if offset @ [math.cos(start[2]), math.sin(start[2])] >= 0 else -1
        angle = math.atan2(math.sin(end[2] - start[2]), math.cos(end[2] - start[2]))
        curvature = angle / (direction * STEP)
        assert abs(curvature) <= K + 1e-8, 'UNREPRESENTABLE_REFERENCE_CURVATURE'
        arc = primitive(start, direction, curvature, np.linspace(STEP/samples, STEP, samples))
        assert np.max(abs(arc[-1] - end)) < 1e-8, 'REFERENCE_NOT_AN_ACKERMANN_ARC'
        rows.extend(arc)
    return np.asarray(rows)


def certify(path, known, prior):
    assert prior is not None, 'MISSING_CAUSAL_PERIODIC_SET'
    poses = dense_path(path)
    static, dynamic = Geometry(known, prior).clearances(poses)
    return dict(
        passed=bool(np.minimum(static, dynamic).min() >= REQUIRED),
        static_lower_m=float(static.min() - SPATIAL - GAP),
        dynamic_cycle_lower_m=float(dynamic.min() - SPATIAL - GAP),
        terminal_cycle_lower_m=float(dynamic[-1] - SPATIAL),
        original_threshold_m=.155,
        maximum_original_spatial_reserve_m=SPATIAL,
        interpolation_reserve_m=GAP,
        samples=len(poses),
    )


def construct(start, goal, known, prior):
    """Static route first; select only its connected, fully certified initial arc."""
    static_route = search(start, goal, known, None)
    result = dict(passed=False, models=0, integrations=0,
                  path=[], original_goal=list(goal),
                  static_route=static_route,
                  goal_reached=False, physical_execution=False)
    if not static_route['passed']:
        return dict(result, status='NO_COMPLETE_STATIC_ROUTE')
    path = static_route['path']
    geometry = Geometry(known, prior)
    accepted = 0
    limit = min(len(path)-1, int(round(MAX_SEGMENT_M / STEP)))
    for index in range(limit + 1):
        probe = dense_path(path[index-1:index+1]) if index else np.asarray(path[:1])
        if not geometry.passes(probe).all():
            break
        accepted = index
    segment = path[:accepted+1]
    initial_error = float(np.linalg.norm(np.asarray(start[:2])-goal))
    final_error = float(np.linalg.norm(np.asarray(segment[-1][:2])-goal))
    progress = initial_error-final_error
    if accepted == 0 or progress < MIN_PROGRESS_M:
        return dict(result, status='NO_CERTIFIED_PROGRESS_SEGMENT',
                    available_prefix_m=accepted*STEP,
                    available_goal_progress_m=progress)
    proof = certify(segment, known, prior)
    assert proof['passed'], 'EXTRACTED_SEGMENT_CERTIFICATE_DISAGREES'
    return dict(result, passed=True, status='RECOVERY_SEGMENT', path=segment,
                certificate=proof, nominal_length_m=accepted*STEP,
                nominal_goal_progress_m=progress,
                nominal_terminal_goal_error_m=final_error,
                causal_periodic_source_tick=prior['source_tick'],
                next_goal_is_original_goal=True,
                limits='Reference geometry only; actual RPP tracking, new observations and final arrival unverified.')
