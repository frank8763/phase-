"""Read-only acquisition at the native owner; no model imports/construction.

The full-state digest is evidence identity only. It is never a planning input.
Actual scan acquisition is delegated to the unchanged qualified SampleCache.
"""
import hashlib
import json
from route_event import frames, validate_envelope


def acquire(vehicle, cache, gear, *, run_id, sequence, now):
    wire = frames.wire_packet(cache, vehicle, run_id, sequence)
    state = {name: getattr(vehicle.d, name).tolist() for name in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat')}
    state['time'] = float(vehicle.d.time)
    # This digest leaves the actual arrays at the evidence owner.
    fingerprint = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    feedback = dict(native_tick=vehicle.count, sim_time=float(vehicle.d.time), body=list(vehicle.body()),
                    encoders=vehicle.steering_sample().tolist(), last_ctrl=vehicle.adapter.last.tolist(),
                    integral=float(vehicle.adapter.integral), parked_target=getattr(vehicle.adapter, 'parked_target', None),
                    steering_motion_active=bool(getattr(vehicle.adapter, '_steering_motion_active', False)),
                    gear_memory=dict(gear=gear.gear, brake_start=gear.brake_start, last_tick=gear.last_tick))
    value = dict(kind='ROUTE_ACTUAL_FRAME', wire=wire, feedback=feedback, evidence_state_sha256=fingerprint)
    return validate_envelope(value, run_id=run_id, now=now(), previous_sequence=sequence - 1)
