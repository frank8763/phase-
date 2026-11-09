"""Optional declared periodic-course prior; not the general .08m/s motion class.

Unknown center, direction and phase. Each directional coordinate is
c + a*sin(.32*t) + b*cos(.32*t), |a|, |b| <= .25. Causal measured
outer supports constrain a convex 3D coefficient polytope. No actor truth input.
"""
import itertools,math,time
import numpy as np
from scipy.spatial import ConvexHull
OMEGA=.32
AMPLITUDE=.25
EPS=2e-7

def clip(vertices,normal,bound):
 d=vertices@normal-bound
 if np.max(d)<=0:return vertices
 if np.min(d)>0:raise ValueError('PERIODIC_PRIOR_INCONSISTENT_WITH_OBSERVATIONS')
 hull=ConvexHull(vertices)
 edges={tuple(sorted((int(a),int(b))))for face in hull.simplices for a,b in itertools.combinations(face,2)}
 new=[v for v,x in zip(vertices,d)if x<=0]
 for i,j in edges:
  if (d[i]<0<d[j])or(d[j]<0<d[i]):new.append(vertices[i]+(vertices[j]-vertices[i])*d[i]/(d[i]-d[j]))
 p=np.unique(np.round(np.asarray(new),12),axis=0)
 return p[ConvexHull(p).vertices]

class PeriodicSupport:
 def __init__(self):
  self.polytopes=[np.asarray(list(itertools.product([-8.,8.],[-AMPLITUDE,AMPLITUDE],[-AMPLITUDE,AMPLITUDE])))for _ in range(8)]
  self.constraints=[];self.last=None;self.source_tick=None
 def update(self,stamp,native_tick,support):
  if support is None:return False
  if self.last is not None and stamp-self.last<.249999:return False
  n=np.array([1.,math.sin(OMEGA*stamp),math.cos(OMEGA*stamp)])
  # Atomic staging: a failed prior does not silently fall back after partial updates.
  updated=[]
  for i,p in enumerate(self.polytopes):updated.append(clip(clip(p,n,support[i]+EPS),-n,support[i+8]+EPS))
  self.polytopes=updated;self.last=stamp;self.source_tick=native_tick
  self.constraints.append(dict(time=stamp,native_tick=native_tick,support=list(support)))
  return True
 def bounds(self,times):
  t=np.atleast_1d(times);n=np.c_[np.ones(len(t)),np.sin(OMEGA*t),np.cos(OMEGA*t)]
  q=[n@p.T for p in self.polytopes]
  return np.column_stack([x.max(axis=1)+EPS for x in q]+[-x.min(axis=1)+EPS for x in q])
 def snapshot(self):return dict(omega=OMEGA,amplitude=AMPLITUDE,last=self.last,source_tick=self.source_tick,vertices=[p.tolist()for p in self.polytopes])
