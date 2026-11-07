"""Known, exact static map conditional reachability; no actor-state input."""
import hashlib,math
import cv2,numpy as np
from recursive_domain import AXIS,GRID,HALF_DIAGONAL,SLACK,LOWER,canonical_distance,exclusion,RecursiveDomain
from free_certificate import body_points

def static_mask(protocol):
 x,y=np.meshgrid(AXIS,AXIS,indexing='ij');distance=np.minimum.reduce((x+5,5-x,y+5,5-y))
 for cx,cy,hx,hy in protocol['known_rectangles']:
  dx=np.abs(x-cx)-hx;dy=np.abs(y-cy)-hy;sdf=np.hypot(np.maximum(dx,0),np.maximum(dy,0))+np.minimum(np.maximum(dx,dy),0);distance=np.minimum(distance,sdf)
 for cx,cy,r in protocol['known_circles']:distance=np.minimum(distance,np.hypot(x-cx,y-cy)-r)
 allowed=distance+HALF_DIAGONAL>=.10-SLACK;allowed[[0,-1],:]=True;allowed[:,[0,-1]]=True
 return allowed

def grow(possible,allowed=None):
 out=cv2.dilate(possible.astype(np.uint8),np.ones((3,3),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=1).astype(bool)
 if allowed is not None:out&=allowed
 out[[0,-1],:]=True;out[:,[0,-1]]=True
 return out

class MapDomain(RecursiveDomain):
 def __init__(self,origin,allowed):self.origin=np.asarray(origin,float);self.allowed=allowed;self.time=None;self.possible=None;self.distance=None;self.last={}
 def update(self,packet):
  free,_,_=exclusion(packet,self.origin)
  if self.time is None:assert packet['time']==0.;previous=np.ones_like(free)
  else:assert 0<float(packet['time'])-self.time<.081;previous=grow(self.possible,self.allowed)
  self.possible=previous&~free&self.allowed;self.possible[[0,-1],:]=True;self.possible[:,[0,-1]]=True;self.time=float(packet['time']);self.distance=canonical_distance(self.possible)

def distance_lower(distance,points):
 p=np.asarray(points,float);flat=p.reshape(-1,2);idx=np.rint((flat-LOWER)/GRID).astype(int);valid=((idx>=0)&(idx<len(AXIS))).all(axis=1);idx=np.clip(idx,0,len(AXIS)-1);value=distance[idx[:,0],idx[:,1]]-np.linalg.norm(LOWER+idx*GRID-flat,axis=1)-HALF_DIAGONAL-SLACK;value[~valid]=0.;return np.maximum(0,value).reshape(p.shape[:-1])

def future_fields(possible,allowed):
 rows=[possible.copy()];distances=[canonical_distance(possible)]
 for j in range(41):rows.append(grow(rows[-1],allowed));distances.append(canonical_distance(rows[-1]))
 return rows,distances

def future_body(fields,poses):
 points,cover=body_points(poses);ticks=np.arange(1,len(poses)+1);bucket=np.ceil(ticks/8).astype(int);out=np.empty(len(poses))
 for b in np.unique(bucket):
  ids=bucket==b;out[ids]=distance_lower(fields[b],points[ids]).min(axis=1)-cover-.10
 return out
