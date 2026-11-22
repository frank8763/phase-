"""Same-input installation boundary, before current Engine construction.

No model, scan, state write, memory epoch or executable authority here. Private
success is a dependency; the separately admitted LiveGuard remains mandatory.
"""
import copy
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def checked_identity(value,key):
    clean=copy.deepcopy(value);identity=clean.pop(key)
    assert digest(clean)==identity,'INSTALL_CONTENT_IDENTITY_CHANGED:'+key
    return identity


def before_current_engine(context,native):
    method=context['method'];guard=context['guard'];proposal=context['proposal']
    identity=checked_identity(method,'response_method_sha256')
    base=method['base_method'];physical=base['physical_source']
    assert checked_identity(base,'method_input_sha256')==method['base_method_semantic_sha256']
    checked_identity(physical,'input_sha256')
    assert method['scientific_integration_revision']==base['scientific_integration_revision']==12
    assert method['models_authorized']is method['physical_permission']is False
    assert base['models_authorized']is base['physical_permission']is False
    assert physical['models_authorized']is physical['physical_permission']is False
    assert digest(method['actual_next_segment'])==method['segment_sha256']==proposal['segment_sha256']
    assert digest(physical['causal_snapshot'])==physical['causal_snapshot_sha256']==base['causal_snapshot_sha256']==method['causal_snapshot_sha256']
    assert method['geometry_kind']=='ORIGINAL_CAUSAL_TIME_POLYGONS'
    assert guard.method==method and guard.input_sha==identity
    guard.require_current_event_input(method)
    assert guard.phases_started==['CPP_PROPOSAL','CPP_GENERATION','PYTHON_AUDIT'] and guard.active_phase is None
    assert proposal==guard.proposal and proposal['passed'] and proposal['closed']
    assert proposal['motion_native']+2200==proposal['nominal_native']
    reader=context['generation_reader']
    assert reader.seal['generation_result_sha256']==guard.generation_result_sha256
    assert reader.seal['binding']['stage']=='CPP_GENERATION'
    assert reader.seal['binding']['response_method_sha256']==identity
    assert reader.seal['binding']['proposal_sha256']==guard.proposal_sha256
    tick=base['fixed_origin_native'];packet=physical['packet'];vehicle=native.vehicle
    assert type(tick)is int and tick==native.applied==vehicle.count==packet['native_tick']
    assert not native.bridge_started and not native.in_step
    assert Path(type(native).apply.__code__.co_filename).resolve()==R/'experiments/v1567_epoch_scope_target/native_step.py'
    assert Path(type(native).packet.__code__.co_filename).resolve()==R/'experiments/v1567_epoch_scope_target/native_step.py'
    assert base['fixed_origin_sim_time']==packet['sim_time']==float(vehicle.d.time)
    assert abs(packet['sim_time']-.01*tick)<=1e-8
    assert native.mode_memory.snapshot(tick)==physical['mode_history']
    assert dict(gear=native.gear.gear,last_tick=native.gear.last_tick,brake_start=native.gear.brake_start)==physical['gear_memory']
    assert physical['gear_memory']['last_tick']==tick-1
    assert context['geometry'] is guard.geometry
    assert context['geometry'].origin==tick and context['geometry'].end>=tick+proposal['nominal_native']+2200
    assert packet['body']==list(vehicle.body())
    assert packet['controller_memory']['last_ctrl']==vehicle.adapter.last.tolist()
    assert packet['controller_memory']['integral']==float(vehicle.adapter.integral)
    assert [*packet['steering']['position'],*packet['steering']['velocity']]==vehicle.steering_sample().tolist()
    return dict(passed=True,response_method_sha256=identity,origin_native=tick,
        strict2200_source=True,private_evidence_not_live_authority=True,
        actual_runtime_qualified=False,models_constructed=0,physical_native=0)
