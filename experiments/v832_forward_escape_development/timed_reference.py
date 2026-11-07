"""Finite-horizon time-labelled geometric reference; never a control certificate."""
import math
from types import MethodType
import numpy as np
from motion_tracker import future_boxes,paired_rectangle_clearance,SPEED
HORIZON=6.56
REFERENCE_SPEED=.20
SHIFT_TIME=.40
# Dense reference samples are at <=.008m and <=.04s intervals.
# This bounds relative displacement from a sample to the midpoint of its gap.
ROBOT_INTERPOLATION_PAD=.004*(1.+math.hypot(.44,.375)*math.tan(.42722137342572125)/.6)
ACTOR_PER_AXIS_TIME_PAD=SPEED*.02

def attach(field,state):
    field.temporal_state=None if state['center']is None else state
    def values(self,poses,times):
        p=np.asarray(poses,float).reshape(-1,3);t=np.asarray(times,float).reshape(-1);assert len(p)==len(t)and np.all(t>=-1e-10)
        out=self.pose_values(p)
        if self.temporal_state is None:return out
        near=t<=HORIZON+1e-10
        if np.any(near):
            lo,hi=future_boxes(self.temporal_state,t[near]);mid=(lo+hi)/2;half=(hi-lo)/2+1e-5+ACTOR_PER_AXIS_TIME_PAD
            dynamic=paired_rectangle_clearance(self,p[near],mid,half)-ROBOT_INTERPOLATION_PAD
            out[near]=np.minimum(out[near],dynamic)
        return out
    field.reference_values=MethodType(values,field)
    return field

def route_world(world,state):
    # world already has the CURRENT causal rectangle. It remains a conservative
    # static guide everywhere. Only the old all-future union rectangle is omitted.
    result=dict(world);result['sensor_points']=[]
    if state['center']is None:return result,{'status':'NO_DETECTION_NO_PROJECTION','hidden_world_geometry_used':False}
    return result,dict(status='TIME_LABELLED_CURRENT_OCCUPANCY_REFERENCE',horizon_s=HORIZON,reference_speed_m_s=REFERENCE_SPEED,gear_transition_reference_wait_s=SHIFT_TIME,dynamic_future_is_not_static_union=True,current_causal_rectangle_retained=True,beyond_horizon_is_uncertified_guidance=True,robot_interpolation_pad_m=ROBOT_INTERPOLATION_PAD,actor_per_axis_time_pad_m=ACTOR_PER_AXIS_TIME_PAD,hidden_world_geometry_used=False,scope='Proposed timing only; no waiting primitive or execution guarantee. All actual 328 native control admission remains separate.')

def scheduled_samples(path,times):
    path=np.asarray(path);times=np.asarray(times);poses=[];clock=[]
    assert len(path)==len(times)and np.all(np.diff(times)>0)
    for a,b,ta,tb in zip(path[:-1],path[1:],times[:-1],times[1:]):
        moving=.04/REFERENCE_SPEED;wait=max(0.,tb-ta-moving)
        if wait>1e-8:
            tt=np.linspace(ta,ta+wait,max(2,int(math.ceil(wait/.02))+1));poses.extend(np.repeat([a[:3]],len(tt),axis=0));clock.extend(tt)
        dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi
        for u in np.arange(1,6)/5.:
            poses.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy]);clock.append(ta+wait+u*(tb-ta-wait))
    return np.asarray(poses),np.asarray(clock)

def current_route_samples(path,index,current):
    section=np.asarray(path)[index:min(len(path),index+26)].copy()
    if len(section)==0:return np.asarray([current]),np.array([0.])
    route=np.vstack([np.r_[current,section[0,3]],section]);distance=np.linalg.norm(np.diff(route[:,:2],axis=0),axis=1);poses=[route[0,:3]];times=[0.];clock=0.
    for a,b,ds in zip(route[:-1],route[1:],distance):
        wait=SHIFT_TIME if a[3]!=b[3]else 0.
        if wait:
            tt=clock+np.linspace(0,wait,21);poses.extend(np.repeat([a[:3]],21,axis=0));times.extend(tt)
        dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi;n=max(1,int(math.ceil(ds/.008)),int(math.ceil(abs(dy)/.01)))
        for u in np.arange(1,n+1)/n:poses.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy]);times.append(clock+wait+u*ds/REFERENCE_SPEED)
        clock+=wait+ds/REFERENCE_SPEED
    return np.asarray(poses),np.asarray(times)
