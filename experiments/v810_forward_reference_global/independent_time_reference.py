"""Independent current-occupancy/time-box reference reconstruction. No online helper imports."""
import math
from types import SimpleNamespace
import numpy as np
from exact_footprint import pose_values
ROBOTPAD=.004*(1+math.hypot(.44,.375)*math.tan(.42722137342572125)/.6)
def field(protocol,state):
 b=np.asarray(protocol['footprint_bounds']);rect=list(protocol['known_rectangles'])
 if state['center']is not None:rect.append(state['current_outer_rectangle'])
 return SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(rect).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
def values(f,state,poses,times):
 p=np.asarray(poses);t=np.asarray(times);v=pose_values(f,p)
 if state['center']is None:return v
 pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper'])
 for i in np.flatnonzero(t<=6.56+1e-10):
  dt=t[i];lo=np.maximum(pl+dt*vl-.02*dt*dt,pl-.12*dt)-1e-5-.12*.02;hi=np.minimum(pu+dt*vu+.02*dt*dt,pu+.12*dt)+1e-5+.12*.02
  box=SimpleNamespace(half=f.half,center_local=f.center_local,rectangles=np.array([[*((lo+hi)/2),*((hi-lo)/2)]]),circles=np.empty((0,3)),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-1e6,upper=1e6))
  v[i]=min(v[i],float(pose_values(box,p[i:i+1])[0])-.1-ROBOTPAD)
 return v
def revalidation_queries(path,index,current):
 part=np.asarray(path)[index:min(len(path),index+26)]
 route=np.vstack([np.r_[current,part[0,3]],part]);p=[route[0,:3]];t=[0.];clock=0.
 for a,b in zip(route[:-1],route[1:]):
  ds=float(np.linalg.norm(b[:2]-a[:2]));wait=.4 if a[3]!=b[3]else 0.
  if wait:
   for dt in np.linspace(0,.4,21):p.append(a[:3]);t.append(clock+dt)
  dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi;n=max(1,int(math.ceil(ds/.008)),int(math.ceil(abs(dy)/.01)))
  for k in range(1,n+1):
   u=k/n;p.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy]);t.append(clock+wait+u*ds/.2)
  clock+=wait+ds/.2
 # Additional angular refinement protects the constant bicycle-interpolation pad
 # for the connector from real pose to the closest reference point as well.
 pp=[p[0]];tt=[t[0]];dymax=.008*math.tan(.42722137342572125)/.6
 for a,b,ta,tb in zip(np.asarray(p)[:-1],np.asarray(p)[1:],t[:-1],t[1:]):
  dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi;n=max(1,int(math.ceil(abs(dy)/dymax)))
  for k in range(1,n+1):
   u=k/n;pp.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy]);tt.append(ta+u*(tb-ta))
 return np.asarray(pp),np.asarray(tt)

