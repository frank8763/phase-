"""Complete saved-current/source/gear/clock/control/reference schema audit.

Saved-array checks do not add model integrations or substitute for original
Allocator recomputation, own fullstate replay or success-dependent repeat pair.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent


def exact(name,path,source):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source[str(path.relative_to(R))]
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def current_branches(folder,*,method,setup,geometry,fullstate,rows,source,check,method_memories):
    import numpy as np
    folder=Path(folder);module=exact('v1602_actual_stream_codec',C/'stream.py',source)
    gates=exact('v1602_original_current_complete_checks',C/'gates.py',source)
    projection=exact('v1602_actual_fullstate_coordinates',R/'experiments/v1528_fixed_we_evaluation_contract/origin_binding.py',source)
    digest=lambda v:hashlib.sha256(module.codec().encoded(v)).hexdigest()
    closed=json.loads((folder/'CURRENT_CLOSED.json').read_text());assert closed['closed']and not closed['failed']
    assert not closed['stream_write_inflight_unknown']and closed['pending_origin']is closed['pending_data']is closed['pending_actual_row']is None
    path=folder/'CURRENT.bin';assert path.stat().st_size==closed['stream_bytes']==closed['actual_stream_bytes']<=22*1024**2
    expected=[r for r in rows if 'source_packet'in r]
    origin=None;arrays=None;chain='0'*64;whole=hashlib.sha256();calls=0;minimum=float('inf')
    with path.open('rb')as stream:
        while True:
            check();header=stream.read(module.HEADER.size)
            if not header:break
            assert len(header)==module.HEADER.size;magic,mlen,plen=module.HEADER.unpack(header)
            assert magic==b'WE12AC01'and mlen<=16384 and plen<=8*1024**2
            meta=stream.read(mlen);payload=stream.read(plen);assert len(meta)==mlen and len(payload)==plen
            value=json.loads(meta)
            assert value['call_index']==calls and value['previous_chain_sha256']==chain
            assert value['response_method_sha256']==method['response_method_sha256']and value['payload_sha256']==hashlib.sha256(payload).hexdigest()
            kind=value['kind'];row=expected[calls]
            if kind=='ORIGIN':
                assert origin is None and arrays is None;origin=json.loads(payload);packet=origin['source_packet'];tick=packet['native_tick']
                assert packet==row['source_packet']and digest(packet)==row['source_packet_sha256']==origin['source_packet_sha256']
                actual={k:fullstate[k][tick]for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
                assert projection.compare(actual,packet,setup)['passed']
                assert origin['method_memory']['covered_native']==tick and origin['gear_memory']['last_tick']==tick-1
                assert origin['method_memory']['epoch_native']==method['base_method']['fixed_origin_native']
                assert origin['method_memory']==method_memories[tick]
            elif kind=='DATA':
                assert origin is not None and arrays is None and value['complete_native']==2200
                arrays=module.record_codec().decode(payload,value['arrays']);packet=origin['source_packet']
                assert int(arrays['native'][0])==packet['native_tick']
                assert np.max(abs(arrays['states'][0,[0,1,2,3,5]]-np.asarray(packet['body'])))<=1e-8
                assert abs(arrays['states'][0,4]-packet['body_lateral'])<=1e-8
                assert np.max(abs(arrays['memory'][0,:4]-packet['controller_memory']['last_ctrl']))<=1e-8
                assert abs(arrays['memory'][0,4]-packet['controller_memory']['integral'])<=1e-8
                assert np.max(abs(arrays['encoders'][0]-np.asarray([*packet['steering']['position'],*packet['steering']['velocity']])))<=1e-8
                assert arrays['modes'][0].tolist()==[int(packet['coupled_episode']),int(packet['steering_motion_active']),int(origin['method_memory']['steering_load_episode'])]
                gear=origin['gear_memory'];assert arrays['gear'][0].tolist()==[gear['gear'],gear['last_tick'],-1 if gear['brake_start']is None else gear['brake_start']]
            else:
                assert kind=='PROOF'and origin is not None and arrays is not None
                proof=json.loads(payload)
                recomputed=gates.evaluate(arrays,method,setup,geometry,expected_native=2200,zero_suffix=2200,raw_current_only=True)
                assert proof['passed']and recomputed['passed']and proof['full_checks']==recomputed['checks']
                assert abs(proof['causal_tube_lower_m']-recomputed['causal_tube_lower_m'])<=1e-8
                assert proof['source_packet_sha256']==row['source_packet_sha256']and proof['before_native']==row['before_native']
                minimum=min(minimum,recomputed['causal_tube_lower_m']);origin=None;arrays=None;calls+=1
            chain=hashlib.sha256(chain.encode()+meta+payload).hexdigest();whole.update(header+meta+payload)
    assert origin is None and arrays is None and calls==len(expected)==closed['current_branches']==closed['applied_receipts']
    assert chain==closed['last_chain_sha256']and whole.hexdigest()==closed['whole_stream_sha256']
    return dict(passed=True,current_complete2200_branches=calls,minimum_tube_m=minimum,
        model_integrations=0,saved_array_audit_not_fresh_model_replay=True)


def whole_goal(task,body,*,discovered,actual_travel_after_detection_m,final_rows):
    distance=math.dist(body[:2],task['goal_xy'])
    progress=sum((body[i]-task['start_xy'][i])*[math.cos(task['start_yaw']),math.sin(task['start_yaw'])][i]for i in (0,1))
    after=actual_travel_after_detection_m
    tail=final_rows[-200:]
    checks=dict(bodycenter_goal_045=distance<=.45,forward_75=progress>=7.5,
        actual_dynamic_discovery=discovered is True,after_discovery_1m=after is not None and after>=1.,
        complete200_actual_zero_tail=len(tail)==200 and all(r['applied']and r['request']==[0.,0.,False]for r in tail))
    return dict(passed=all(checks.values()),checks=checks,distance_m=distance,forward_m=progress,after_discovery_m=after,
        whole_gate_not_segment_gate=True)


def integrated(task,result,*,components,source,check):
    import gzip
    import numpy as np
    out=Path(task['output']);recorded=exact('v1602_new_integrated_rows',C/'recorded.py',source)
    rows,events,root=recorded.collect(out,source=source);n=len(rows)
    def arrays(path):
        with np.load(path,allow_pickle=False)as s:return {k:s[k].copy()for k in s.files}
    full=arrays(out/'FULL_STATE_NPLUS1.npz');trace=arrays(out/'physics/NATIVE_TRACE.npz')
    assert n==result['actual_native']and not result['actual_inflight_unknown']and n>0
    assert all(len(full[k])==n+1 for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat'))
    assert all(np.isfinite(a).all()for a in full.values())
    assert np.max(abs(full['time']-.01*np.arange(n+1)))<=1e-8
    assert all(np.array_equal(full[k][1:],trace[k])for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat'))
    assert np.array_equal(full['applied_ctrl'],full['ctrl'][1:])
    setup=json.loads((out/'physics/SETUP.json').read_text());ids=setup['actuator_ids']
    ctrl=full['ctrl'][1:,ids];limits=np.asarray(setup['limits']);rates=.01*np.asarray(setup['slew_per_second'])
    assert (ctrl>=limits[:,0]-1e-8).all()and(ctrl<=limits[:,1]+1e-8).all()
    assert(abs(np.diff(full['ctrl'][:,ids],axis=0))<=rates+1e-8).all()
    assert trace['clearance'].min()>=.15-1e-8 and trace['self_margin'].min()>=-1e-10
    with gzip.open(out/'physics/CONTACTS.json.gz','rt')as stream:contacts=json.load(stream)
    assert len(contacts)==n+1 and all(x[2]not in {'robot_obstacle_contact','robot_obstacle_penetration','robot_self_contact','unknown_contact'}for group in contacts for x in group)
    frames=exact('v1602_original_frame_binding',R/'experiments/v1396_rpp_rpc_retirement/frames.py',source)
    gear_module=exact('v1602_original_native_gear',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py',source)
    mode_module=exact('v1602_original_continuous_mode',R/'experiments/v1398_current_event_witness/mode_memory.py',source)
    scalar=exact('v1602_original_actual_coordinates',R/'experiments/v1429_native_scalar_event_audit/event_audit.py',source)
    command_module=exact('v1602_original_route_retirement',R/'experiments/v1479_retirement_scope_binding/route_command.py',source)
    sent={};retirements=[];gate=command_module.Commands(task['run_id'],retirement_sink=retirements.append)
    for event in root:
        check()
        if event['kind']in {'PUBLISHED_ACTUAL_ENVELOPE','CURRENT_SHARED_POLICY_DELIVERY'}:
            e=event['envelope'];wire=e['wire'];frames.validate_wire(wire)
            assert wire['sequence']not in sent and wire['run_id']==task['run_id'];sent[wire['sequence']]=wire
            tick=wire['native_tick'];state={k:full[k][tick].tolist()if hasattr(full[k][tick],'tolist')else full[k][tick]for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
            assert scalar.recorded.digest(state)==e['evidence_state_sha256']
        elif event['kind']=='RECEIVED_ACTUAL_ROUTE'and event['packet']['kind']=='command':
            gate.accept(event['packet'],sent,current_native=event['before_native'],now=event['received_monotonic'])
    saved_retirements=[e['retirement']for e in root if e['kind']=='RETIRED_ACTUAL_ROUTE']
    assert retirements==saved_retirements
    assert sorted(sent)==list(range(len(sent)))
    gear=gear_module.GearHandoff();modes=mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
    owners={}
    for i,row in enumerate(rows):
        check();state={k:full[k][i]for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
        body,lateral,enc=scalar.measured(state,setup)
        assert np.max(abs(np.asarray(row['body'])-body))<=1e-8 and np.max(abs(np.asarray(row['encoders'])-enc))<=1e-8
        upstream=row.get('upstream_request',row.get('raw_request'))
        vr,wr,proof=gear.select(*upstream[:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders'])
        assert row['request']==[vr,wr,False]and proof==row['gear_handoff']
        if 'mode_history'in row:assert row['mode_history']==modes.snapshot(i)
        modes.applied(before_native=i,v=vr,w=wr,parked_target=row['parked_target'],steering_motion_active_after=row['parked_target']is not None)
        owner=row['control_owner'];assert owner in {'ORIGINAL_RPP','DISCLOSED_SHARED_EXECUTION_BRIDGE','APPLIED_STOP_TAIL'}
        owners[owner]=owners.get(owner,0)+1
        if owner!='APPLIED_STOP_TAIL':
            delivery=row['delivery'];frames.validate_binding(delivery,sent)
            assert delivery['source_kind']=='ACTUAL_FRAME'and 0<=i-delivery['observation_native_tick']<5
            checked=row.get('source_checked_monotonic',row.get('expiry_gate',{}).get('applied_monotonic'))
            assert 0<=checked-delivery['origin']['generated_monotonic']<=.2 and 0<=checked-delivery['observation_sampled_at']<=.2
            if owner=='DISCLOSED_SHARED_EXECUTION_BRIDGE':assert delivery['origin']['kind']=='DISCLOSED_SHARED_SEGMENT_POLICY'
    epoch=exact('v1602_original_carried_method_epoch',R/'experiments/v1567_epoch_scope_target/method_memory.py',source)
    observed=[];memory=epoch.MethodMemory(components.method,save_receipt=observed.append)
    memory_rows=[event['receipt']for event in events if event['kind']=='METHOD_MEMORY']
    assert memory_rows and memory_rows[0]==observed[0]
    actual_rows=[row for row in rows if 'source_packet'in row];method_memories={}
    assert len(memory_rows)==len(actual_rows)+1
    for row,transition in zip(actual_rows,memory_rows[1:]):
        method_memories[row['before_native']]=memory.current()
        assert transition['applied_body']==row['request'][:2]and transition['source_packet_sha256']==row['source_packet_sha256']
        memory.applied(transition)
    current=current_branches(out/'goal_bound_actual',method=components.method,setup=setup,geometry=components.guard.geometry,
        fullstate=full,rows=rows,source=source,check=check,method_memories=method_memories)
    reference_module=exact('v1602_immutable_reference_audit',C/'reference.py',source)
    nominal=components.generation_reader.arrays('nominal')['states'];origin=components.method['base_method']['fixed_origin_native']
    reference=reference_module.FixedResponse(states=nominal.tolist(),origin_native=origin,
        origin_sim_time=components.method['base_method']['fixed_origin_sim_time'],expected_state_bytes_sha256=hashlib.sha256(nominal.tobytes()).hexdigest(),
        method_sha256=components.method['response_method_sha256'],nominal_native=components.proposal['nominal_native'])
    tracker_module=exact('v1602_actual_policy_audit',C/'tracker.py',source)
    tracker=tracker_module.SegmentTracker(components.method['actual_next_segment'],origin_body=components.method['base_method']['physical_source']['packet']['body'],
        origin_native=origin,origin_sim_time=components.method['base_method']['fixed_origin_sim_time'])
    after_events=[e for e in events if e['kind']=='AFTER_NATIVE'];assert len(after_events)==len(actual_rows)
    for offset in range(0,len(actual_rows),5):
        check();block=actual_rows[offset:offset+5];assert len(block)==5
        decision=None
        if offset<components.proposal['motion_native']:
            first=block[0];decision=tracker.select(first['body'],native_tick=first['before_native'],sim_time=first['source_packet']['sim_time'])
            assert not decision['terminal_requested']
            assert all(np.max(abs(np.asarray(row['raw_request'][:2])-decision['body_request']))<=1e-8 for row in block)
        receipts=[]
        for j,row in enumerate(block):
            i=row['before_native']+1;state={k:full[k][i]for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
            body,_,_=scalar.measured(state,setup);membership=reference.assess([float(v)for v in body],i)
            stored=row['response_membership'];assert membership['reference_index']==stored['reference_index']
            assert all(abs(membership[k]-stored[k])<=1e-8 for k in ('rear_error_m','yaw_error_rad','time_error_s'))
            receipt=copy.deepcopy(after_events[offset+j]);receipt['durable_receipt_sha256']=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();receipts.append(receipt)
        if decision is not None:tracker.commit(decision,applied_native=5,applied_request_receipts_sha256=hashlib.sha256(json.dumps(receipts,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest())
    allocation=result['independent_allocation'];replay=result['replay']
    assert allocation['passed']and allocation['recorded_rows']==n and allocation['allocator_recomputations']==n
    assert not allocation['allocator_recomputation_inflight_unknown']and allocation['maximum_memory_control_error']<=1e-8
    assert replay['passed']and replay['replay_native']==n and replay['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and replay['contact_mismatched_ticks']==0
    physical=result['physical'];body=physical['final_body']
    whole=whole_goal(task,body,discovered=physical['first_actor_detection']is not None,
        actual_travel_after_detection_m=physical['actual_travel_after_detection_m'],final_rows=rows)
    coverage_module=exact('v1602_original_offline_coverage',R/'experiments/v1370_overnight_controller_matrix/evaluate_coverage.py',source)
    coverage=coverage_module.evaluate(out,json.loads((out/'FORECAST_RECORDS.json').read_text()));assert coverage['passed']
    with gzip.open(out/'physics/SENSORS.json.gz','rt')as stream:sensors=json.load(stream)
    assert sensors and sensors[0]['native_tick']==0 and sensors[-1]['native_tick']==n
    assert len(rows)>=2200 and all(r['request']==[0.,0.,False]and r['control_owner']=='APPLIED_STOP_TAIL'for r in rows[-2200:])
    assert components.execution.closed and result['actual_goal_bound_segment_completed']and result['source_unchanged']
    return dict(passed=True,closed=True,current_branches=current,actual_native=n,control_owner_counts=owners,
        forecast_coverage=coverage,original_whole_goal=whole,scope='FIRST_GOAL_BOUND_SEGMENT_RUNTIME_ONLY',whole_route_passed=False,
        model_integrations=0,physical_native=0,pair_unexecuted=True)


def pair(first,second,*,np):
    assert set(first)==set(second)=={'time','qpos','qvel','ctrl','mocap_pos','mocap_quat','applied_ctrl'}
    errors={}
    for key in first:
        assert first[key].shape==second[key].shape and np.isfinite(first[key]).all()and np.isfinite(second[key]).all()
        errors[key]=float(np.max(abs(first[key]-second[key])))if first[key].size else 0.
    return dict(passed=max(errors.values())<=1e-8,maximum_error_by_field=errors,includes_canonical_t0=True,
        repeat_not_inferred_from_array_copy=True)
