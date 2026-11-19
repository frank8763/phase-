"""Independent full recorded component safety, controls and measured restart."""
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from gear_handoff import GearHandoff

R=Path(__file__).resolve().parents[2]


def audit(task):
    out=Path(task['output']);read=lambda name:json.loads((out/name).read_text())
    result=read('RESULT.json');setup=read('physics/SETUP.json');initial=read('INITIAL_PACKET.json')
    journal=read('APPLIED_JOURNAL.json');release=read('COMPONENT_RELEASE.json')
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k].copy() for k in z.files}
    with gzip.open(out/'physics/CONTACTS.json.gz','rt') as f:contacts=json.load(f)
    n=len(trace['time']);ctrl=trace['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    checks=dict(fully_recorded=n==result['new_actual_native']==result['own_replay_native']==len(journal),
        finite_all_states=all(np.isfinite(trace[k]).all() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),
        actual_clearance=bool(trace['clearance'].min()>=.15-1e-8),full_self=bool(trace['self_margin'].min()>=-1e-10),
        actual_control_limits=bool((ctrl>=limits[:,0]-1e-10).all() and (ctrl<=limits[:,1]+1e-10).all()),
        actual_control_rates=bool((abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()),
        zero_bad_contacts=len(contacts)==n+1 and all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
        complete_native_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),
        full_own_replay=result.get('replay',{}).get('passed') is True and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        complete_stop_tail=all(row['phase']=='COMPLETE_STOP_TAIL' and row['request']==[0.,0.,False] for row in journal[-200:]) and len(journal)>=200,
        source_unchanged=result['source_unchanged'],component_functional=result['passed'])
    gate=GearHandoff();gate_ok=True
    for row in journal:
        v,w,proof=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        gate_ok &= row['applied'] and row['request']==[v,w,False] and row['gear_handoff']==proof
    checks['full_gear_reconstruction']=bool(gate_ok)
    # For this fixed .08 reverse/zero component, the unchanged physical Adapter
    # delegates to the signed allocator; speed-governed .125 mode is never used.
    sys.path.insert(0,str(R/'experiments/v993_steering_transient_diagnosis'))
    from fixture import make
    spec=importlib.util.spec_from_file_location('independent_component_allocator',R/'experiments/v1035_signed_timed_input_source/signed_control.py')
    signed=importlib.util.module_from_spec(spec);spec.loader.exec_module(signed);owner=make(signed.Adapter,setup)
    error=0.
    for i,row in enumerate(journal):
        error=max(error,float(abs(owner.last-row['last_ctrl']).max()),abs(owner.integral-row['integral']))
        u=owner.compute(*row['request'][:2],*row['body'][3:],False)
        error=max(error,float(abs(u-ctrl[i]).max()))
    checks['independent_signed_allocation']=error<=1e-8
    point=release['release'];checks['actual_restart200_then_rest']=point is not None and point['proof']['measured_rest'] and point['native_tick']-release['restart_native']>=200
    checks['actual_post_release_reverse']=release['actual_post_release_distance_m']>=.02 and release['after_body'][3]<-.02
    return dict(passed=all(checks.values()),checks=checks,actual_reviewed=n,minimum_actual_clearance_m=float(trace['clearance'].min()),
        independent_control_error=error,models=0,new_physical_native=0,scope='component not navigation')
