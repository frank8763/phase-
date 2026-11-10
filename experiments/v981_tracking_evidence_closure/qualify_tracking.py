"""Saved-pose reproduction, independent curve oracle and actual guard call seam."""
import copy
import gzip
import hashlib
import importlib.abc
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

C = Path(__file__).parent
R = C.resolve().parents[1]
O = R/'runs/v981_tracking_evidence_closure'
sys.path.insert(0, str(C))
from baseline_red import NoModel
sys.meta_path.insert(0, NoModel())
from tracking import TrackingGuard, dense_reference, GRID_M
from transaction import RecoveryTransaction
from independent_tracking import check as independent_check


def main():
    saved = R/'runs/v980_recovery_actuation_postmortem'
    inventory = json.loads((saved/'v979-fixed-recovery-physical-gate.INVENTORY.json').read_text())
    catalog = {row['path']: row['sha256'] for row in inventory['files']}
    for name in ['COMPONENT_REFERENCE.json', 'ONLINE_TRACKING_FAULT.json', 'COMMAND_TUBES.json.gz']:
        assert hashlib.sha256((saved/name).read_bytes()).hexdigest() == catalog['runs/v858_nav2_verified/v979/component_0/'+name]
    plan = json.loads((saved/'COMPONENT_REFERENCE.json').read_text())['proposal']
    packet = json.loads((saved/'ONLINE_TRACKING_FAULT.json').read_text())['packet']
    guard = TrackingGuard(plan)
    checks = {}
    for mode in ['FOLLOW_RECOVERY', 'STOPPED_REPLAN']:
        guard.mode = mode
        guard.monitor_body(packet)
        checks['saved_fault_accepts_'+mode] = guard.last_proof['heading_upper_rad'] < .035
    captured = dict(guard.last_proof)
    spec = importlib.util.spec_from_file_location('v981_independent_midpoint', R/'experiments/v977_state_consistent_recovery/saved_qualification.py')
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    independent = oracle.reconstruct(plan['initial_state'], plan['edge_targets'])[:, :3]
    online = dense_reference(plan)
    difference = np.max(abs(online-independent), axis=0)
    checks['independent_curve_within_explicit_numerical_reserves'] = bool(difference[:2].max() < 1e-5 and difference[2] < 1e-5)
    checks['reference_and_controller_path_unchanged'] = guard.path == plan['path']
    checks['original_position_heading_limits'] = captured['position_limit_m'] == .04 and captured['heading_limit_rad'] == .035
    witnesses=json.loads(gzip.decompress((saved/'COMMAND_TUBES.json.gz').read_bytes()))
    observations=[row['packet']['body'][:3] for row in witnesses]+[packet['body'][:3]]
    for pose in observations:
        guard.monitor_body(dict(body=pose))
    independently_saved=independent_check(plan,observations)
    checks['all_26_available_saved_poses_online_and_independent'] = len(observations)==26 and independently_saved['passed']
    fixed=json.loads((R/'records/nav2_v977_20261110/ZERO_MODEL_QUALIFICATION.json').read_text())['rows']
    fixed_reports=[]
    for row in fixed:
        p=row['plan'];candidate_guard=TrackingGuard(p);candidate_guard.mode='FOLLOW_RECOVERY'
        for pose in p['path']:
            candidate_guard.monitor_body(dict(body=pose))
        fixed_reports.append(independent_check(p,p['path']))
    checks['both_fixed_saved_state_references_qualify'] = len(fixed_reports)==2 and all(row['passed'] for row in fixed_reports)
    proofs = []
    # Both ends and every edge boundary, including ±pi-equivalent observations.
    for index in range(0, len(online), 25):
        p = dict(body=online[index].tolist())
        guard.monitor_body(p)
        proofs.append(guard.last_proof)
        p['body'][2] += 2*math.pi
        guard.monitor_body(p)
    checks['on_reference_and_angle_wrap_all_coarse_samples'] = True
    failures = []
    def rejects(label, target, bad_packet, reason):
        try:
            target.monitor_body(bad_packet)
        except AssertionError as error:
            ok = str(error) == reason
        else:
            ok = False
        failures.append(dict(name=label, passed=ok))
    for sign in [-1., 1.]:
        bad = copy.deepcopy(packet)
        bad['body'] = online[200].tolist()
        bad['body'][2] += sign*.0351
        rejects('true_heading_violation_'+str(sign), guard, bad, 'ONLINE_RECOVERY_HEADING_ENVELOPE_FAILED')
    bad = dict(body=[*online[200]])
    bad['body'][0] += 1.
    rejects('position_violation', guard, bad, 'ONLINE_RECOVERY_POSITION_ENVELOPE_FAILED')
    rejects('nonfinite', guard, dict(body=[math.nan, 0., 0.]), 'NONFINITE_RECOVERY_OBSERVATION')
    changed = TrackingGuard(plan)
    changed.mode = 'FOLLOW_RECOVERY'
    changed.path[0][0] += .001
    rejects('committed_path_mutation', changed, packet, 'COMMITTED_REFERENCE_MUTATED')
    changed = TrackingGuard(plan)
    changed.mode = 'FOLLOW_RECOVERY'
    changed.dense.flags.writeable = True
    changed.dense[0, 0] += .001
    rejects('dense_certificate_mutation', changed, packet, 'TRACKING_CERTIFICATE_MUTATED')
    corrupted = copy.deepcopy(plan)
    corrupted['state_path'][5][0] += .001
    try:
        TrackingGuard(corrupted)
    except AssertionError as error:
        checks['altered_proposal_rejected'] = str(error) == 'COMMITTED_CURVE_NOT_RECONSTRUCTIBLE'
    else:
        checks['altered_proposal_rejected'] = False
    checks['all_violation_negatives'] = all(x['passed'] for x in failures)
    wrong=copy.deepcopy(packet['body'][:3]);wrong[2]+= .2
    checks['independent_real_heading_violation_stays_red'] = not independent_check(plan,[wrong])['passed']
    # The real frozen transaction's observation call now reaches this exact guard.
    tx = RecoveryTransaction([4., 0.], {})
    tx.guard = guard
    tx.mode = 'FOLLOW_RECOVERY'
    tx.monitor_body(packet)
    checks['production_transaction_dispatch_bound'] = tx.guard.last_proof['heading_upper_rad'] < .035
    bridge = (R/'experiments/v979_state_recovery_physical/closed_handoff.py').read_text()
    checks['component_call_uses_same_guard_API'] = 'from transaction import TrackingGuard,fingerprint' in bridge and 'TrackingGuard(plan)' in bridge
    timings = []
    for _ in range(1000):
        start = time.perf_counter()
        guard.monitor_body(packet)
        timings.append(time.perf_counter()-start)
    report = dict(passed=all(checks.values()), checks=checks, negatives=failures,
                  saved_fault=captured, saved_pose_independent=independently_saved, both_fixed_state_independent=fixed_reports,
                  independent_dense_maximum_xyz_error=difference.tolist(),
                  dense_samples=len(online), grid_m=GRID_M,
                  monitoring_measured_s=dict(median=float(np.median(timings)), p99=float(np.quantile(timings,.99)), maximum=max(timings)),
                  timing_scope='1000 local saved-pose calls; no real-time guarantee',
                  models=0, actual_native=0, private_native=0, replay_native=0,
                  physical_ready=False, old_outcome_unchanged='V979_NOT_PASSED')
    (O/'TRACKING_QUALIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    assert report['passed']


if __name__ == '__main__':
    main()
