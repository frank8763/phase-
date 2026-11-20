"""Saved V1378 response followed by the registered nominal segment, zero models.

The measured preparation belongs to this one saved input. Movement and its
time/error bounds remain assumptions, even when the conditional geometry passes.
"""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R, O, RAW, read, sha, json, np, load, function, scalar_distance, SimpleNamespace
from audit_timed_nominal import independent_swept

ACTUAL = R / 'runs/v858_nav2_verified/v1378/steering_response'


def validate(data):
    assert data['models'] == data['physical_native'] == data['replay_native'] == 0
    assert data['coefficient_source_tick'] == 32200
    assert data['actual_preparation_only_one_saved_input'] is True
    assert data['complete_physical_admission'] is False
    assert data['moving_tracking_and_timing_envelope_qualified'] is False
    assert data['moving_start_native_tick'] == 32600
    assert abs(data['observed_preparation_and_tail_s'] - 3.9) < 1e-8
    assert data['nominal_wait_s'] == 0
    t = np.asarray(data['move_relative_times_s'])
    p = np.asarray(data['nominal_rear_poses'])
    v = np.asarray(data['nominal_speed_m_s'])
    assert len(t) == len(p) == len(v)
    assert abs(t[0] - 3.9) < 1e-8 and np.max(abs(np.diff(t) - .02)) < 1e-8
    body = read(ACTUAL / 'FINAL_PACKET.json')['body']
    start = np.array([body[0] - .3 * math.cos(body[2]), body[1] - .3 * math.sin(body[2]), body[2]])
    assert np.max(abs(p[0] - start)) < 1e-8, 'ACTUAL_START_NOT_BOUND'
    assert max(abs(v)) <= .1 + 1e-8 and max(abs(v[-101:])) < 1e-10
    assert data['moving_time_uncertainty_s'] == .2
    assert data['state_tube_assumptions']['translation_m'] == .02
    assert data['state_tube_assumptions']['yaw_rad'] == .1


def main():
    os.sched_setaffinity(0, {4})
    os.nice(max(0, 19 - os.getpriority(os.PRIO_PROCESS, 0)))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')))
    signal.alarm(600)
    begin = time.monotonic()
    frozen = read(O / 'OBSERVED_BRIDGE_SOURCE_FREEZE.json')['files']
    assert all(sha(R / p) == h for p, h in frozen.items())
    result = read(ACTUAL / 'RESULT.json')
    audit = read(ACTUAL / 'FINAL_INDEPENDENT_AUDIT.json')
    assert result['passed'] and audit['passed']
    rows = read(ACTUAL / 'APPLIED_JOURNAL.json')[32210:]
    final = read(ACTUAL / 'FINAL_PACKET.json')
    assert len(rows) == 390 and final['native_tick'] == 32600
    assert [x['before_native'] for x in rows] == list(range(32210, 32600))
    assert sum(x['phase'] == 'COMPLETE_STOP_TAIL' for x in rows) == 200
    assert all(max(abs(v) for v in x['last_ctrl'][2:]) == 0 for x in rows)
    prep = [x['body'] for x in rows] + [final['body']]
    origin_body = prep[0]
    translation = max(math.dist(p[:2], origin_body[:2]) for p in prep)
    turn = max(abs(math.atan2(math.sin(p[2]-origin_body[2]), math.cos(p[2]-origin_body[2]))) for p in prep)
    assert translation <= .02 and turn <= .1
    # Observed pose/tick readback only: no physics construction or replay.
    model = read(RAW / 'CAUSAL_PREDICTION_MODEL.json')
    assert model['periodic']['source_tick'] == 32200
    known = read(RAW / 'physics/SETUP.json')['known']
    goal = np.asarray(read(O / 'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['original_segment_unchanged']['poses'][-1])
    body = final['body']
    start = np.array([body[0]-.3*math.cos(body[2]), body[1]-.3*math.sin(body[2]), body[2]])
    length = float(np.linalg.norm(goal[:2] - start[:2]))
    cruise = (length - .15) / .1
    assert cruise > 0
    moving = 3 + cruise
    t = np.arange(math.ceil((moving+2)/.02)+1)*.02
    a = np.clip(t, 0, 1)
    c = np.clip(t-1, 0, cruise)
    b = np.clip(t-1-cruise, 0, 2)
    distance = .05*a*a+.1*c+.1*b-.025*b*b
    speeds = np.where(t <= 1, -.1*t, -np.maximum(0, .1-.05*b))
    yaw = start[2] + .5*distance
    rear = np.c_[start[0]+(np.sin(yaw)-math.sin(start[2]))/-.5,
                 start[1]-(np.cos(yaw)-math.cos(start[2]))/-.5, yaw]
    center = rear.copy()
    center[:, :2] += .3*np.c_[np.cos(yaw), np.sin(yaw)]
    times = 3.9+t
    indices = np.floor(times/.1+1e-10).astype(int)
    support = load('original_bridge_support', 'experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped = function('experiments/v1366_canonical_timed_lattice/build_polygons.py', 'clipped')
    distances = function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py', 'distances')
    geometry = load('original_bridge_static', 'experiments/v855_renewal_worker/exact_footprint.py')
    field = SimpleNamespace(half=np.array([.44,.375]), center_local=np.array([.3,0.]),
        rectangles=np.asarray(known['known_rectangles']), circles=np.asarray(known['known_circles']),
        sensor_points=[], sensor_extra=0., config=SimpleNamespace(lower=-5., upper=5.))
    static = geometry.pose_values(field, rear)
    normals = np.c_[np.cos(np.arange(16)*math.pi/8), np.sin(np.arange(16)*math.pi/8)]
    values = np.empty(len(t)); polygons = {}; support_error = 0.
    for index in np.unique(indices):
        lo = model['last_observed_time']+max(0, index*.1-.22)
        hi = model['last_observed_time']+(index+1)*.1+.22
        bounds = support.swept_bounds(model['periodic']['vertices'], lo, hi)+.1
        support_error = max(support_error, float(np.max(abs(bounds-independent_swept(model['periodic']['vertices'], lo, hi)))))
        polygon = clipped(normals, bounds); polygons[str(index)] = polygon.tolist()
        mask = indices == index
        values[mask] = distances(center[mask], polygon)
    assert support_error < 1e-8
    independent = np.array([scalar_distance(p, polygons[str(i)]) for p, i in zip(center, indices)])
    geometry_error = float(np.max(abs(independent-values))); assert geometry_error < 1e-8
    radius = math.hypot(.74, .375)
    interpolation = (.1+radius*.05)*.02/2
    nominal_lower = float(np.minimum(values, static).min())-interpolation
    # Distance to an obstacle is 1-Lipschitz under Hausdorff displacement.
    # This is a sufficient set bound, not an experimentally qualified response.
    tube_cost = .02 + 2*radius*math.sin(.1/2)
    conditional_lower = nominal_lower-tube_cost
    endpoint_pos = float(np.linalg.norm(rear[-1,:2]-goal[:2]))
    endpoint_heading = abs(math.atan2(math.sin(rear[-1,2]-goal[2]), math.cos(rear[-1,2]-goal[2])))
    data = dict(models=0, physical_native=0, private_native=0, replay_native=0,
        coefficient_source_tick=32200, actual_preparation_only_one_saved_input=True,
        moving_start_native_tick=32600, observed_preparation_and_tail_s=3.9,
        actual_preparation_native=190, actual_stop_tail_native=200,
        observed_max_translation_m=translation, observed_max_yaw_change_rad=turn,
        observed_preparation_causal_lower_m=audit['minimum_causal_actual_clearance_m'],
        nominal_wait_s=0, move_relative_times_s=times.tolist(), nominal_rear_poses=rear.tolist(),
        nominal_speed_m_s=speeds.tolist(), source_cell_indices=indices.tolist(),
        source_interval_polygons=polygons, nominal_dynamic_clearance_m=values.tolist(),
        nominal_static_clearance_m=static.tolist(), moving_time_uncertainty_s=.2,
        nominal_moving_clearance_lower_m=nominal_lower, continuous_interpolation_allowance_m=interpolation,
        state_tube_assumptions=dict(translation_m=.02, yaw_rad=.1, qualified=False),
        full_footprint_state_tube_cost_m=tube_cost,
        conditional_moving_tube_lower_m=conditional_lower,
        conditional_geometry_passed=conditional_lower>=.22,
        nominal_endpoint_position_m=endpoint_pos, nominal_endpoint_heading_rad=endpoint_heading,
        nominal_endpoint_passed=endpoint_pos<=.12 and endpoint_heading<=.20,
        sufficient_translation_plus_rotation_error_budget_m=nominal_lower-.22,
        complete_physical_admission=False, moving_tracking_and_timing_envelope_qualified=False,
        original_endpoint_contract_and_fixed_candidate_unchanged=True,
        independent_support_error=support_error, independent_distance_error=geometry_error,
        wall_s=time.monotonic()-begin)
    validate(data)
    rejects=[]
    for key, value in [('coefficient_source_tick',32600), ('complete_physical_admission',True),
                       ('moving_tracking_and_timing_envelope_qualified',True), ('moving_start_native_tick',32210),
                       ('observed_preparation_and_tail_s',4.), ('moving_time_uncertainty_s',0.)]:
        bad=copy.deepcopy(data);bad[key]=value
        try:validate(bad)
        except AssertionError:rejects.append(key)
        else:raise AssertionError('TAMPER_ACCEPTED '+key)
    bad=copy.deepcopy(data);bad['nominal_rear_poses'][0][0]+=.01
    try:validate(bad)
    except AssertionError:rejects.append('start_pose')
    else:raise AssertionError('START_TAMPER_ACCEPTED')
    data['negative_cases_rejected']=rejects
    assert all(sha(R / p) == h for p, h in frozen.items())
    target=O/'OBSERVED_PREPARATION_BRIDGE.json';assert not target.exists()
    target.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    assert read(target)==data
    print(json.dumps({k:v for k,v in data.items() if not isinstance(v,(list,dict))},allow_nan=False))


if __name__ == '__main__':
    main()
