"""Independent map mask and numpy propagation/scipy distance implementation."""
import hashlib,numpy as np
from scipy.ndimage import distance_transform_edt
from recursive_domain import RecursiveDomain,AXIS,GRID,HALF_DIAGONAL,SLACK,LOWER,exclusion
from free_certificate import body_points

def grow(a,mask):
 p=np.pad(a,1,constant_values=True);out=np.zeros_like(a)
 for i in range(3):
  for j in range(3):out|=p[i:i+a.shape[0],j:j+a.shape[1]]
 out&=mask;out[[0,-1],:]=True;out[:,[0,-1]]=True;return out

def field(a):return distance_transform_edt(~a,sampling=GRID)
def lookup(f,pts):
 pts=np.asarray(pts);shape=pts.shape[:-1];flat=pts.reshape(-1,2);ix=np.rint((flat-LOWER)/GRID).astype(int);valid=((ix>=0)&(ix<len(AXIS))).all(axis=1);ix=np.clip(ix,0,len(AXIS)-1);value=f[ix[:,0],ix[:,1]]-np.linalg.norm(LOWER+GRID*ix-flat,axis=1)-HALF_DIAGONAL-SLACK;value[~valid]=0.;return np.maximum(0,value).reshape(shape)
class IndependentDomain(RecursiveDomain):
 def __init__(self,origin,protocol,mode):
  super().__init__(origin);x,y=np.meshgrid(AXIS,AXIS,indexing='ij');mask=np.ones_like(x,dtype=bool)
  for cx,cy,hx,hy in protocol['known_rectangles']:
   u=abs(x-cx)-hx;v=abs(y-cy)-hy;distance=np.where((u<=0)&(v<=0),np.maximum(u,v),np.sqrt(np.maximum(u,0)**2+np.maximum(v,0)**2));mask&=distance+HALF_DIAGONAL>=.1-SLACK
  for cx,cy,rad in protocol['known_circles']:mask&=np.sqrt((x-cx)**2+(y-cy)**2)-rad+HALF_DIAGONAL>=.1-SLACK
  for boundary in [x+5,5-x,y+5,5-y]:mask&=boundary+HALF_DIAGONAL>=.1-SLACK
  mask[[0,-1],:]=True;mask[:,[0,-1]]=True;self.allowed=mask;self.mask_sha=hashlib.sha256(np.packbits(mask,bitorder='little').tobytes()).hexdigest();self.mode=mode;self.cache_time=None;self.sets=None;self.fields=None
 def update(self,packet):
  free,_,_=exclusion(packet,self.origin)
  if self.time is None:assert packet['time']==0.;past=np.ones_like(free)
  else:assert 0<float(packet['time'])-self.time<.081;past=grow(self.possible,self.allowed)
  self.possible=past&~free&self.allowed;self.possible[[0,-1],:]=True;self.possible[:,[0,-1]]=True;self.time=float(packet['time']);self.distance=field(self.possible);self.last=dict(schema='V772_KNOWN_STATIC_NONPENETRATING_01',mode=self.mode,mask_sha256=self.mask_sha,radius_m=.10,axis_speed_bound=.12,future_step_s=.08,condition='unknown_actor_does_not_penetrate_known_static_geometry');self.cache_time=None;self.sets=None;self.fields=None
 def future(self):
  if self.cache_time!=self.time:
   self.sets=[self.possible.copy()];self.fields=[self.distance.copy()]
   for _ in range(41):self.sets.append(grow(self.sets[-1],self.allowed));self.fields.append(field(self.sets[-1]))
   self.cache_time=self.time
  return self.sets,self.fields
 def buckets(self,times):
  x=(np.asarray(times)-self.time)/.01;ticks=np.rint(x).astype(int);assert np.max(abs(x-ticks))<1e-6 and np.min(ticks)>=0 and np.max(ticks)<=328;return(ticks+7)//8
 def future_point_lower(self,points,times):
  _,fields=self.future();buckets=self.buckets(times);points=np.asarray(points);result=np.empty(points.shape[:-1])
  for b in np.unique(buckets):use=buckets==b;result[use]=lookup(fields[b],points[use])
  return result
 def body_lower(self,poses,times):
  original=RecursiveDomain.body_lower(self,poses,times)
  if self.mode=='MAP_HISTORY':return original
  pts,cover=body_points(poses);return np.maximum(original,self.future_point_lower(pts,times).min(axis=1)-cover-.1)
