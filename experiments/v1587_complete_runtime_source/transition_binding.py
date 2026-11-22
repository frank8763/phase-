"""Bind durable applied receipts and method memory to canonical actual N+1.

No model imports, integration, FFI or numerical expected-state input. Caller
must already validate complete actual-array shapes and the source manifest.
"""
import copy
import hashlib
import json


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):return hashlib.sha256(encoded(value)).hexdigest()


def fullstate_at(fullstate,tick):
    result={}
    for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):
        value=fullstate[key][tick]
        result[key]=value.tolist()if hasattr(value,'tolist')else copy.deepcopy(value)
    result['time']=float(fullstate['time'][tick])
    return result


def verify(*,fullstate,rows,events,method,check):
    actual=[row for row in rows if 'source_packet'in row]
    before=[];after=[];memory=[];pending=None
    for event in events:
        check();kind=event['kind']
        if kind=='BEFORE_NATIVE':
            assert pending is None,'APPLIED_TRANSITION_OVERLAP'
            pending=event;before.append(event)
        elif kind=='AFTER_NATIVE':
            assert pending is not None,'APPLIED_TRANSITION_WITHOUT_BEFORE'
            assert event['row']['before_native']==pending['row']['before_native']
            after.append(event);pending=None
        elif kind=='METHOD_MEMORY':
            memory.append(event['receipt'])
    assert pending is None and len(before)==len(after)==len(actual)
    assert len(memory)==len(actual)+1 and actual,'APPLIED_TRANSITION_COVERAGE'
    origin=method['base_method']['fixed_origin_native']
    assert memory[0]['kind']=='DECLARED_OBSERVER_ENTRY_METHOD_EPOCH'
    assert memory[0]['epoch_native']==memory[0]['covered_native']==origin
    assert memory[0]['response_method_sha256']==method['response_method_sha256']
    for row,before_event,after_event,transition in zip(actual,before,after,memory[1:]):
        check();tick=row['before_native']
        assert type(tick)is int and 0<=tick<len(rows)
        assert after_event['row']==row and row['applied']is True
        initial=copy.deepcopy(row);initial['applied']=False
        assert before_event['row']==initial
        identity=digest(initial)
        assert before_event['source_row_sha256']==after_event['source_row_sha256']==identity
        assert after_event['after_native']==after_event['root_native_count']==tick+1
        assert after_event['contact_records']==tick+2,'ACTUAL_CONTACT_PREFIX_COVERAGE'
        before_sha=digest(fullstate_at(fullstate,tick))
        after_sha=digest(fullstate_at(fullstate,tick+1))
        assert row['source_full_state_sha256']==before_sha
        assert after_event['after_full_state_sha256']==after_sha
        assert transition['source_full_state_sha256']==before_sha
        assert transition['after_full_state_sha256']==after_sha
        assert row['source_packet']['native_tick']==tick
        assert transition['source_packet_sha256']==row['source_packet_sha256']==digest(row['source_packet'])
        assert transition['actual_receipt_sha256']==digest(after_event)
        assert transition['before_native']==tick and transition['after_native']==tick+1
        assert transition['epoch_native']==origin
        assert transition['response_method_sha256']==method['response_method_sha256']
        assert transition['applied_body']==row['request'][:2]
        assert transition['parked_target']==row['parked_target']
    assert [r['before_native']for r in actual]==list(range(origin,origin+len(actual)))
    return dict(passed=True,source_only_array_audit=True,applied_transitions=len(actual),
        canonical_before_after_fullstate_bound=True,actual_receipts_bound=True,
        model_integrations=0,physical_native=0,actual_runtime_qualification_inferred=False)
