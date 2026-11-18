"""Saved-array failure diagnosis. Never constructs/steps a physical model."""
import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np

R = Path(__file__).resolve().parents[2]
D = R / 'records/v1329_static_route_20261118'
RAW = R / 'runs/v858_nav2_verified/v1329/static_main'


def read(p): return json.loads(p.read_text())
def dump(p, x): p.write_text(json.dumps(x, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assert-safe', action='store_true')
    args = parser.parse_args()
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert (R / 'REVIEW_PENDING').read_bytes() == (R / 'runs/v1329_coherent_mppi_static_route/REVIEW_PENDING.before').read_bytes()
    result = read(RAW / 'RESULT.json')
    trace = dict(np.load(RAW / 'physics/NATIVE_TRACE.npz'))
    failed = dict(np.load(RAW / 'physics/FAILED_NATIVE_STATE.npz'))
    setup = read(RAW / 'physics/SETUP.json')
    journal = read(RAW / 'APPLIED_JOURNAL.json')
    n = len(trace['time'])
    actual = int(round(float(failed['time']) / .01))
    assert actual == n + 1 == result['physical']['root_guard_native_count'] == result['physical']['actual_native']
    assert len(journal) == actual and not journal[-1]['applied']
    assert all(row['applied'] and row['before_native'] == i for i, row in enumerate(journal[:-1]))
    # The failed step is physically witnessed even though the original generic
    # exception flag conservatively left new_actual_native=null. Preserve it.
    pose = failed['qpos']
    yaw = float(np.arctan2(2*(pose[3]*pose[6]+pose[4]*pose[5]), 1-2*(pose[5]**2+pose[6]**2)))
    task = read(R / 'experiments/v1329_coherent_mppi_static_route/TASKS.json')[0]
    reference = np.asarray(task['center_reference_path'])
    nearest = int(np.argmin(np.linalg.norm(reference[:, :2] - pose[:2], axis=1)))
    geometry = R / 'experiments/v855_renewal_worker/exact_footprint.py'
    spec = importlib.util.spec_from_file_location('saved_only_geometry', geometry)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    field = SimpleNamespace(half=np.array([.44, .375]), center_local=np.zeros(2),
                            rectangles=np.asarray(setup['known']['known_rectangles']),
                            circles=np.asarray(setup['known']['known_circles']), sensor_points=[],
                            sensor_extra=0., config=SimpleNamespace(lower=-5., upper=5.))
    body = [*pose[:2], yaw]
    nearest_obstacles = []
    for i, rectangle in enumerate(field.rectangles):
        single = SimpleNamespace(**vars(field)); single.rectangles = rectangle[None]; single.circles = []
        nearest_obstacles.append((float(module.pose_values(single, [body])[0]), i))
    minimum, obstacle = min(nearest_obstacles)
    with gzip.open(RAW / 'physics/SENSORS.json.gz', 'rt') as stream: scans = json.load(stream)
    scan = scans[-1]
    ranges = np.asarray(scan['ranges']); angles = float(scan['yaw']) + np.arange(32)*np.pi/16
    endpoints = np.asarray(scan['xy']) + ranges[:, None]*np.c_[np.cos(angles), np.sin(angles)]
    point_field = SimpleNamespace(**vars(field)); point_field.rectangles = np.empty((0, 4)); point_field.circles = np.empty((0, 3))
    point_field.sensor_points = endpoints[ranges < 2.99]
    point_clear = float(module.pose_values(point_field, [body])[0])
    ids = setup['actuator_ids']; ctrl = np.vstack([trace['ctrl'], failed['ctrl']])[:, ids]
    limits = np.asarray(setup['limits']); rate = np.asarray(setup['slew_per_second'])*.01
    initial = read(RAW / 'INITIAL_PACKET.json')['controller_memory']['last_ctrl']
    with gzip.open(RAW / 'physics/CONTACTS.json.gz', 'rt') as stream: contacts = json.load(stream)
    checks = dict(finite_all_saved_states=all(np.isfinite(v).all() for v in [*trace.values(), *failed.values()]),
                  complete_failure_state_witness=actual == n+1,
                  saved_time_consistent=bool(np.max(abs(trace['time']-.01*np.arange(1,n+1))) <= 1e-8 and abs(float(failed['time'])-.01*actual) <= 1e-8),
                  recorded_prefix_safe=bool(trace['clearance'].min() >= .15-1e-8),
                  actual_failed_state_safety=False,
                  self_prefix_legal=bool(trace['self_margin'].min() >= -1e-10),
                  all_including_failed_control_limits=bool(((ctrl >= limits[:,0]-1e-10)&(ctrl <= limits[:,1]+1e-10)).all()),
                  all_including_failed_control_slew=bool((abs(np.diff(np.vstack([initial, ctrl]),axis=0)) <= rate+1e-10).all()),
                  all_contacts_recorded=len(contacts)==actual+1,
                  bad_contacts_zero=all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
                  source_unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in read(R/'experiments/v1329_coherent_mppi_static_route/SOURCE_FREEZE.json')['files'].items()))
    summary = dict(passed=False, closed=True, scope='one exposed static pilot', actual_native_exact=actual,
                   regular_trace_native=n, separately_saved_failed_native=1, own_replay_native=0,
                   private_mujoco_native=0, training_updates=0, canonical_vehicle_initializations=1,
                   internal_factory_model_constructions='unknown', original_null_counter_preserved=True,
                   exact_count_witnesses=['failed_state.time/dt','root_guard_native_count','physical.actual_native','regular_trace+1','applied_journal'],
                   minimum_actual_clearance_m=result['physical']['minimum_actual_clearance_m'], bad_contacts=0,
                   remaining_goal_m=result['physical']['goal_distance_m'], wall_s=result['wall_s'],
                   nearest_reference_index=nearest, center_reference_distance_m=float(np.linalg.norm(reference[nearest,:2]-pose[:2])),
                   heading_difference_to_nearest_reference_rad=abs(float(np.arctan2(np.sin(yaw-reference[nearest,2]),np.cos(yaw-reference[nearest,2])))),
                   nominal_reference_clearance_m=float(module.pose_values(field,[reference[nearest]])[0]),
                   nominal_failed_pose_clearance_m=minimum, nearest_static_rectangle_index=obstacle,
                   last_scan_endpoints_nominal_clearance_m=point_clear,
                   scan_endpoint_comparison_is_not_accumulated_costmap_reconstruction=True,
                   unexecuted=['static_repeat'], complete_stop_executed=False, own_replay_executed=False,
                   checks=checks, diagnostic_models=0, diagnostic_new_physical_native=0,
                   safety_gate_reproduced=result['physical']['minimum_actual_clearance_m'] < .15-1e-8)
    assert summary['safety_gate_reproduced'] and all(v for k,v in checks.items() if k != 'actual_failed_state_safety')
    D.mkdir(exist_ok=True); dump(D/'RESULT_SUMMARY.json',summary)
    print(json.dumps({k:summary[k] for k in ['actual_native_exact','minimum_actual_clearance_m','center_reference_distance_m','nominal_reference_clearance_m','last_scan_endpoints_nominal_clearance_m','safety_gate_reproduced']}))
    if args.assert_safe:
        assert not summary['safety_gate_reproduced'], 'REPRODUCED_NATIVE_CLEARANCE_FAILURE'


if __name__ == '__main__': main()
