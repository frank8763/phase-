"""Select the next required certificate from current evidence, never issue control."""
import math
def next_gate(event):
    assert event['kind']=='CUSP_NEXT_SEGMENT_CHECK' and event['gear'] in (-1,1)
    body=event['body'];assert len(body)==5 and all(math.isfinite(x) for x in body)
    source=event['source'];assert type(source['native_tick']) is int and type(source['coefficient_tick']) is int
    assert source['coefficient_tick']<=source['native_tick'] and 0<=source['checked_monotonic']-source['sampled_monotonic']<=.2,'CAUSE_OR_FRESHNESS'
    assert all(math.isfinite(source[k]) for k in ('checked_monotonic','sampled_monotonic'))
    geometry=event['geometry'];position=geometry['start_distance_m'];yaw=geometry['start_heading_rad']
    assert all(math.isfinite(x) and x>=0. for x in (position,yaw))
    if max(abs(x) for x in body[3:])>.003:gate='COMPLETE_MEASURED_STOP'
    elif position>.12 or yaw>.20:gate='MEASURED_POSE_CAPTURE_CERTIFICATE'
    elif geometry.get('minimum_clearance_m',-math.inf)<.22:gate='CAUSAL_TIMED_NEXT_SEGMENT_CERTIFICATE'
    else:gate='CURRENT_STATE_BRAKING_AND_RPP_ADMISSION'
    return dict(next_required_gate=gate,physical_admission=False,control_emitted=False,fixed_tick_rescue=False)
