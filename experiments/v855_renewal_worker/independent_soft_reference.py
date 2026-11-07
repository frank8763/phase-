"""Independent public-box geometry and soft reachability cost; no online helpers."""
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
from independent_time_reference import field

def soft_values(f,state,poses,renewal=False):
    p=np.asarray(poses,float).reshape(-1,3);answer=np.zeros(len(p))
    if state['center']is None:return answer
    pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper'])
    vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper'])
    for dt in np.arange(7)*6.56/6:
        lo=np.maximum(pl+dt*vl-.02*dt*dt,pl-.12*dt)
        hi=np.minimum(pu+dt*vu+.02*dt*dt,pu+.12*dt)
        box=SimpleNamespace(half=f.half,center_local=f.center_local,
            rectangles=np.array([[*((lo+hi)/2),*((hi-lo)/2)]]),circles=np.empty((0,3)),
            sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-1e6,upper=1e6))
        d=pose_values(box,p)-.1
        answer=np.maximum(answer,np.exp(-dt/3.28)*np.clip((.30-d)/1.,0.,1.))
    if renewal:
        from independent_norm import radial_lower
        risk=np.clip((.155-radial_lower(f,p,state,np.full(len(p),6.56)))/(.08*6.56),0.,1.)
        answer=np.maximum(answer,risk)
    return answer

def dense_path(path):
    path=np.asarray(path);dense=[]
    for a,b in zip(path[:-1],path[1:]):
        dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi
        for u in np.arange(5)/5.:
            dense.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy])
    dense.append(path[-1,:3]);return np.asarray(dense)
