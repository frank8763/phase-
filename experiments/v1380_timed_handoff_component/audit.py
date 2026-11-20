"""Complete physical audit plus original response-model branch re-evaluation.

Run only through run_phase CPU2 single lock: analytical steps counted separately.
"""
import gzip
import math
import sys
import numpy as np
from component_context import *
from controller import Capture,errors
from geometry_contract import Geometry,membership
from gear_handoff import GearHandoff
from stamped_contract import before_step
sys.path.insert(0,str(R/'experiments/v1372_coherent_sampling_fault'))
from sampling_audit import state_body_audit,frame_audit,body_from_state


def audit(task):
    out=Path(task['output']);native=read(out/'RESULT.json');setup=read(out/'physics/SETUP.json');initial_packet=read(out/'INITIAL_PACKET.json');final=read(out/'FINAL_PACKET.json');rows=read(out/'APPLIED_JOURNAL.json');origin=32600
    with np.load(out/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k] for k in z.files}
    with gzip.open(out/'physics/SENSORS.json.gz','rt') as f:sensors=json.load(f)
    with gzip.open(out/'physics/CONTACTS.json.gz','rt') as f:contacts=json.load(f)
    n=len(rows);prefix_error=0.
    with np.load(Path(task['prior_raw'])/'physics/NATIVE_TRACE.npz') as z:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            if trace[k].size:prefix_error=max(prefix_error,float(abs(trace[k][:origin]-z[k][:origin]).max()))
    assert n>=origin and len(trace['time'])==n
    body_error=state_body_audit(trace,rows,initial_packet['body']);ctrl=trace['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
    checks=dict(full_recorded=n==native['actual_total_native']==native['own_replay_native'],exact_prefix=prefix_error<=1e-8 and read(out/'PREFIX_RESTORE.json')['passed'],full_body_feedback=body_error<=1e-8,
        separated_counts=native['historical_prefix_replay_native']==origin and native['new_component_native']==n-origin,
        original_model=setup['model_sha256']==read(Path(task['prior_raw'])/'physics/SETUP.json')['model_sha256'],
        finite=all(np.isfinite(trace[k]).all() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),actual_clearance=bool(trace['clearance'].min()>=.15-1e-8),self_margin=bool(trace['self_margin'].min()>=-1e-10),
        actual_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all() and (ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([initial_packet['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all()),
        no_bad_contacts=len(contacts)==n+1 and all(c[2] not in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact'] for row in contacts for c in row),
        own_replay=native.get('replay',{}).get('passed') is True and native['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8,
        complete_stop=all(z['applied'] and z['phase']=='COMPLETE_STOP_TAIL' and z['request']==[0.,0.,False] for z in rows[-200:]),
        measured_rest=max(abs(x) for x in final['body'][3:])<=.003,steering_rest=max(abs(x) for x in final['steering']['velocity'])<=.03,drive_zero=max(abs(x) for x in final['controller_memory']['last_ctrl'][2:])<=1e-10,
        root_guard=native['physical']['root_guard_native_count']==n,allocator=native.get('independent_allocation',{}).get('passed') is True,source_unchanged=native['source_unchanged'] and sources())
    gate=GearHandoff();selector=Capture(task);command_by_tick={c['before_native']:c for c in read(out/'CAPTURE_COMMANDS.json')};wires=read(out/'OBSERVATIONS_SENT.json')
    checks['all_wire_actual_scan_binding']=frame_audit(wires,sensors,rows,origin)
    geometry=Geometry(setup['known'],read(R/task['causal_model_file']));reference=read(R/task['response_reference_file'])['predicted_states'];minimum=math.inf;previous_ref=0
    for i,row in enumerate(rows):
        assert row['applied'] and row['before_native']==i
        if i in command_by_tick:
            c=command_by_tick[i];wire=wires[c['packet']['sequence']];assert wire['native_tick']==i
            v,w,state=selector.select(row['body'],i,row['encoders'],row['last_ctrl']);assert state==c['controller_state'] and [v,w]==[c['packet']['v'],c['packet']['w']]
            d=c['delivery'];assert d['observation_native_tick']==i and d['observation_sampled_at']==wire['sampled_at'] and d['command_sequence']==c['packet']['sequence']
            assert d['origin']['generated_monotonic']==c['packet']['issued_at'] and c['dynamic_allowed'] and c['static_allowed']
            actual_lower=geometry.actual(row['body'],i);assert abs(c['dynamic_proof']['lower_m']-actual_lower)<=1e-8
            assert c['applied_native']==5
            for x in rows[i:i+5]:assert x['delivery']==d and x['raw_upstream_request']==[v,w,False]
        vr,wr,p=gate.select(*row['upstream_request'][:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert row['request']==[vr,wr,False] and row['gear_handoff']==p
        if i>=origin:selector.observe_gear(i,p)
        if row['expiry_gate'] is not None:
            a,b,proof=before_step(*row['raw_upstream_request'][:2],row['delivery'],row['expiry_gate']['applied_monotonic']);assert row['upstream_request']==[a,b,False] and proof==row['expiry_gate'] and proof['fresh']
        if i>=origin:
            body=body_from_state(trace['qpos'][i],trace['qvel'][i]);lower=geometry.actual(body,i+1);minimum=min(minimum,lower);assert lower>=.22-1e-8 and abs(lower-row['post_step_causal_bound']['lower_m'])<=1e-8
            proof=membership(body,i+1,reference);assert row['response_membership']==proof and proof['reference_index']>=previous_ref;previous_ref=proof['reference_index']
    checks.update(all_gear_expiry_source_clock=True,actual_response_tube=True,all_actual_causal22=True)
    # Re-evaluate every original analytical braking branch from its exact actual
    # body/encoder/control-memory source, not from a supplied nominal state.
    sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
    from logic import Predictor,initial,kernel,Adapter
    proofs=read(out/'BRAKING_PROOFS.json');analytical=0;error=0.;low=math.inf
    with np.load(out/'BRAKING_ALTERNATIVES.npz') as z:
        states=z['states'];controls=z['ctrl']
        assert len(proofs)==len(states)==len(controls)==n-origin and native['analytical_native']==200*(n-origin)
        for index,proof in enumerate(proofs):
            assert time.time()<1795165200-10,'AUDIT_ROOT_CUTOFF'
            tick=origin+index;row=rows[tick];packet=proof['source_packet'];assert proof['before_native']==tick and packet['native_tick']==tick and packet['body']==row['body']
            assert packet['controller_memory']['last_ctrl']==row['last_ctrl'] and packet['controller_memory']['integral']==row['integral']
            assert packet['steering']['position']==row['encoders'][:2] and packet['steering']['velocity']==row['encoders'][2:]
            p=Predictor(setup,initial(packet),kernel.PARAMETERS);p.adapter.__class__=Adapter;p.adapter.parked_target=None
            error=max(error,float(abs(p.state-states[index,0]).max()))
            for k in range(200):
                s,u=p.step(0.,0.,False);analytical+=1;error=max(error,float(abs(s-states[index,k+1]).max()),float(abs(u-controls[index,k]).max()))
            lower=geometry.tube(states[index],tick);low=min(low,lower);assert abs(lower-proof['causal_tube_lower_m'])<=1e-8 and proof['passed'] and lower>=.22-1e-8
            assert abs(p.state[[3,4,5]]).max()<=.003 and abs(p.state[7])<=.03 and abs(p.adapter.last[2:]).max()<=1e-10
    checks['all_native_complete_braking_sources_recomputed']=error<=1e-8
    checks['braking_analysis_counted']=analytical==native['analytical_native']
    position,heading=errors(final['body'],task['target_segment']);checks.update(endpoint_position=position<=.12,endpoint_heading=heading<=.20,component_functional=native['passed'])
    repeat=None
    if task['role']=='repeat':
        base=Path(read(C/'TASKS.json')[0]['output']);repeat_error=0.
        with np.load(base/'physics/NATIVE_TRACE.npz') as z:
            assert len(z['time'])==n
            for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                if trace[k].size:repeat_error=max(repeat_error,float(abs(trace[k]-z[k]).max()))
        checks['full_repeat']=repeat_error<=1e-8;repeat=dict(full_state_ctrl_mocap_max_error=repeat_error,full_native_count=n)
    checks={k:bool(v) for k,v in checks.items()}
    return dict(passed=all(checks.values()),checks=checks,position_error_m=position,heading_error_rad=heading,minimum_causal_actual_clearance_m=minimum,
        minimum_complete_braking_tube_lower_m=low,response_model_recomputation_error=error,body_error=body_error,prefix_error=prefix_error,
        actual_total_native=n,historical_prefix_replay_native=origin,new_component_native=n-origin,own_replay_native=n,
        audit_analytical_native=analytical,models=0,new_physical_native=0,repeat=repeat,scope='fixed original32210 complete next-segment handoff; no original route or generalization')
