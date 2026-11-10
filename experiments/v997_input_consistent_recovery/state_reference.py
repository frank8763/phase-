"""Measured-steering continuous references, pure analytical bicycle geometry.

This module creates references, not actuator authority or physical predictions.
Every spatial sample retains the original full-cycle geometry certificate.
"""
import json
import heapq
import importlib.util
import math
import sys
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location('v977_original_geometry', R/'experiments/v968_rpp_closed_loop_night/corridor_search.py')
_old = importlib.util.module_from_spec(_spec)
_path = sys.path[:]
try:
    _spec.loader.exec_module(_old)
finally:
    sys.path[:] = _path

PARAMETERS=json.loads((Path(__file__).parent/'RESPONSE_PARAMETERS.json').read_text())
GAIN=float(PARAMETERS['gain_a']);RATE_COUPLING=float(PARAMETERS['steering_rate_b'])
K = _old.K
WHEELBASE = .60
TRACK = .54
VIRTUAL_RATE = .60
REFERENCE_SPEED = .05
STEP = .10
EDGE_N = 8
MAX_EXPANSIONS = 5000
MAX_LENGTH = 1.2
POSITION_ENVELOPE = .04
ACTUAL_PROGRESS_REQUIRED = .40
NUMERICAL_RESERVE = 1e-5
REQUIRED = _old.REQUIRED + NUMERICAL_RESERVE + math.hypot(.44,.375)*abs(RATE_COUPLING)*(VIRTUAL_RATE/REFERENCE_SPEED)*(STEP/EDGE_N)/2
MAX_DELTA = math.atan(WHEELBASE*K)
TARGETS = np.linspace(-MAX_DELTA, MAX_DELTA, 5)
_GX, _GW = np.polynomial.legendre.leggauss(8)


def snapshot_state(packet, source, now):
    body = np.asarray(packet['body'], float)
    enc = packet['steering']
    q = np.asarray(enc['position'], float)
    rate = np.asarray(enc['velocity'], float)
    assert body.shape == (5,) and q.shape == rate.shape == (2,), 'INVALID_STATE_SHAPE'
    assert np.isfinite([*body, *q, *rate, now, packet['body_measured_at'], enc['measured_at']]).all(), 'NONFINITE_STATE'
    assert 0 <= now-packet['body_measured_at'] <= .05, 'STALE_BODY'
    assert enc['native_tick'] == packet['native_tick'] and abs(enc['measured_at']-packet['body_measured_at']) <= 1e-9, 'INCOHERENT_ENCODERS'
    assert abs(q).max() <= .52+1e-6 and abs(rate).max() <= .03, 'UNQUALIFIED_STEERING_STATE'
    assert max(abs(body[3:])) <= .03, 'RECOVERY_REQUIRES_ACTUAL_STOP'
    assert source['source_native_tick'] <= packet['native_tick'], 'FUTURE_SOURCE'
    assert 0 <= source['source_age_s'] <= .2, 'STALE_CAUSAL_SOURCE'
    prior = source['periodic']
    assert prior['source_tick'] <= source['source_native_tick'], 'FUTURE_PERIODIC_SOURCE'
    assert prior['omega'] == .32 and prior['amplitude'] == .25, 'PERIODIC_CLASS_CHANGED'
    t = np.tan(q)
    pair = np.array([t[0]/(WHEELBASE+TRACK/2*t[0]), t[1]/(WHEELBASE-TRACK/2*t[1])])
    assert abs(pair[0]-pair[1]) <= .02, 'INCONSISTENT_ACKERMANN_ENCODERS'
    assert abs(pair).max() <= K+2e-6, 'UNQUALIFIED_INITIAL_CURVATURE'
    return np.r_[body[:3], math.atan(WHEELBASE*float(pair.mean()))]


def primitive(state, target, distances):
    """Exact heading integral; split Gauss quadrature for x/y at ramp end."""
    state = np.asarray(state, float)
    s = np.atleast_1d(np.asarray(distances, float))
    assert state.shape == (4,) and np.isfinite([*state, target, *s]).all()
    assert (s >= 0).all() and abs(target) <= MAX_DELTA+1e-12
    x, y, a, d0 = state
    change = target-d0
    if abs(change) < 1e-13:
        poses = _old.primitive(state[:3], 1, GAIN*math.tan(d0)/WHEELBASE, s)
        return np.c_[poses, np.full(len(s), d0)]
    slope = math.copysign(VIRTUAL_RATE/REFERENCE_SPEED, change)
    ramp = abs(change)/abs(slope)
    u = np.minimum(s, ramp)
    delta = d0+slope*u

    def heading(at):
        return a-GAIN*(np.log(np.cos(d0+slope*at))-math.log(math.cos(d0)))/(WHEELBASE*slope)+RATE_COUPLING*slope*at

    points = u[:, None]*(_GX[None, :]+1)/2
    yaw = heading(points)
    px = x+u/2*(np.cos(yaw)@_GW)
    py = y+u/2*(np.sin(yaw)@_GW)
    h = heading(u)
    tail = s-u
    kt = GAIN*math.tan(target)/WHEELBASE
    if abs(kt) < 1e-12:
        px += tail*np.cos(h)
        py += tail*np.sin(h)
    else:
        px += (np.sin(h+kt*tail)-np.sin(h))/kt
        py -= (np.cos(h+kt*tail)-np.cos(h))/kt
    return np.c_[px, py, h+kt*tail, delta]


def search_static(start, goal, known):
    """Deterministic bounded search; steering is part of the visited state."""
    geometry = _old.Geometry(known, None)
    heuristic, hproof = geometry.heuristic(goal)

    def key(p):
        return (round(p[0]/.05), round(p[1]/.05),
                round((p[2] % (2*math.pi))*72/(2*math.pi)) % 72,
                round(p[3]/(MAX_DELTA/2)))

    nodes = [(np.asarray(start), -1, None)]
    best = {key(start): 0.}
    heap = [(1.5*heuristic(start), 0., 0)]
    samples = np.linspace(STEP/EDGE_N, STEP, EDGE_N)
    endpoint = None
    expanded = rejected = 0
    while heap and expanded < MAX_EXPANSIONS:
        _, cost, index = heapq.heappop(heap)
        state, _, _ = nodes[index]
        if cost > best.get(key(state), math.inf)+1e-10:
            continue
        expanded += 1
        if np.linalg.norm(state[:2]-goal) <= .2:
            endpoint = index
            break
        edges = np.asarray([primitive(state, target, samples) for target in TARGETS])
        static = geometry.clearances(edges[:, :, :3].reshape(-1, 3))[0].reshape(len(TARGETS), EDGE_N)
        allowed = (static >= REQUIRED).all(axis=1)
        for j, target in enumerate(TARGETS):
            if not allowed[j]:
                rejected += 1
                continue
            child = edges[j, -1]
            new_cost = cost+STEP*(1+.15*abs(target)/MAX_DELTA)+.02*abs(target-state[3])/MAX_DELTA
            marker = key(child)
            if new_cost >= best.get(marker, math.inf)-1e-10:
                continue
            best[marker] = new_cost
            nodes.append((child, index, float(target)))
            heapq.heappush(heap, (new_cost+1.5*heuristic(child), new_cost, len(nodes)-1))
    report = dict(passed=endpoint is not None, expanded=expanded, generated=len(nodes),
                  rejected_edges=rejected, max_expansions=MAX_EXPANSIONS, heuristic=hproof)
    if endpoint is None:
        return dict(report, status='NO_STEERING_CONTINUOUS_STATIC_ROUTE_WITHIN_FIXED_WORK')
    chain = []
    while endpoint != -1:
        chain.append(endpoint)
        endpoint = nodes[endpoint][1]
    chain.reverse()
    return dict(report, status='STEERING_STATE_ROUTE_FOUND',
                states=[nodes[i][0].tolist() for i in chain], targets=[nodes[i][2] for i in chain[1:]])


def progress_lower_bound(start, finish, goal):
    nominal = float(np.linalg.norm(np.asarray(start)[:2]-goal)-np.linalg.norm(np.asarray(finish)[:2]-goal))
    return nominal, nominal-2*POSITION_ENVELOPE


def construct(packet, source, goal, known, now):
    initial = snapshot_state(packet, source, now)
    goal = np.asarray(goal, float)
    assert goal.shape == (2,) and np.isfinite(goal).all(), 'INVALID_ORIGINAL_GOAL'
    geometry = _old.Geometry(known, source['periodic'])
    start_static, start_dynamic = geometry.clearances(initial[None, :3])
    if min(start_static[0], start_dynamic[0]) < REQUIRED:
        return dict(passed=False, models=0, integrations=0, path=[], status='UNSAFE_INITIAL_REFERENCE_STATE')
    route = search_static(initial, goal, known)
    base = dict(passed=False, models=0, integrations=0, private_dynamics_predictions=0,
                path=[], original_goal=goal.tolist(), static_route=route,
                source_native_tick=source['source_native_tick'], body_native_tick=packet['native_tick'])
    if not route['passed']:
        return dict(base, status=route['status'])
    dense = [initial.tolist()]
    accepted = []
    minimum = math.inf
    candidates = []
    for target in route['targets'][:int(round(MAX_LENGTH/STEP))]:
        segment = primitive(dense[-1], target, np.linspace(STEP/EDGE_N, STEP, EDGE_N))
        static, dynamic = geometry.clearances(segment[:, :3])
        lower = float(np.minimum(static, dynamic).min())
        if lower < REQUIRED:
            break
        dense.extend(segment.tolist())
        accepted.append(target)
        minimum = min(minimum, lower)
        nominal, actual_lower = progress_lower_bound(initial, dense[-1], goal)
        candidates.append((len(accepted), nominal, actual_lower))
    valid = [x for x in candidates if x[2] >= ACTUAL_PROGRESS_REQUIRED]
    if not valid:
        return dict(base, status='NO_CERTIFIED_ACTUAL_PROGRESS_LOWER_BOUND', available_length_m=len(accepted)*STEP,
                    nominal_goal_progress_m=candidates[-1][1] if candidates else 0.,
                    actual_goal_progress_lower_m=candidates[-1][2] if candidates else -2*POSITION_ENVELOPE)
    count, nominal, actual_lower = valid[-1]
    dense = dense[:count*EDGE_N+1]
    return dict(base, passed=True, status='STATE_CONTINUOUS_RECOVERY_REFERENCE', path=[x[:3] for x in dense],
                state_path=dense, edge_targets=accepted[:count], initial_state=initial.tolist(),
                reference_speed_m_s=REFERENCE_SPEED, virtual_steering_rate_rad_s=VIRTUAL_RATE,
                nominal_length_m=count*STEP, nominal_goal_progress_m=nominal,
                actual_goal_progress_lower_m=actual_lower, unchanged_actual_progress_requirement_m=ACTUAL_PROGRESS_REQUIRED,
                position_envelope_m=POSITION_ENVELOPE, minimum_raw_full_cycle_clearance_m=minimum,
                original_threshold_m=.155, spatial_reserve_m=_old.SPATIAL, interpolation_reserve_m=_old.GAP,
                numerical_reserve_m=NUMERICAL_RESERVE, required_clearance_m=REQUIRED,response_parameters=PARAMETERS,maximum_reference_heading_gradient=GAIN*K+abs(RATE_COUPLING)*VIRTUAL_RATE/REFERENCE_SPEED,
                stop_authority_created=False, physical_tracking_qualified=False)
