"""Independent complete native-trajectory audit for steering-continuous references."""
import gzip
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
_saved=sys.path[:]
try:
    spec=importlib.util.spec_from_file_location('v977_original_causal_audit',R/'experiments/v968_rpp_closed_loop_night/corridor_audit.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
finally:sys.path[:]=_saved
sys.path.insert(0,str(C))
from independent_tracking import check as tracking
from saved_qualification import reconstruct,independently_check_geometry


def audit_reference(plan,known,prior):
    assert plan['passed'] is True and plan['status']=='STATE_CONTINUOUS_RECOVERY_REFERENCE','WRONG_REFERENCE_KIND'
    assert plan['reference_speed_m_s']==.05 and plan['virtual_steering_rate_rad_s']==.60,'REFERENCE_DYNAMICS_CHANGED'
    fine=reconstruct(plan['initial_state'],plan['edge_targets'])
    states=np.asarray(plan['state_path']);path=np.asarray(plan['path'])
    assert states.shape==fine[::25].shape and np.max(abs(states-fine[::25]))<1e-5,'REFERENCE_NOT_RECONSTRUCTIBLE'
    assert path.shape==states[:,:3].shape and np.max(abs(path-states[:,:3]))<=1e-12,'STATE_PATH_MISMATCH'
    k=np.tan(fine[:,3])/.60
    assert abs(k).max()<=.758770385+1e-8,'CURVATURE_LIMIT_CHANGED'
    rate=abs(np.diff(fine[:,3]))/(.0005/.05)
    assert rate.max()<=.60+1e-10,'STEERING_RATE_CHANGED'
    raw=independently_check_geometry(fine,known,prior)
    rho=math.hypot(.44,.375)
    reserve=.04+rho*.035+.1*(.13+rho*.16)+.02*(.13+rho*.16+.08)
    gap=.0005/2*(1+rho*.758770385)
    lower=raw-reserve-gap
    assert lower>=.155,'REFERENCE_NOT_FULL_CYCLE_SAFE'
    nominal=float(np.linalg.norm(fine[0,:2]-plan['original_goal'])-np.linalg.norm(fine[-1,:2]-plan['original_goal']))
    assert nominal-.08>=.4,'ACTUAL_PROGRESS_LOWER_BOUND_FAILED'
    return dict(passed=True,full_cycle_clearance_lower_m=lower,actual_progress_lower_m=nominal-.08,
                maximum_curvature=float(abs(k).max()),maximum_virtual_steering_rate=float(rate.max()),
                independent_dense_samples=len(fine),models=0,integrations=0,physical_tracking_claim=False)


def audit(out):
    out=Path(out);rows=json.loads((out/'RECOVERY_CORRIDORS.json').read_text())
    journal=json.loads(gzip.decompress((out/'MOTION_ENVELOPE.json.gz').read_bytes()))
    states={row['native_tick']:row for row in journal['states']};priors={};periodic=original.PeriodicSupport()
    for row in journal['states']:
        periodic.update(row['time'],row['native_tick'],row['support_bounds'])
        priors[row['native_tick']]=None if periodic.last is None else periodic.snapshot()
    setup=json.loads((out/'physics/SETUP.json').read_text());task=json.loads((out/'TASK.json').read_text())
    with np.load(out/'physics/NATIVE_TRACE.npz')as data:
        recorded=original.body_rows(data);velocity=data['qvel'].copy();qpos=data['qpos'].copy()
    reports=[];completed=0
    for row in rows:
        for label in ['entry','search','install','end']:
            if label+'_packet' not in row:continue
            packet,source=row[label+'_packet'],row[label+'_source']
            original.check_source(packet,source,recorded,states,priors)
            angles=qpos[packet['native_tick']-1,setup['steering_qpos_addresses']]
            assert np.max(abs(angles-packet['steering']['position']))<=1e-8,'RECOVERY_ENCODERS_NOT_ACTUAL'
        entry=row['entry_packet'];trigger=row['trigger']['trigger']
        assert trigger['body_native_tick']==entry['native_tick'] and trigger['failed_reference_count']>=3
        assert trigger['observed_stall_s']>=1.5-1e-8 and trigger['observed_motion_m']<.02
        proposal=row.get('proposal');proof=None;actual=None
        if proposal and proposal['passed']:
            assert proposal['original_goal']==task['goal_xy']
            assert np.max(abs(np.asarray(proposal['initial_state'][:3])-row['search_packet']['body'][:3]))<=1e-8
            proof=audit_reference(proposal,setup['known'],row['search_source']['periodic'])
        if row['passed']:
            assert proof and proof['passed'],'NO_QUALIFIED_REFERENCE'
            audit_reference(proposal,setup['known'],row['install_source']['periodic'])
            assert row['install_effect']['path']==proposal['path']
            assert row['install_effect']['controller_id']=='RecoveryFollowPath' and row['install_effect']['goal_checker_id']=='recovery_goal_checker'
            assert row['follow_result_status']==4 and row['renewal']['goal']==task['goal_xy']
            events=[e['action']for e in row['transaction_events']]
            assert events[:3]==['CANCEL_NORMAL_NAVIGATION','WAIT_FRESH_STOPPED_BODY','SEND_FOLLOW_PATH_ONCE']
            assert events.count('SEND_FOLLOW_PATH_ONCE')==1 and events[-1]=='PLAN_TO_ORIGINAL_GOAL'
            assert row['transaction_events'][1]['normal_terminal_status']in [5,6],'NORMAL_ACTION_OVERLAP'
            start=row['install_packet']['native_tick'];end=row['end_packet']['native_tick'];assert end>start
            body=recorded[end-1]
            progress=float(np.linalg.norm(np.asarray(entry['body'][:2])-task['goal_xy'])-np.linalg.norm(body[:2]-task['goal_xy']))
            assert progress>=.4 and np.linalg.norm(body[:2]-proposal['path'][-1][:2])<=.04
            assert np.linalg.norm(velocity[end-1,:2])<=.03
            actual=tracking(proposal['path'],recorded[start-1:end,:3],.0125)
            assert actual['passed'],'ACTUAL_REFERENCE_TRACKING_ENVELOPE_FAILED'
            completed+=1
        reports.append(dict(entry_tick=entry['native_tick'],completed=bool(row['passed']),independent_geometry=proof,actual_tracking=actual))
    result=dict(passed=True,evidence_passed=True,completed_certified_segments=completed,
                attempted_recovery_segments=len(rows),segments=reports,models=0,integrations=0,
                functionally_exercised=completed>=1,scope='Independent cause/encoder/reference/control tracking audit; no new integration')
    (out/'CORRIDOR_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
