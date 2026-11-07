"""Conditional static-map reachability without actor motion/state access."""
import hashlib,numpy as np
from map_domain import MapDomain,static_mask,future_fields,distance_lower
from recursive_domain import RecursiveDomain
from free_certificate import body_points

class RiskDomain(MapDomain):
 def __init__(self,origin,protocol,mode):
  allowed=static_mask(protocol);super().__init__(origin,allowed);self.mode=mode;self.mask_sha=hashlib.sha256(np.packbits(allowed,bitorder='little').tobytes()).hexdigest();self._cache_time=None;self._sets=None;self._fields=None
 def update(self,packet):
  super().update(packet);self._cache_time=None;self._sets=None;self._fields=None
  from persistent_norm import update_height
  update_height(self)
  self.last=dict(schema='V772_KNOWN_STATIC_NONPENETRATING_01',mode=self.mode,mask_sha256=self.mask_sha,radius_m=.10,axis_speed_bound=.12,future_step_s=.08,condition='unknown_actor_does_not_penetrate_known_static_geometry')
 def future(self):
  if self._cache_time!=self.time:self._sets,self._fields=future_fields(self.possible,self.allowed);self._cache_time=self.time
  return self._sets,self._fields
 def buckets(self,times):
  ticks=np.rint((np.asarray(times)-self.time)/.01).astype(int);assert np.all(abs((np.asarray(times)-self.time)-ticks*.01)<1e-8)and np.all(ticks>=0)and np.all(ticks<=328);return(ticks+7)//8
 def future_point_lower(self,points,times):
  sets,fields=self.future();bucket=self.buckets(times);points=np.asarray(points);out=np.empty(points.shape[:-1])
  for b in np.unique(bucket):
   use=bucket==b;out[use]=distance_lower(fields[b],points[use])
  return out
 def body_lower(self,poses,times):
  original=RecursiveDomain.body_lower(self,poses,times)
  if self.mode=='MAP_HISTORY':return original
  points,cover=body_points(poses);future=self.future_point_lower(points,times).min(axis=1)-cover-.10;return np.maximum(original,future)
 def save_future(self,path):
  sets,fields=self.future();np.savez_compressed(path,bits=np.stack([np.packbits(s,bitorder='little')for s in sets]),shape=self.possible.shape,time=self.time,mask_sha256=self.mask_sha)
