"""Separate200 plan event; original250 CUSP contract remains exact."""
import copy
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'experiments/v1397_event_handoff_integration/route_event.py';s=importlib.util.spec_from_file_location('v1422_original_route_event',p);base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
validate_envelope=base.validate_envelope;digest=base.digest;finite_vector=base.finite_vector;math=base.math;contract=base.contract

def ordered_request(envelope, segment, geometry, forecast, *, run_id, event_index, brake_start, now, plan_index, ordered_segments, completed_bridge_events):
    measured = validate_envelope(envelope, run_id=run_id, now=now, previous_sequence=-1)
    wire = measured['wire']; feedback = measured['feedback']
    assert type(event_index) is int and event_index >= 0, 'EVENT_INDEX'
    assert type(brake_start) is int and 0 <= brake_start <= wire['native_tick'] - 200, 'PLAN_200_APPLIED_STOP_NOT_ESTABLISHED'
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
    event = dict(kind='ORDERED_ROUTE_FIRST_SEGMENT_CHECK', body=wire['body'], gear=segment['gear'], geometry=geometry,
                 source=dict(native_tick=wire['native_tick'], coefficient_tick=coefficient,
                             checked_monotonic=now, sampled_monotonic=wire['sampled_at']))
    classification=copy.deepcopy(event);classification['kind']='CUSP_NEXT_SEGMENT_CHECK'
    decision=contract.next_gate(classification)
    assert type(plan_index)is int and plan_index>=1 and type(completed_bridge_events)is int and completed_bridge_events>=1,'ORDERED_EVENT_NOT_AFTER_COMPLETED_BRIDGE'
    assert isinstance(ordered_segments,list)and ordered_segments and ordered_segments[0]==segment,'ORDERED_EVENT_WRONG_FIRST_SEGMENT'
    for left,right in zip(ordered_segments,ordered_segments[1:]):
        assert left['gear']!=right['gear']and left['poses'][-1]==right['poses'][0],'ORDERED_EVENT_SEGMENT_DISCONTINUITY'
    # Body rest alone is insufficient for parked steering or a gear release.
    if (max(abs(x) for x in feedback['encoders'][2:]) > .03
            or max(abs(x) for x in feedback['last_ctrl'][2:]) > 1e-10
            or feedback['steering_motion_active'] or feedback['parked_target'] is not None):
        decision = dict(decision, next_required_gate='COMPLETE_MEASURED_STOP_AND_STEERING_REST')
    result = dict(kind='CURRENT_ORDERED_ROUTE_CERTIFICATE_REQUEST', schema=1, event_contract='POST_BRIDGE_ORDERED_ROUTE_FIRST_SEGMENT_V1', stop_requirement_native=200, plan_index=plan_index, segment_index=0, ordered_segments_sha256=digest(ordered_segments), ordered_segments=copy.deepcopy(ordered_segments), completed_bridge_events=completed_bridge_events, run_id=run_id, event_index=event_index,
                  event=event, decision=decision, actual=measured, next_segment=copy.deepcopy(segment),
                  causal_forecast=copy.deepcopy(forecast), brake_start=brake_start,
                  historical_component_controls_reused=False, physical_admission=False, control_emitted=False)
    result['request_sha256'] = digest(result)
    return result


def validate_request(request):
    event=request['event'];kind=event['kind']
    common=dict(run_id=request['run_id'],event_index=request['event_index'],brake_start=request['brake_start'],now=event['source']['checked_monotonic'])
    if kind=='CUSP_NEXT_SEGMENT_CHECK':
        expected=base.make_request(request['actual'],request['next_segment'],event['geometry'],request['causal_forecast'],**common)
    else:
        assert kind=='ORDERED_ROUTE_FIRST_SEGMENT_CHECK','UNKNOWN_CURRENT_ROUTE_EVENT'
        assert request['event_contract']=='POST_BRIDGE_ORDERED_ROUTE_FIRST_SEGMENT_V1'and request['stop_requirement_native']==200 and request['segment_index']==0
        expected=ordered_request(request['actual'],request['next_segment'],event['geometry'],request['causal_forecast'],plan_index=request['plan_index'],ordered_segments=request['ordered_segments'],completed_bridge_events=request['completed_bridge_events'],**common)
    assert expected==request,'CURRENT_ROUTE_EVENT_CONTRACT_OR_SOURCE_CHANGED'
    return 250 if kind=='CUSP_NEXT_SEGMENT_CHECK'else 200
