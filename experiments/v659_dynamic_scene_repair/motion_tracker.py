"""Causal one-object development tracker. No simulator geometry/trajectory reads."""
from collections import deque
from types import MethodType,SimpleNamespace
import numpy as np
from range_circle_memory import measured_rays,known_filter
from multi_circle_memory import components

class Tracker:
    def __init__(self):self.frames=deque(maxlen=16);self.center=None;self.velocity=np.zeros(2);self.last_time=None
    def update(self,env,rect,circ,step):
        rays=measured_rays(env);points=rays[:,:2]+(rays[:,4,None]-.04)*rays[:,2:4]
        points=points[known_filter(points,rect,circ)]
        now=float(env.data.time);observed=False
        clusters=[ids for ids in components(points,.25)if len(ids)>=1]
        if clusters:
            if self.center is None:ids=max(clusters,key=len)
            else:ids=min(clusters,key=lambda ids:float(np.linalg.norm(points[ids].mean(axis=0)-self.center)))
            surface=points[ids].mean(axis=0);direction=surface-np.asarray(env.robot_xy);direction/=max(np.linalg.norm(direction),1e-9)
            center=surface+.08*direction
            if self.center is None or np.linalg.norm(center-self.center)<=.7:
                self.frames.append((now,center));self.center=center;self.last_time=now;observed=True
                if len(self.frames)>=4:
                    t=np.array([x[0]for x in self.frames]);p=np.array([x[1]for x in self.frames]);t-=t.mean()
                    velocity=(t[:,None]*(p-p.mean(axis=0))).sum(axis=0)/max(float(t@t),1e-9)
                    speed=np.linalg.norm(velocity);self.velocity=velocity*min(1.,.12/max(speed,1e-9))
        age=0. if self.last_time is None else now-self.last_time
        if self.center is None:circles=[]
        else:circles=[[*self.center,.22+.12*age]]
        state={'center':None if self.center is None else self.center.tolist(),'velocity':self.velocity.tolist(),
               'age_s':age,'observed_this_frame':observed,'retained_frames':len(self.frames),
               'time':now,'hidden_world_geometry_used':False,'scope':'one-object empirical causal range tracker; not calibrated'}
        return circles,state

def install_time_gate(field,state,mode,known_circles):
    from exact_footprint import pose_values
    static=SimpleNamespace(half=field.half,center_local=field.center_local,rectangles=field.rectangles,
             circles=np.asarray(known_circles).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=field.config)
    center=None if state['center']is None else np.asarray(state['center']);velocity=np.asarray(state['velocity']);age=state['age_s']
    def trajectory_values(self,poses,dt):
        values=pose_values(static,poses)
        if center is None:return values
        p=np.asarray(poses);times=np.arange(1,len(p)+1)*dt
        if mode=='instant':future=np.broadcast_to(center,(len(p),2));radius=np.full(len(p),.22+.12*age)
        else:
            future=center+times[:,None]*velocity
            radius=.22+.12*age+.04*times+.03*times**2
        delta=future-p[:,:2];c=np.cos(p[:,2]);s=np.sin(p[:,2]);local=np.c_[delta[:,0]*c+delta[:,1]*s,-delta[:,0]*s+delta[:,1]*c]
        residual=abs(local-self.center_local)-self.half
        distance=np.where(residual.max(axis=1)<=0,residual.max(axis=1),np.linalg.norm(np.maximum(residual,0),axis=1))-radius
        return np.minimum(values,distance)
    field.trajectory_values=MethodType(trajectory_values,field)
