"""One real source event -> method12 description; no executable authority.

No old catalogue/refuge template, saved actuator controls or certificate is a
model input. Capture/provider runtime must be resolved by the actual owner.
"""
import copy
import hashlib
import json

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def describe(capture,request,proof,*,registration,registration_sha256,source_manifest_sha256,save_proof):
    diagnostic=dict(passed=False,first_error=None,models=0,physical_native=0,
        accepted_model_or_physical_permission=False,source_role='CURRENT_SEGMENT_METHOD_DESCRIPTION',
        old_saved_inputs_consumed=False)
    first=None;answer=None
    try:
        assert registration['revision']==12 and registration['previous_revision']==11
        assert registration['registered_before_method_implementation']is True
        assert registration['last_scientific_revision_in_current_authority']is True
        assert digest(registration)==registration_sha256
        assert capture['role']=='CAPTURED_SOURCE_ONLY_NOT_METHOD_INPUT'
        assert capture['physical_permission']is False and capture['numerical_permission']is False
        assert proof['passed']is True and proof['source_only']is True
        packet=capture['packet'];tick=packet['native_tick'];current=capture['causal_source']
        assert request['event_index']==0 and request['event']['kind']=='CUSP_NEXT_SEGMENT_CHECK'
        assert digest(packet)==proof['current_packet_sha256']
        assert capture['fullstate']==proof['before_fullstate']
        assert digest(capture['fullstate'])==request['actual']['evidence_state_sha256']
        assert proof['fullstate_projection']['passed']is True
        assert proof['canonical_receipt_content']['complete_prefix_native']==tick
        assert proof['causal_content']['all_recorded_inputs_bound_to_actual_sent_wires']is True
        assert proof['causal_source']==current and current['request_sha256']==request['request_sha256']
        assert current['run_id']==request['run_id']and current['covered_native']==tick
        assert current['snapshot_sha256']==digest(current['snapshot'])==request['causal_forecast']['coefficient_snapshot_sha256']
        assert capture['mode_memory']['covered_native']==tick and capture['gear_memory']['last_tick']==tick-1
        assert packet['coupled_episode']is False and packet['steering_motion_active']is False and packet['parked_target']is None
        assert max(abs(v)for v in packet['body'][3:])<=.003
        assert max(abs(v)for v in packet['steering']['velocity'])<=.03
        assert max(abs(v)for v in packet['controller_memory']['last_ctrl'][2:])<=1e-10
        assert type(tick)is int and abs(packet['sim_time']-.01*tick)<=1e-8
        assert packet['steering']['native_tick']==tick and packet['body_measured_at']==packet['steering']['measured_at']
        epoch=dict(epoch_native=tick,covered_native=tick,steering_load_episode=False,
            actual_sensor_claim=False,single_entry_epoch=True,origin_capture_sha256=digest(capture))
        physical=dict(packet=copy.deepcopy(packet),fullstate=copy.deepcopy(capture['fullstate']),
            mode_history=copy.deepcopy(capture['mode_memory']),gear_memory=copy.deepcopy(capture['gear_memory']),
            causal_snapshot=copy.deepcopy(current['snapshot']),causal_snapshot_sha256=current['snapshot_sha256'],
            source_role='CURRENT_CANONICAL_CAPTURE_AWAITING_ACTUAL_RUNTIME_RESOLVER',
            complete_capture_sha256=digest(capture),models_authorized=False,physical_permission=False)
        physical['input_sha256']=digest(physical)
        base=dict(kind='GOAL_BOUND_CURRENT_CANONICAL_EVENT_INPUT',scientific_integration_revision=12,
            fixed_origin_native=tick,fixed_origin_sim_time=packet['sim_time'],method_memory=epoch,
            physical_source=physical,causal_snapshot_sha256=current['snapshot_sha256'],
            current_event_request_sha256=request['request_sha256'],model_variant='V1159_BOUNDED_STEERING_LOAD_OVER_V1114',
            models_authorized=False,physical_permission=False)
        base['method_input_sha256']=digest(base)
        answer=dict(kind='DISCLOSED_GOAL_BOUND_SEGMENT_METHOD_NOT_ADMISSION',scientific_integration_revision=12,
            run_id=request['run_id'],event_index=0,base_method=base,base_method_semantic_sha256=base['method_input_sha256'],
            actual_next_segment=copy.deepcopy(request['next_segment']),
            segment_sha256=digest(request['next_segment']),geometry_kind='ORIGINAL_CAUSAL_TIME_POLYGONS',
            causal_snapshot_sha256=current['snapshot_sha256'],registration_sha256=registration_sha256,
            source_manifest_sha256=source_manifest_sha256,capture_proof_sha256=digest(proof),
            model_variant=base['model_variant'],policy=copy.deepcopy(registration['algorithm']),
            fixed_geometry=copy.deepcopy(registration['geometry']),
            original_selector_reproduced=False,original_RPP_system_claim=False,
            disclosed_shared_bridge=True,models_authorized=False,physical_permission=False,
            actual_capture_runtime_qualified=False,whole_route_passed=False)
        answer['response_method_sha256']=digest(answer)
        diagnostic.update(passed=True,response_method_sha256=answer['response_method_sha256'],
            source_capture_sha256=digest(capture),base_method_input_sha256=base['method_input_sha256'])
    except BaseException as error:first=repr(error);diagnostic['first_error']=first
    secondary=None
    try:save_proof(diagnostic)
    except BaseException as error:secondary=repr(error)
    if first or secondary:
        error=RuntimeError(first or 'CURRENT_SEGMENT_METHOD_SOURCE_PROOF_SAVE_REFUSED')
        error.proof=diagnostic;error.secondary=secondary;raise error
    return answer
