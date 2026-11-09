"""Causal periodic coefficient enclosure; NumPy-only online clipping.

New public class: fixed .32rad/s frequency and <=.25m sinusoidal amplitude.
Unknown anchor, axis and phase are not read. Intersect with the original speed
bound when forecasting. Inconsistent observations stop; no unlogged fallback.
"""
import itertools,math
import numpy as np
OMEGA=.32;AMPLITUDE=.25;EPS=2e-7
class Polytope:
 def __init__(self):
  self.v=np.asarray(list(itertools.product([-8.,8.],[-.25,.25],[-.25,.25])))
  self.a=np.r_[np.eye(3),-np.eye(3)];self.b=np.array([8.,.25,.25,8.,.25,.25])
 def clip(self,n,b):
  d=self.v@n-b
  if np.max(d)<=0:return
  if np.min(d)>0:raise ValueError('PERIODIC_PRIOR_INCONSISTENT_WITH_OBSERVATIONS')
  # Vertices joined by an edge share two linearly independent supporting planes.
  active=np.abs(self.v@self.a.T-self.b)<1e-8
  i,j=np.triu_indices(len(self.v),1);cross=(d[i]*d[j]<0)
  i,j=i[cross],j[cross];shared=active[i]&active[j]
  points=[z for z,x in zip(self.v,d)if x<=0]
  for u,w,mask in zip(i,j,shared):
   normals=self.a[mask]
   if len(normals)<2:continue
   if np.max(np.linalg.norm(np.cross(normals[0],normals[1:]),axis=1))<1e-10:continue
   points.append(self.v[u]+(self.v[w]-self.v[u])*d[u]/(d[u]-d[w]))
  candidate=np.unique(np.round(np.asarray(points),12),axis=0)
  if len(candidate)<4:raise ValueError('DEGENERATE_PERIODIC_POLYTOPE')
  self.v=candidate;self.a=np.r_[self.a,n[None,:]];self.b=np.r_[self.b,b]
  # Planes not incident on any current vertex are redundant for edge discovery.
  keep=np.any(np.abs(self.v@self.a.T-self.b)<1e-8,axis=0)
  self.a,self.b=self.a[keep],self.b[keep]
class PeriodicSupport:
 def __init__(self):self.polytopes=[Polytope()for _ in range(8)];self.constraints=[];self.last=None;self.source_tick=None
 def update(self,stamp,native_tick,support):
  if support is None:return False
  if self.last is not None and stamp-self.last<.249999:return False
  n=np.array([1.,math.sin(OMEGA*stamp),math.cos(OMEGA*stamp)])
  # Any numerical inconsistency is a failed candidate, never a prior reset.
  for i,p in enumerate(self.polytopes):p.clip(n,support[i]+EPS);p.clip(-n,support[i+8]+EPS)
  self.last=stamp;self.source_tick=native_tick;self.constraints.append(dict(time=stamp,native_tick=native_tick,support=list(support)));return True
 def bounds(self,times):return bounds_from_vertices([p.v for p in self.polytopes],times)
 def snapshot(self):return dict(omega=OMEGA,amplitude=AMPLITUDE,last=self.last,source_tick=self.source_tick,vertices=[p.v.tolist()for p in self.polytopes])
def bounds_from_vertices(vertices,times):
 t=np.atleast_1d(times);n=np.c_[np.ones(len(t)),np.sin(OMEGA*t),np.cos(OMEGA*t)]
 q=[n@np.asarray(p).T for p in vertices]
 return np.column_stack([x.max(axis=1)+EPS for x in q]+[-x.min(axis=1)+EPS for x in q])
def swept_bounds(vertices,t0,t1):
 """Exact maximum of each coefficient vertex over an interval, plus roundoff."""
 assert t1>=t0
 results=[]
 for p in vertices:
  p=np.asarray(p);a,b=p[:,1],p[:,2]
  ends=np.stack([p[:,0]+a*math.sin(OMEGA*t)+b*math.cos(OMEGA*t)for t in [t0,t1]])
  upper=ends.max(axis=0);lower=ends.min(axis=0)
  phase=np.arctan2(a,b)
  for offset,ismax in [(0.,True),(math.pi,False)]:
   k=np.ceil((OMEGA*t0-phase-offset)/(2*math.pi));at=(phase+offset+2*math.pi*k)/OMEGA;mask=at<=t1+1e-12
   extreme=p[:,0]+(1 if ismax else -1)*np.hypot(a,b)
   if ismax:upper=np.where(mask,np.maximum(upper,extreme),upper)
   else:lower=np.where(mask,np.minimum(lower,extreme),lower)
  results.append((float(upper.max())+EPS,float(-lower.min())+EPS))
 return np.array([x[0]for x in results]+[x[1]for x in results])
