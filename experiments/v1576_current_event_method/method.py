"""Revision11 model description from one current candidate, no admission."""
import copy
import hashlib
import json

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def describe(candidate):
    clean=copy.deepcopy(candidate);identity=clean.pop('candidate_sha256')
    assert digest(clean)==identity and candidate['scientific_integration_revision']==11
    assert candidate['kind']=='CURRENT_CANONICAL_METHOD_CANDIDATE_NOT_ADMISSION'
    assert candidate['numerical_permission']is False and candidate['physical_permission']is False
    captured=candidate['current_source'];packet=captured['packet'];epoch=candidate['method_epoch']
    assert packet['native_tick']==epoch['epoch_native']==epoch['covered_native']==candidate['origin_native']
    assert epoch['steering_load_episode']is False and epoch['actual_sensor_claim']is False
    assert digest(captured)==epoch['origin_capture_sha256']
    source=dict(packet=copy.deepcopy(packet),fullstate=copy.deepcopy(captured['fullstate']),
        gear_memory=copy.deepcopy(captured['gear_memory']),mode_history=copy.deepcopy(captured['mode_memory']),
        causal_snapshot=copy.deepcopy(candidate['causal_snapshot']),
        causal_snapshot_sha256=candidate['causal_snapshot_sha256'],
        run_id=candidate['run_id'],source_role='CURRENT_EVENT_SOURCE_AWAITING_RUNTIME_RESOLVER',
        source_capture_sha256=digest(captured),physical_permission=False,models_authorized=False)
    source['input_sha256']=digest(source)
    base=dict(kind='REVISION11_CURRENT_EVENT_RESPONSE_INPUT',scientific_integration_revision=11,
        physical_source=source,physical_source_input_sha256=source['input_sha256'],
        fixed_origin_native=candidate['origin_native'],fixed_origin_sim_time=candidate['origin_sim_time'],
        method_memory=copy.deepcopy(epoch),causal_snapshot_sha256=candidate['causal_snapshot_sha256'],
        model_variant='V1159_BOUNDED_STEERING_LOAD_OVER_V1114',
        current_candidate_sha256=identity,capture_proof_sha256=candidate['capture_proof_sha256'],
        models_authorized=False,physical_permission=False)
    base['method_input_sha256']=digest(base)
    result=dict(base_method=base,base_method_semantic_sha256=base['method_input_sha256'],
        scientific_integration_revision=11,current_candidate_sha256=identity,
        registration_sha256=candidate['registration_sha256'],
        raw_schedule=copy.deepcopy(candidate['raw_schedule']),raw_schedule_sha256=candidate['raw_schedule_sha256'],
        fixed_boundaries=copy.deepcopy(candidate['fixed_boundaries']),
        geometry_kind='FULL_PERIOD_DISK',causal_snapshot_sha256=candidate['causal_snapshot_sha256'],
        current_and_prospective_stop_native=2200,minimum200_preserved=True,
        canonical_gear_per_native=True,extra_gear_hold_ticks=0,fixed_source_clock=True,
        model_variant=base['model_variant'],encoder_policy='MEASURED_ORIGIN_THEN_CURRENT_SCALAR_V1409_BRANCH_OWNED',
        actual_next_segment=copy.deepcopy(candidate['next_segment']),
        model_endpoint_required=copy.deepcopy(candidate['model_endpoint_required']),
        original_selector_reproduced=False,model_permission=False,physical_permission=False,
        model_evidence_is_not_fresh_command=True,whole_route_passed=False)
    result['response_method_sha256']=digest(result)
    return result
