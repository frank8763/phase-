"""One fixed speed-response profile; no model imports or ownership handoff."""
import math,time
import numpy as np
from whole_input import virtual

def execute(vehicle,plan,deadline):
    states=np.asarray(plan['state_path'],float);requests=np.asarray(plan['planned_body_requests'],float)
    assert plan['passed'] is True and states.shape==(501,8) and requests.shape==(500,3),'PROFILE_SHAPE'
    assert np.isfinite(states).all() and np.isfinite(requests).all(),'NONFINITE_PROFILE'
    assert np.all(requests[:300,0]==.08) and np.all(requests[300:]==0.) and np.all(requests[:,2]==0.),'FIXED_MOTION_AND_FULL_TAIL'
    assert np.all(abs(requests[:,1])<=.08*.758770385+1e-10),'STEERING_DOMAIN'
    start=np.asarray(vehicle.body());assert np.linalg.norm(start[:3]-states[0,:3])<=1e-8,'WRONG_INITIAL_POSE'
    maximum=np.zeros(3);history=[]
    for i,request in enumerate(requests):
        assert time.time()<deadline-60,'ABSOLUTE_STOP_RESERVE'
        vehicle.step(*request)
        body=np.asarray(vehicle.body());enc=vehicle.steering_sample();q=np.asarray(enc[:2])
        assert abs(body[3])<=.13 and abs(body[4])<=.16,'BODY_CAP'
        d=body[2]-states[i+1,2]
        errors=np.array([np.linalg.norm(body[:2]-states[i+1,:2]),abs(math.atan2(math.sin(d),math.cos(d))),abs(virtual(q)-states[i+1,6])])
        maximum=np.maximum(maximum,errors);assert np.all(errors<=[.01,.008,.015]),'HELDOUT_NATIVE_RESPONSE_ERROR'
        history.append([*body,*q,*errors])
    history=np.asarray(history);assert np.linalg.norm(history[-50:,3:5],axis=1).max()<=.03,'FULL_STOP_NOT_OBSERVED'
    displacement=float(np.linalg.norm(history[-1,:2]-states[0,:2]));assert displacement>=.15,'NO_PHYSICAL_SPEED_RESPONSE'
    return dict(passed=True,native_steps=500,maximum_position_m=float(maximum[0]),maximum_heading_rad=float(maximum[1]),maximum_virtual_steering_rad=float(maximum[2]),actual_displacement_m=displacement,complete_200_native_stop=True)
