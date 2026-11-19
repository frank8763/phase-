"""Rate-limited NOMINAL Ackermann primitive, never a physical response model.

The original allocator/vehicle is unchanged. This representation removes the
instantaneous curvature switch; it cannot certify real tracking/braking time.
"""
import math
import numpy as np

WHEELBASE=.6
MAX_CURVATURE=.5
MAX_CENTER=math.atan(WHEELBASE*MAX_CURVATURE)
STEERING_RATE=.6


def generate(pose,speed,steering,desired_speed,desired_steering,duration,*,prior_gear=0,rest_native=0):
    assert len(pose)==3 and np.isfinite([*pose,speed,steering,desired_speed,desired_steering,duration]).all(),'NONFINITE_OR_SHAPE'
    assert abs(speed)<=.1+1e-8 and abs(desired_speed)<=.1+1e-8,'NOMINAL_SPEED_LIMIT'
    assert max(abs(steering),abs(desired_steering))<=MAX_CENTER+1e-10,'STEERING_LIMIT'
    assert duration>0 and abs(duration/.01-round(duration/.01))<1e-8,'PRIMITIVE_CLOCK'
    assert speed*desired_speed>=0,'SIGN_REVERSAL_NEEDS_MEASURED_REST'
    if desired_speed==0.:
        assert abs(desired_steering-steering)<1e-10,'ZERO_TWIST_CANNOT_ESTABLISH_PARKED_TARGET'
    gear=1 if desired_speed>0 else -1 if desired_speed<0 else 0
    assert prior_gear in [-1,0,1] and type(rest_native) is int and rest_native>=0
    if gear and prior_gear and gear!=prior_gear:assert abs(speed)<=.003 and rest_native>=200,'GEAR200_AND_REST_REQUIRED'
    x,y,yaw=map(float,pose);delta=float(steering);v=float(speed);rows=[[x,y,yaw,0.,v,delta]]
    for step in range(1,round(duration/.01)+1):
        rate=.05 if abs(desired_speed)<abs(v) else .1
        following_v=v+float(np.clip(desired_speed-v,-rate*.01,rate*.01))
        following_delta=delta+float(np.clip(desired_steering-delta,-STEERING_RATE*.01,STEERING_RATE*.01))
        distance=.005*(v+following_v);k=math.tan((delta+following_delta)/2)/WHEELBASE;angle=yaw+distance*k
        if abs(k)>1e-10:x+=(math.sin(angle)-math.sin(yaw))/k;y-=(math.cos(angle)-math.cos(yaw))/k
        else:x+=distance*math.cos(yaw);y+=distance*math.sin(yaw)
        yaw=angle;v=following_v;delta=following_delta;rows.append([x,y,yaw,step*.01,v,delta])
    return np.asarray(rows)


def physical_ready(*,response_envelope,full_route_reviewed):
    # No qualified envelope has been obtained in this batch. Keep this explicit
    # rather than silently substituting a nominal mathematical trajectory.
    return bool(response_envelope and response_envelope.get('actual_controls_and_timing_qualified') is True and full_route_reviewed is True)
