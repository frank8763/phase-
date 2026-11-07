"""Conservative historical certificates, time anchored to avoid repeated rounding loss."""
import numpy as np
from recursive_domain import HALF_DIAGONAL,SLACK,SPEED
SCALE=1000000.
def update_height(domain):
 fresh=np.maximum(0.,domain.distance-HALF_DIAGONAL-SLACK)
 raw=(fresh+SPEED*domain.time)*SCALE
 assert np.max(raw)<np.iinfo(np.uint32).max,'HEIGHT_RANGE_OVERFLOW'
 # Zero carries no positive certificate. Flooring once per new observation
 # loses <1 micrometre. Old integer certificates are never re-quantized.
 candidate=np.where(fresh>0.,np.floor(raw),0.).astype('<u4')
 domain.history_height=candidate if not hasattr(domain,'history_height')else np.maximum(domain.history_height,candidate)

class Historical:
 def __init__(self,domain):self.origin=domain.origin;self.time=domain.time;self.height=domain.history_height
 def point_lower(self,points,times):
  from recursive_domain import AXIS,LOWER,GRID
  p=np.asarray(points,float);flat=p.reshape(-1,2);t=np.broadcast_to(times,p.shape[:-1]).reshape(-1);assert np.all(t>=self.time-1e-10),'NONCAUSAL_HISTORY_QUERY'
  ix=np.rint((flat-LOWER)/GRID).astype(int);valid=((ix>=0)&(ix<len(AXIS))).all(axis=1);ix=np.clip(ix,0,len(AXIS)-1)
  current=np.maximum(0.,self.height[ix[:,0],ix[:,1]].astype(float)/SCALE-SPEED*self.time-np.linalg.norm(LOWER+ix*GRID-flat,axis=1));current[~valid]=0.
  return(current-SPEED*np.maximum(0.,t-self.time)).reshape(p.shape[:-1])
