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


def current_branches(folder,*,method,setup,geometry,fullstate,rows,source,check):
    import numpy as np
    folder=Path(folder);module=exact('v1577_actual_stream_codec',C/'stream.py',source)
    gates=exact('v1577_original_current_complete_checks',C/'gates.py',source)
    projection=exact('v1577_actual_fullstate_coordinates',R/'experiments/v1528_fixed_we_evaluation_contract/origin_binding.py',source)
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


def whole_goal(task,body,*,discovered,discovery_body,final_rows):
    distance=math.dist(body[:2],task['goal_xy'])
    progress=sum((body[i]-task['start_xy'][i])*[math.cos(task['start_yaw']),math.sin(task['start_yaw'])][i]for i in (0,1))
    after=None if discovery_body is None else math.dist(body[:2],discovery_body[:2])
    tail=final_rows[-200:]
    checks=dict(bodycenter_goal_045=distance<=.45,forward_75=progress>=7.5,
        actual_dynamic_discovery=discovered is True,after_discovery_1m=after is not None and after>=1.,
        complete200_actual_zero_tail=len(tail)==200 and all(r['applied']and r['request']==[0.,0.,False]for r in tail))
    return dict(passed=all(checks.values()),checks=checks,distance_m=distance,forward_m=progress,after_discovery_m=after,
        whole_gate_not_segment_gate=True)


def pair(first,second,*,np):
    assert set(first)==set(second)=={'time','qpos','qvel','ctrl','mocap_pos','mocap_quat','applied_ctrl'}
    errors={}
    for key in first:
        assert first[key].shape==second[key].shape and np.isfinite(first[key]).all()and np.isfinite(second[key]).all()
        errors[key]=float(np.max(abs(first[key]-second[key])))if first[key].size else 0.
    return dict(passed=max(errors.values())<=1e-8,maximum_error_by_field=errors,includes_canonical_t0=True,
        repeat_not_inferred_from_array_copy=True)
