"""Bind an owner-held complete measured origin to one immutable cusp request."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def exact(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


event=exact('v1398_original_event_inputs',ROOT/'experiments/v1397_event_handoff_integration/route_event.py')
sys.path.insert(0,str(ROOT/'experiments/v1397_event_handoff_integration'))
import route_event as shared_event
assert Path(shared_event.__file__).resolve()==ROOT/'experiments/v1397_event_handoff_integration/route_event.py', 'CURRENT_EVENT_SOURCE_COLLISION'
field=exact('v1398_current_causal_bridge',ROOT/'experiments/v1397_event_handoff_integration/causal_bridge_field.py')


def bind(vehicle, request, mode_memory, causal_snapshot, *, gear, now):
    value=copy.deepcopy(request);identity=value.pop('request_sha256')
    assert event.digest(value)==identity, 'CURRENT_REQUEST_CHANGED'
    envelope=event.validate_envelope(request['actual'],run_id=request['run_id'],now=now,previous_sequence=-1)
    wire=envelope['wire'];feedback=envelope['feedback']
    assert vehicle.count==wire['native_tick'] and abs(float(vehicle.d.time)-wire['sim_time'])<=1e-8, 'OWNER_ADVANCED_AFTER_REQUEST'
    state={key:getattr(vehicle.d,key).tolist() for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')};state['time']=float(vehicle.d.time)
    assert hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==envelope['evidence_state_sha256'], 'OWNER_FULL_STATE_CHANGED'
    body=list(vehicle.body());encoders=vehicle.steering_sample().tolist()
    assert body==wire['body'] and encoders==feedback['encoders'], 'OWNER_MEASURED_FEEDBACK_CHANGED'
    assert vehicle.adapter.last.tolist()==feedback['last_ctrl'] and float(vehicle.adapter.integral)==feedback['integral'], 'OWNER_MEMORY_CHANGED'
    modes=mode_memory.snapshot(vehicle.count)
    active=bool(getattr(vehicle.adapter,'_steering_motion_active',False));parked=getattr(vehicle.adapter,'parked_target',None)
    assert active==modes['steering_motion_active']==feedback['steering_motion_active'], 'OWNER_MODE_CHANGED'
    assert parked==modes['parked_target']==feedback['parked_target'], 'OWNER_PARKED_TARGET_CHANGED'
    assert dict(gear=gear.gear,brake_start=gear.brake_start,last_tick=gear.last_tick)==feedback['gear_memory'], 'OWNER_GEAR_MEMORY_CHANGED'
    lateral=float(-vehicle.d.qvel[0]*math.sin(body[2])+vehicle.d.qvel[1]*math.cos(body[2]))
    assert math.isfinite(lateral) and abs(lateral)<=.03+1e-8, 'OWNER_LATERAL_CAP'
    bridge=field.all_future(causal_snapshot,current_native=vehicle.count,current_sim_time=float(vehicle.d.time))
    assert bridge['periodic_source_tick']==request['event']['source']['coefficient_tick'], 'OWNER_COEFFICIENT_SOURCE_CHANGED'
    assert event.digest(causal_snapshot)==request['causal_forecast']['coefficient_snapshot_sha256'], 'OWNER_COEFFICIENT_SNAPSHOT_CHANGED'
    origin=dict(body=body,body_lateral=lateral,native_tick=vehicle.count,sim_time=float(vehicle.d.time),
                body_measured_at=wire['sampled_at'],sent_at=now,
                steering=dict(position=encoders[:2],velocity=encoders[2:],native_tick=vehicle.count,measured_at=wire['sampled_at']),
                controller_memory=copy.deepcopy(dict(last_ctrl=feedback['last_ctrl'],integral=feedback['integral'])),
                coupled_episode=modes['coupled_episode'],steering_motion_active=active,parked_target=parked)
    result=dict(request_sha256=identity,full_state_sha256=envelope['evidence_state_sha256'],origin=origin,
                mode_history=modes,gear_memory=copy.deepcopy(feedback['gear_memory']),
                next_segment=copy.deepcopy(request['next_segment']),bridge_forecast=bridge,
                causal_snapshot_sha256=event.digest(causal_snapshot),physical_admission=False)
    result['input_sha256']=event.digest(result)
    return result
