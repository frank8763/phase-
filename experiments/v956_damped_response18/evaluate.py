"""Full response/handoff array evaluation, with no simulator imports or side effects."""
import math
import numpy as np


def response_expected(origin,v,w):
    t=np.minimum(np.arange(1,221)*.01,.2);a=origin[2]+w*t
    if abs(w)<1e-10:x=origin[0]+v*t*math.cos(origin[2]);y=origin[1]+v*t*math.sin(origin[2])
    else:x=origin[0]+v/w*(np.sin(a)-math.sin(origin[2]));y=origin[1]-v/w*(np.cos(a)-math.cos(origin[2]))
    return np.c_[x,y,a]


def evaluate(data,servo,origin,task,handoff=False):
    data=np.asarray(data,float);servo=np.asarray(servo,float);origin=np.asarray(origin,float)
    assert data.shape==((1800,5)if handoff else(420,5))and servo.shape==((1800,4)if handoff else(420,4))
    assert np.isfinite(data).all()and np.isfinite(servo).all()and np.isfinite(origin).all()
    if handoff:
        actual=data[400:1800];t=np.minimum(np.arange(1,1401)*.01,12.)
        expected=np.c_[origin[0]+.1*t*math.cos(origin[2]),origin[1]+.1*t*math.sin(origin[2]),np.full(len(t),origin[2])]
        bound=.04
    else:
        actual=data[200:];expected=response_expected(origin,*task['command'])
        bound=.04 if task['command'][0]*origin[3]<0 else .02
    assert actual.shape==expected.shape[:1]+(5,) and expected.shape[1]==3
    position=float(np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1).max())
    angle=float(abs(np.arctan2(np.sin(actual[:,2]-expected[:,2]),np.cos(actual[:,2]-expected[:,2]))).max())
    checks=dict(bounded_position=position<=bound,bounded_rotation=angle<=.035,
        measured_speed_bound=float(abs(data[:,3]).max())<=.13,measured_yaw_bound=float(abs(data[:,4]).max())<=.16,
        settled_by_half_second=bool(abs(data[(1649 if handoff else 269):,3:5]).max()<=.03),
        final_measured_steering_neutral=bool(abs(servo[-1,:2]).max()<=.01 and abs(servo[-1,2:]).max()<=.03))
    if handoff:
        checks['actual_progress']=float((data[1599,:2]-origin[:2])@[math.cos(origin[2]),math.sin(origin[2])])>=1.
    return dict(checks={k:bool(v)for k,v in checks.items()},position_residual_max_m=position,position_bound_m=bound,
        angle_residual_max_rad=angle,evaluated_samples=len(actual)),expected
