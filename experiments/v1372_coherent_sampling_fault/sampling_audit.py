"""Independent full-state and actual-sensor audit, without model imports."""
import gzip
import math
import numpy as np
from component_context import *
from gear_handoff import GearHandoff
from stamped_contract import assess_delivery,validate_delivery,before_step

def lines(path):return [json.loads(s) for s in path.read_text().splitlines()]

def body_from_state(q,v):
    yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    return [float(q[0]),float(q[1]),yaw,float(v[0]*math.cos(yaw)+v[1]*math.sin(yaw)),float(v[5])]

def state_body_audit(trace,journal,initial_body):
    maximum=0.
    for i,row in enumerate(journal):
        expected=initial_body if i==0 else body_from_state(trace['qpos'][i-1],trace['qvel'][i-1])
        maximum=max(maximum,float(np.max(abs(np.asarray(row['body'])-expected))))
    assert maximum<=1e-8,'JOURNAL_BODY_DIFFERS_FROM_NATIVE_STATE'
    return maximum

def frame_audit(wires,sensors,journal,origin):
    actual={}
    for sensor in sensors:actual.setdefault(sensor['native_tick'],[]).append(sensor)
    for i,w in enumerate(wires):
        assert w['sequence']==i and w['native_tick']>=origin,'OBSERVATION_SEQUENCE'
        tick=w['native_tick'];f=w['sensor_frame']
        assert tick in actual,'ACTUAL_SENSOR_MISSING'
        assert any(s['ranges']==w['ranges_m'] and s['time']==f['time'] and s['xy']==f['xy'] and s['yaw']==f['yaw'] for s in actual[tick]),'ACTUAL_SCAN_CHANGED'
        assert f['native_tick']==tick and f['sampled_at']==w['sampled_at'],'FRAME_TICK_OR_AGE_CHANGED'
        assert abs(w['sim_time']-f['time'])<=1e-8,'FRAME_CLOCK_CHANGED'
        assert np.max(abs(np.asarray(w['body'])-journal[tick]['body']))<=1e-8,'FRAME_BODY_CHANGED'
        assert max(abs(x-y) for x,y in zip(f['xy'],w['body'][:2]))<=1e-8
        assert abs(math.atan2(math.sin(f['yaw']-w['body'][2]),math.cos(f['yaw']-w['body'][2])))<=1e-6
        assert math.isfinite(w['sampled_at'])
        if i:
            assert w['sampled_at']>=wires[i-1]['sampled_at']
            if tick!=wires[i-1]['native_tick']:assert w['sampled_at']>wires[i-1]['sampled_at'],'STALE_SCAN_ACQUISITION'
    return True

def audit(task):
    out=Path(task['output']);origin=task['origin_native_tick'];result=read(out/'RESULT.json');peer=read(out/'ROS_RESULT.json')
    setup=read(out/'physics/SETUP.json');initial=read(out/'INITIAL_PACKET.json');final=read(out/'FINAL_PACKET.json')
    component=read(out/'COMPONENT_INITIAL_PACKET.json');journal=read(out/'APPLIED_JOURNAL.json')
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k].copy() for k in z.files}
    with gzip.open(out/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    with gzip.open(out/'physics/CONTACTS.json.gz','rt') as f:contacts=json.load(f)
    n=len(trace['time']);maximum=0.;original=Path(task['prior_raw'])
    with np.load(original/'physics/NATIVE_TRACE.npz') as z:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            if trace[k].size:maximum=max(maximum,float(abs(trace[k][:origin]-z[k][:origin]).max()))
    ctrl=trace['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    body_error=state_body_audit(trace,journal,initial['body'])
    checks=dict(full_recorded=n==len(journal)==result['actual_total_native']==result['own_replay_native'],
        full_feedback_body_matches_native_state=body_error<=1e-8,
        historical_exact=maximum<=1e-8 and read(out/'PREFIX_RESTORE.json')['passed'],
        correct_separate_counts=result['historical_prefix_replay_native']==origin and result['new_component_native']==225 and n==origin+225,
        original_model=setup['model_sha256']==read(original/'physics/SETUP.json')['model_sha256'],
        full_clearance=bool(trace['clearance'].min()>=.15-1e-8),self_margin=bool(trace['self_margin'].min()>=-1e-10),
        full_finite=all(np.isfinite(trace[k]).all() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),
        full_native_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),
        legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all() and (ctrl<=limits[:,1]+1e-10).all()),
        legal_slew=bool((abs(np.diff(np.vstack([initial['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()),
        no_bad_contacts=len(contacts)==n+1 and all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
        full_own_replay=result.get('replay',{}).get('passed') is True and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        root_guard_count=result['physical']['root_guard_native_count']==n,
        independent_allocation=result.get('independent_allocation',{}).get('passed') is True,
        complete_stop_tail=all(z['phase']=='COMPLETE_STOP_TAIL' and z['request']==[0.,0.,False] for z in journal[-200:]),
        origin_matches=component['native_tick']==origin and np.max(abs(np.asarray(component['body'])-task['origin_body']))<=1e-8,
        final_rest=max(abs(x) for x in final['body'][3:])<=.003,
        steering_rest=max(abs(x) for x in final['steering']['velocity'])<=.03,
        drive_zero=max(abs(x) for x in final['controller_memory']['last_ctrl'][2:])<=1e-10,
        sources_unchanged=result['source_unchanged'] and sources(),peer_closed=peer['closed'] and peer['no_physical_modules_loaded'])
    gate=GearHandoff()
    for i,row in enumerate(journal):
        assert row['before_native']==i and row['applied']
        v,w,p=gate.select(*row['upstream_request'][:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert row['request']==[v,w,False] and row['gear_handoff']==p,'GEAR_PROOF_CHANGED'
    checks['full_gear_audit']=True
    wires=lines(out/'OBSERVATIONS_SENT.jsonl');checks['every_wire_actual_sensor_body_clock']=frame_audit(wires,sensors,journal,origin)
    wire_by_seq={w['sequence']:w for w in wires};received=lines(out/'RECEIVED_COMMANDS.jsonl');commands=read(out/'ROS_COMMANDS.json')
    assert commands==lines(out/'ROS_COMMANDS.jsonl') and len(commands)==len(received)==5,'COMMAND_EVIDENCE_INCOMPLETE'
    for index,event in enumerate(received):
        c=event['packet'];assert c==commands[index] and c['sequence']==index and c['v']==c['w']==0.
        w=wire_by_seq[c['observation_sequence']]
        assert c['observation_native_tick']==w['native_tick'] and c['observation_sampled_at']==w['sampled_at']
        d=assess_delivery(c,event['decision']['receipt_monotonic'],run_id=task['run_id'],previous_sequence=index-1)
        assert d==event['decision'] and event['before_native']==origin+index*5
        assert d['reason']==('OBSERVATION_EXPIRED' if index<4 else None)
        for row in journal[origin+index*5:origin+(index+1)*5]:
            assert row['upstream_request']==[0.,0.,False]
            if index<4:assert row['phase']=='FRESHNESS_BRAKE_HOLD' and row['freshness_rejection_index']==index
            else:
                delivery=validate_delivery(c,row['delivery']['validated_monotonic'])
                v,w,p=before_step(0.,0.,delivery,row['expiry_gate']['applied_monotonic'])
                assert delivery==row['delivery'] and p==row['expiry_gate'] and row['upstream_request']==[v,w,False]
    checks['four_real_expired_then_one_fresh']=True
    checks['all_fast_brake_ticks_have_real_scans']={origin+i*5 for i in range(6)}<=set(s['native_tick'] for s in sensors)
    checks['component_functional']=result['passed'] and peer['passed']
    return dict(passed=all(checks.values()),checks=checks,models=0,new_physical_native=0,
        actual_total_native=n,historical_prefix_replay_native=origin,new_component_native=n-origin,
        own_replay_native=n,original_prefix_max_error=maximum,full_body_state_error=body_error,scope='sampling fault only; zero goal navigation')
