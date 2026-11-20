"""Proposed data-only observation-frame contract; not installed in a runner."""
import math

def needs_sample(sensor_tick,current_tick,sampled_at,now):
    assert type(current_tick) is int and current_tick>=0
    assert all(math.isfinite(x) for x in [sampled_at,now]) and now>=sampled_at
    return sensor_tick is None or sensor_tick!=current_tick or now-sampled_at>=.04

def validate_frame(scan,body_tick,sim_time,body):
    assert scan['native_tick']==body_tick,'SENSOR_NATIVE_TICK_MISMATCH'
    assert abs(scan['time']-sim_time)<=1e-8,'SENSOR_PHYSICAL_CLOCK_MISMATCH'
    assert len(body)==5 and len(scan['xy'])==2
    assert all(math.isfinite(x) for x in [*body,*scan['xy'],scan['yaw'],scan['time'],sim_time])
    assert max(abs(x-y) for x,y in zip(scan['xy'],body[:2]))<=1e-8,'SENSOR_POSE_MISMATCH'
    angle=abs(math.atan2(math.sin(scan['yaw']-body[2]),math.cos(scan['yaw']-body[2])))
    assert angle<=1e-6,'SENSOR_HEADING_MISMATCH'
    return True
