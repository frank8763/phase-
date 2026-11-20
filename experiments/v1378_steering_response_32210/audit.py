"""Full saved-state/control/causal-bound audit; zero physical imports."""
import gzip
import math
import sys
import numpy as np
from component_context import *
from controller import Capture,errors
from envelope_geometry import bounds
from gear_handoff import GearHandoff
from stamped_contract import before_step
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from sampling_audit import state_body_audit,frame_audit,body_from_state
sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
from recovery_guard import check as static_guard
from dynamic_reserve import check as dynamic_guard
sys.path.insert(0,str(R/'experiments/v1374_day_handoff_validation'))
from probe import interval_ball,field,geometry

def audit(task):
    out=Path(task['output']);native=read(out/'RESULT.json');setup=read(out/'physics/SETUP.json');initial=read(out/'INITIAL_PACKET.json');final=read(out/'FINAL_PACKET.json');rows=read(out/'APPLIED_JOURNAL.json');origin=32210
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
        feedback=rows[wire['native_tick']]
        v,w,state=controller.select(wire['body'],wire['native_tick'],feedback['encoders'],feedback['last_ctrl']);assert state==c['controller_state']
        p=c['packet'];assert p['v']==v and p['w']==w and p['run_id']==task['run_id'] and p['sequence']==index
        d=c['delivery'];assert d['origin']['kind']=='RPCCR_STEERING_RESPONSE_NATIVE' and d['origin']['generated_monotonic']==p['issued_at'] and d['observation_sampled_at']==wire['sampled_at'] and d['observation_native_tick']==wire['native_tick'] and d['observation_sequence']==index and d['command_sequence']==index
        lower,translation,turn=bounds(task,wire['body'],setup['known']);da=lower>=.22-1e-8 and translation<=.02+1e-8 and turn<=.1+1e-8;dp=dict(lower_m=lower,translation_m=translation,yaw_rad=turn)
        sa,sp=static_guard(setup['known'],wire['body'],v,w)
        assert c['dynamic_allowed']==da and c['dynamic_proof']==dp and c['static_allowed']==sa and c['static_proof']==sp
        applied=5 if da and sa else 0;assert c['applied_native']==applied
        for row in rows[c['before_native']:c['before_native']+applied]:
            assert row['delivery']==d and row['command_sequence']==index and row['raw_upstream_request']==[v,w,False]
            assert row['parked_target']==(state['parked_target'] if row['expiry_gate']['fresh'] else None)
            if row['parked_target'] is not None:
                assert row['request']==[0.,0.,False] and max(abs(x) for x in row['last_ctrl'][2:])<=1e-10
                body=row['body'];active=row['steering_motion_active_before']
                assert abs(body[3])<=(.01 if active else .003) and abs(body[4])<=(.16 if active else .003),'STEERING_MODE_MEASURED_ENTRY'
                previous=row['last_ctrl'];following=ctrl[row['before_native']]
                def center(front):
                    tangent=np.tan(front);k=[tangent[0]/(.6+.27*tangent[0]),tangent[1]/(.6-.27*tangent[1])]
                    assert abs(k[0]-k[1])<=1e-8
                    return math.atan(.6*sum(k)/2)
                assert abs(center(following[:2])-center(previous[:2]))<=.2*.01+1e-8 and max(abs(x) for x in following[2:])<=1e-10,'ORIGINAL_BOUNDED_COUPLED_STEERING_RATE'
        if applied==0:assert all(row['phase']=='COMPLETE_STOP_TAIL' and row['request']==[0.,0.,False] for row in rows[c['before_native']:])
    checks['measured_capture_controller_and_reserves']=True
    source=read(R/'runs/v1377_timed_handoff_witness/ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')
    assert source['coefficient_source_tick']==task['causal_source_tick']==32200 and source['source_polygon']==task['causal_all_future_polygon']
    certified=1e6;maximum_translation=maximum_turn=0.
    for row in rows[origin:]:
        i=row['before_native'];body=body_from_state(trace['qpos'][i],trace['qvel'][i]);lower,translation,turn=bounds(task,body,setup['known'])
        proof=row['post_step_causal_bound'];assert max(abs(proof['lower_m']-lower),abs(proof['translation_m']-translation),abs(proof['yaw_rad']-turn))<=1e-8
        certified=min(certified,lower);maximum_translation=max(maximum_translation,translation);maximum_turn=max(maximum_turn,turn)
        assert row['request']==[0.,0.,False] and max(abs(x) for x in ctrl[i,2:])<=1e-10,'RESPONSE_COMPONENT_MUST_NOT_DRIVE'
    checks['every_new_actual_pose_causal_all_future22cm']=certified>=.22-1e-8
    checks['whole_declared_coupled_envelope']=maximum_translation<=.02+1e-8 and maximum_turn<=.1+1e-8
    last=wires[-1];feedback=rows[last['native_tick']];_,_,state=controller.select(last['body'],last['native_tick'],feedback['encoders'],feedback['last_ctrl'])
    checks['ready_hold']=state['phase']=='RESPONSE_COMPLETE' and state['ready'] and last['native_tick']-state['ready_since']>=20
    def virtual(front):
        a,b=map(math.tan,front);return math.atan(.6*(a/(.6+.27*a)+b/(.6-.27*b))/2)
    change=abs(virtual(final['steering']['position'])-virtual(read(out/'COMPONENT_INITIAL_PACKET.json')['steering']['position']))
    checks['front_measured_change']=change>=.25
    assert abs(change-native['measured_virtual_front_angle_change_rad'])<=1e-8
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
        measured_virtual_front_angle_change_rad=change,maximum_body_translation_m=maximum_translation,maximum_body_yaw_change_rad=maximum_turn,scope='single coupled steering response, zero drive; not complete handoff or navigation')
