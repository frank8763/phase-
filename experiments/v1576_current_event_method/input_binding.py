"""Revision11 current-origin candidate, never a live/numerical authority.

No model, estimator, optimizer, scan, state write or accepted old-schema method
is created. A complete new backend and independently qualified actual source
resolver must consume this candidate; old saved-M8 loaders cannot authorize it.
"""
import copy
import hashlib
import json
import math


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def candidate(captured,request,*,capture_proof,template,registration,registration_sha256):
    assert registration['revision']==11 and registration['previous_revision']==10
    assert registration['registered_before_new_accepted_domain_implementation']is True
    assert registration['models_authorized']is False and registration['physical_permission']is False
    assert digest(registration)==registration_sha256,'CURRENT_METHOD_REGISTRATION_CHANGED'
    assert captured['role']=='CAPTURED_SOURCE_ONLY_NOT_METHOD_INPUT'
    assert captured['numerical_permission']is False and captured['physical_permission']is False
    assert capture_proof['passed']is True and capture_proof['source_only']is True
    assert capture_proof['current_domain_qualified']is False
    assert request['event_index']==0 and request['event']['kind']=='CUSP_NEXT_SEGMENT_CHECK'
    packet=copy.deepcopy(captured['packet']);tick=packet['native_tick']
    assert type(tick)is int and tick>=250
    assert abs(packet['sim_time']-.01*tick)<=1e-8
    assert captured['fullstate']['time']==packet['sim_time']
    assert digest(captured['fullstate'])==request['actual']['evidence_state_sha256']
    assert digest(packet)==capture_proof['current_packet_sha256']
    assert captured['fullstate']==capture_proof['before_fullstate']
    assert capture_proof['fullstate_projection']['passed']is True
    assert capture_proof['canonical_receipt_content']['complete_prefix_native']==tick
    assert capture_proof['causal_content']['all_recorded_inputs_bound_to_actual_sent_wires']is True
    assert captured['mode_memory']['covered_native']==tick
    assert all(packet[k]==captured['mode_memory'][k]for k in ('coupled_episode','steering_motion_active','parked_target'))
    assert packet['steering_motion_active']is False and packet['parked_target']is None
    assert packet['steering']['native_tick']==tick
    assert packet['body_measured_at']==packet['steering']['measured_at']
    assert captured['gear_memory']['last_tick']==tick-1
    assert max(abs(x)for x in packet['body'][3:])<=.003
    assert max(abs(x)for x in packet['steering']['velocity'])<=.03
    assert max(abs(x)for x in packet['controller_memory']['last_ctrl'][2:])<=1e-10
    source=copy.deepcopy(captured['causal_source'])
    assert source==capture_proof['causal_source'] and source['covered_native']==tick
    assert source['run_id']==request['run_id'] and source['request_sha256']==request['request_sha256']
    assert source['snapshot_sha256']==digest(source['snapshot'])==request['causal_forecast']['coefficient_snapshot_sha256']
    assert template['scientific_integration_revision']==10
    clean=dict(template);identity=clean.pop('response_method_sha256')
    assert digest(clean)==identity,'EXPOSED_CATALOGUE_TEMPLATE_CHANGED'
    raw=copy.deepcopy(template['raw_schedule']);boundaries=copy.deepcopy(template['fixed_boundaries'])
    assert digest(raw)==template['raw_schedule_sha256']
    assert sum(row[2]for row in raw)==13600 and len(boundaries)==281
    assert raw[-1]==[0.,0.,2200,0] and template['current_and_prospective_stop_native']==2200
    assert template['geometry_kind']=='FULL_PERIOD_DISK'and template['extra_gear_hold_ticks']==0
    assert template['canonical_gear_per_native']is True and template['minimum200_preserved']is True
    target=copy.deepcopy(request['next_segment'])
    assert target['gear']in (-1,1)and len(target['poses'])>=2
    assert all(len(pose)==3 and all(type(v)in (int,float)and math.isfinite(v)for v in pose)for pose in target['poses'])
    # This is the disclosed method observer epoch, not an actual sensor field
    # and not a reset of plant/allocator/ModeMemory/gear. Later callbacks must
    # carry its durable applied-request chain; they may never reinstall False.
    method_epoch=dict(epoch_native=tick,covered_native=tick,steering_load_episode=False,
        actual_sensor_claim=False,single_entry_epoch=True,origin_capture_sha256=digest(captured))
    result=dict(kind='CURRENT_CANONICAL_METHOD_CANDIDATE_NOT_ADMISSION',schema=1,
        scientific_integration_revision=11,registration_sha256=registration_sha256,
        run_id=request['run_id'],event_index=0,request_sha256=request['request_sha256'],
        origin_native=tick,origin_sim_time=packet['sim_time'],current_source=copy.deepcopy(captured),
        capture_proof_sha256=digest(capture_proof),causal_snapshot=source['snapshot'],
        causal_snapshot_sha256=source['snapshot_sha256'],geometry_kind='FULL_PERIOD_DISK',
        method_epoch=method_epoch,exposed_catalogue_template_sha256=identity,
        raw_schedule=raw,raw_schedule_sha256=digest(raw),fixed_boundaries=boundaries,
        nominal_native=13600,complete_pairs=281,current_and_prospective_stop_native=2200,
        next_segment=target,model_endpoint_required=dict(rear_position_m=.12,heading_rad=.20),
        fixed_reference_required=dict(position_m=.02,heading_rad=.1,clock_ticks=20),
        original_selector_reproduced=False,old_controls_or_states_as_model_inputs=False,
        original_RPP_local_control_and_disclosed_shared_bridge=True,
        independently_qualified_actual_capture=False,complete_current_model_qualified=False,
        current_CPP_reserve_qualified=False,live_execution_qualified=False,
        numerical_permission=False,physical_permission=False,whole_route_passed=False)
    result['candidate_sha256']=digest(result)
    return result


def authorize_candidate(*args,**kwargs):
    raise RuntimeError('REVISION11_CURRENT_INPUT_FULL_BACKEND_AND_ACTUAL_LIFECYCLE_NOT_QUALIFIED')
