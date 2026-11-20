"""Current-state cusp requests. Classification is never a driving permission.

The measured envelope, target segment and causal forecast are bound together.
Hashes identify evidence; they do not authenticate a sensor or certify dynamics.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def exact_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


frames = exact_module('v1397_actual_frames', ROOT / 'experiments/v1396_rpp_rpc_retirement/frames.py')
contract = exact_module('v1397_frozen_event', Path(__file__).with_name('event_contract.py'))
wire_contract = exact_module('v1397_original_wire_contract', ROOT / 'experiments/v1288_baseline_interface/contract.py')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def finite_vector(value, length):
    assert isinstance(value, list) and len(value) == length, 'MEASURED_VECTOR_SHAPE'
    assert all(type(x) in (int, float) and math.isfinite(x) for x in value), 'MEASURED_VECTOR_NONFINITE'


def validate_envelope(value, *, run_id, now, previous_sequence):
    assert set(value) == {'kind', 'wire', 'feedback', 'evidence_state_sha256'}, 'ROUTE_FRAME_KEYS'
    assert value['kind'] == 'ROUTE_ACTUAL_FRAME', 'ROUTE_FRAME_NOT_ACTUAL'
    wire = value['wire']
    frames.validate_wire(wire)
    wire_contract.observation({k: wire[k] for k in frames.CORE}, run_id=run_id, now=now, previous_sequence=previous_sequence)
    assert wire['run_id'] == run_id, 'ROUTE_FRAME_FOREIGN_RUN'
    assert type(wire['sequence']) is int and wire['sequence'] > previous_sequence, 'ROUTE_FRAME_SEQUENCE'
    assert type(wire['native_tick']) is int and wire['native_tick'] >= 0, 'ROUTE_FRAME_TICK'
    assert math.isfinite(now) and 0 <= now - wire['sampled_at'] <= .2, 'ROUTE_FRAME_EXPIRED'
    feedback = value['feedback']
    assert set(feedback) == {'native_tick', 'sim_time', 'body', 'encoders', 'last_ctrl', 'integral',
                             'parked_target', 'steering_motion_active', 'gear_memory'}, 'ROUTE_FEEDBACK_KEYS'
    assert feedback['native_tick'] == wire['native_tick'] and feedback['sim_time'] == wire['sim_time'], 'FEEDBACK_CLOCK_CHANGED'
    assert feedback['body'] == wire['body'], 'FEEDBACK_BODY_CHANGED'
    finite_vector(feedback['body'], 5)
    finite_vector(feedback['encoders'], 4)
    finite_vector(feedback['last_ctrl'], 4)
    assert type(feedback['integral']) in (int, float) and math.isfinite(feedback['integral']), 'FEEDBACK_INTEGRAL'
    assert type(feedback['steering_motion_active']) is bool, 'FEEDBACK_STEERING_MODE'
    target = feedback['parked_target']
    assert target is None or (type(target) in (int, float) and math.isfinite(target)), 'FEEDBACK_PARKED_TARGET'
    gear = feedback['gear_memory']
    assert set(gear) == {'gear', 'brake_start', 'last_tick'}, 'GEAR_MEMORY_KEYS'
    assert type(gear['gear']) is int and gear['gear'] in (-1, 0, 1), 'GEAR_MEMORY_SIGN'
    assert type(gear['last_tick']) is int and gear['last_tick'] == wire['native_tick'] - 1, 'GEAR_MEMORY_CLOCK'
    assert gear['brake_start'] is None or (type(gear['brake_start']) is int and 0 <= gear['brake_start'] <= wire['native_tick']), 'GEAR_MEMORY_BRAKE'
    h = value['evidence_state_sha256']
    assert isinstance(h, str) and len(h) == 64 and set(h) <= set('0123456789abcdef'), 'STATE_DIGEST_FORMAT'
    return copy.deepcopy(value)


def make_request(envelope, segment, geometry, forecast, *, run_id, event_index, brake_start, now):
    measured = validate_envelope(envelope, run_id=run_id, now=now, previous_sequence=-1)
    wire = measured['wire']; feedback = measured['feedback']
    assert type(event_index) is int and event_index >= 0, 'EVENT_INDEX'
    assert type(brake_start) is int and 0 <= brake_start <= wire['native_tick'] - 250, 'CUSP_250_APPLIED_STOP_NOT_ESTABLISHED'
    assert set(segment) == {'gear', 'poses'} and type(segment['gear']) is int and segment['gear'] in (-1, 1), 'NEXT_SEGMENT_GEAR'
    assert isinstance(segment['poses'], list) and len(segment['poses']) >= 2, 'NEXT_SEGMENT_EMPTY'
    for pose in segment['poses']:
        finite_vector(pose, 3)
    rear = [wire['body'][0] - .3 * math.cos(wire['body'][2]), wire['body'][1] - .3 * math.sin(wire['body'][2]), wire['body'][2]]
    first = segment['poses'][0]
    distance = math.dist(rear[:2], first[:2])
    heading = abs(math.atan2(math.sin(rear[2] - first[2]), math.cos(rear[2] - first[2])))
    assert abs(distance - geometry['start_distance_m']) <= 1e-8 and abs(heading - geometry['start_heading_rad']) <= 1e-8, 'GEOMETRY_WRONG_ACTUAL_START'
    assert forecast is not None, 'CURRENT_CAUSAL_FORECAST_REQUIRED'
    coefficient = forecast['periodic_source_tick']
    assert type(coefficient) is int and 0 <= coefficient <= forecast['native_tick'] <= wire['native_tick'], 'FUTURE_CAUSAL_FORECAST'
    assert forecast['sim_time'] <= wire['sim_time'] + 1e-8, 'FUTURE_FORECAST_CLOCK'
    finite_vector(forecast['center'], 2)
    assert type(forecast['radius_m']) in (int, float) and math.isfinite(forecast['radius_m']) and forecast['radius_m'] >= 0, 'FORECAST_RADIUS'
    event = dict(kind='CUSP_NEXT_SEGMENT_CHECK', body=wire['body'], gear=segment['gear'], geometry=geometry,
                 source=dict(native_tick=wire['native_tick'], coefficient_tick=coefficient,
                             checked_monotonic=now, sampled_monotonic=wire['sampled_at']))
    decision = contract.next_gate(event)
    # Body rest alone is insufficient for parked steering or a gear release.
    if (max(abs(x) for x in feedback['encoders'][2:]) > .03
            or max(abs(x) for x in feedback['last_ctrl'][2:]) > 1e-10
            or feedback['steering_motion_active'] or feedback['parked_target'] is not None):
        decision = dict(decision, next_required_gate='COMPLETE_MEASURED_STOP_AND_STEERING_REST')
    result = dict(kind='CURRENT_CUSP_CERTIFICATE_REQUEST', schema=1, run_id=run_id, event_index=event_index,
                  event=event, decision=decision, actual=measured, next_segment=copy.deepcopy(segment),
                  causal_forecast=copy.deepcopy(forecast), brake_start=brake_start,
                  historical_component_controls_reused=False, physical_admission=False, control_emitted=False)
    result['request_sha256'] = digest(result)
    return result


class CertificateRequired(RuntimeError):
    """The route hook preserves its request, then closes until a backend qualifies."""
    def __init__(self, request):
        self.request = copy.deepcopy(request)
        super().__init__('CURRENT_CUSP_BACKEND_NOT_YET_QUALIFIED:' + request['decision']['next_required_gate'])


def require_certificate(request, persist):
    expected = dict(request); expected.pop('request_sha256')
    assert digest(expected) == request['request_sha256'], 'CUSP_REQUEST_CHANGED'
    persist(copy.deepcopy(request))
    raise CertificateRequired(request)
