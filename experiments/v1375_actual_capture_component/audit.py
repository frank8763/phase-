"""Full saved-state/control/causal-bound audit; zero physical imports."""
import gzip
import math
import sys
import numpy as np
from component_context import *
from controller import Capture,errors
from gear_handoff import GearHandoff
from stamped_contract import before_step
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from sampling_audit import state_body_audit,frame_audit
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from recovery_guard import check as static_guard
from dynamic_reserve import check as dynamic_guard
sys.path.insert(0,str(R/'experiments/v1374_day_handoff_validation'))
from probe import interval_ball,field,geometry

def audit(task):
    out=Path(task['output']);native=read(out/'RESULT.json');setup=read(out/'physics/SETUP.json');initial=read(out/'INITIAL_PACKET.json');final=read(out/'FINAL_PACKET.json');rows=read(out/'APPLIED_JOURNAL.json');origin=9390
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k] for k in z.files}
    with gzip.open(out/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    with gzip.open(out/'physics/CONTACTS.json.gz','rt') as f:contacts=json.load(f)
    n=len(rows);maximum=0.
    with np.load(Path(task['prior_raw'])/'physics/NATIVE_TRACE.npz') as z:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            if trace[k].size:maximum=max(maximum,float(abs(trace[k][:origin]-z[k][:origin]).max()))
    body_error=state_body_audit(trace,rows,initial['body']);ctrl=trace['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    checks=dict(full_recorded=len(trace['time'])==n==native['actual_total_native']==native['own_replay_native'],
        exact_prefix=maximum<=1e-8 and read(out/'PREFIX_RESTORE.json')['passed'],full_body_feedback=body_error<=1e-8,
        separated_counts=native['historical_prefix_replay_native']==origin and native['new_component_native']==n-origin,
        original_model=setup['model_sha256']==read(Path(task['prior_raw'])/'physics/SETUP.json')['model_sha256'],
        finite=all(np.isfinite(trace[k]).all() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),
        actual_clearance=bool(trace['clearance'].min()>=.15-1e-8),self_margin=bool(trace['self_margin'].min()>=-1e-10),
        actual_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),
        legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all() and (ctrl<=limits[:,1]+1e-10).all()),
        legal_slew=bool((abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()),
        no_bad_contacts=len(contacts)==n+1 and all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
        own_replay=native.get('replay',{}).get('passed') is True and native['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        complete_stop=all(z['phase']=='COMPLETE_STOP_TAIL' and z['request']==[0.,0.,False] for z in rows[-200:]),
        measured_rest=max(abs(x) for x in final['body'][3:])<=.003,
        steering_rest=max(abs(x) for x in final['steering']['velocity'])<=.03,
        drive_zero=max(abs(x) for x in final['controller_memory']['last_ctrl'][2:])<=1e-10,
        root_guard=native['physical']['root_guard_native_count']==n,
        allocator=native.get('independent_allocation',{}).get('passed') is True,
        source_unchanged=native['source_unchanged'] and sources())
    gate=GearHandoff()
    for row in rows:
        v,w,p=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert row['applied'] and row['request']==[v,w,False] and row['gear_handoff']==p,'GEAR_CHANGED'
        if row['expiry_gate'] is not None:
            v,w,p=before_step(*row['raw_upstream_request'][:2],row['delivery'],row['expiry_gate']['applied_monotonic'])
            assert row['upstream_request']==[v,w,False] and row['expiry_gate']==p,'EXPIRY_CHANGED'
    checks['all_gear_and_expiry']=True
    wires=read(out/'OBSERVATIONS_SENT.json');checks['all_wire_actual_scan_binding']=frame_audit(wires,sensors,rows,origin)
    controls=read(out/'CAPTURE_COMMANDS.json');controller=Capture(task)
    for index,c in enumerate(controls):
        wire=wires[index];assert wire['native_tick']==c['before_native'] and wire['sequence']==index
        v,w,state=controller.select(wire['body'],wire['native_tick']);assert state==c['controller_state']
        p=c['packet'];assert p['v']==v and p['w']==w and p['run_id']==task['run_id'] and p['sequence']==index
        d=c['delivery'];assert d['origin']['kind']=='RPCCR_CAPTURE_NATIVE' and d['origin']['generated_monotonic']==p['issued_at'] and d['observation_sampled_at']==wire['sampled_at'] and d['observation_native_tick']==wire['native_tick'] and d['observation_sequence']==index and d['command_sequence']==index
        da,dp=dynamic_guard(wire['body'],task['causal_all_future_ball'],v,w);sa,sp=static_guard(setup['known'],wire['body'],v,w)
        assert c['dynamic_allowed']==da and c['dynamic_proof']==dp and c['static_allowed']==sa and c['static_proof']==sp
        applied=5 if da and sa else 0;assert c['applied_native']==applied
        for row in rows[c['before_native']:c['before_native']+applied]:assert row['delivery']==d and row['command_sequence']==index and row['raw_upstream_request']==[v,w,False]
        if applied==0:assert all(row['phase']=='COMPLETE_STOP_TAIL' and row['request']==[0.,0.,False] for row in rows[c['before_native']:])
    checks['measured_capture_controller_and_reserves']=True
    probe=read(R/'runs/v1374_day_handoff_validation/CAPTURE_NOMINAL_PROBE.json');assert probe['periodic_source_tick']==task['causal_source_tick']<=9390
    ball=interval_ball(probe['causal_vertices'],93.9,93.9+math.tau/.32);assert [*ball[0].tolist(),ball[1]]==task['causal_all_future_ball']
    q=trace['qpos'][origin:];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));rear=np.c_[q[:,0]-.3*np.cos(yaw),q[:,1]-.3*np.sin(yaw),yaw]
    certified=float(geometry.pose_values(field(setup['known'],ball),rear).min());checks['every_new_actual_pose_causal_all_future22cm']=certified>=.22-1e-8
    pos,heading=errors(final['body'],task['target_segment']);checks.update(position_capture=pos<=.12,heading_capture=heading<=.20,component_functional=native['passed'])
    repeat=None
    if task['role']=='repeat':
        baseline=read(C/'TASKS.json')[0];base=Path(baseline['output']);error=0.
        with np.load(base/'physics/NATIVE_TRACE.npz') as z:
            assert len(z['time'])==n,'REPEAT_LENGTH'
            for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                if trace[k].size:error=max(error,float(abs(trace[k]-z[k]).max()))
        repeat=dict(full_state_ctrl_mocap_max_error=error,full_native_count=n);checks['full_repeat']=error<=1e-8
    checks={k:bool(v) for k,v in checks.items()}
    return dict(passed=all(checks.values()),checks=checks,position_error_m=pos,heading_error_rad=heading,
        minimum_causal_actual_clearance_m=certified,body_error=body_error,prefix_error=maximum,actual_total_native=n,
        historical_prefix_replay_native=origin,new_component_native=n-origin,own_replay_native=n,repeat=repeat,models=0,new_physical_native=0,
        scope='pose capture component, not complete dynamic handoff or original goal navigation')
