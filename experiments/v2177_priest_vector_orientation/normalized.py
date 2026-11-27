"""Invertible units transform for a prospective optimizer, never invokes one."""
import numpy as np
from collocation import VMAX,KMAX
class Normalized:
 def __init__(self,problem):
  self.problem=problem
  scale=np.ones(problem.total);scale[:problem.pose_count]=np.tile([.6,.6,1.],problem.N+1);scale[problem.speed_start:problem.curvature_start]=VMAX;scale[problem.curvature_start:]=KMAX
  self.scale=scale[problem.free];self.origin=problem.initial.copy();self.eqscale=np.tile([.6,.6,1.],problem.N)
 def original(self,w):return self.origin+self.scale*np.asarray(w,float)
 def bounds(self):
  lo,hi=self.problem.bounds();return (lo-self.origin)/self.scale,(hi-self.origin)/self.scale
 def evaluate(self,w):
  r=self.problem.evaluate(self.original(w));return dict(equalities=r['equalities']/self.eqscale,equality_jacobian=r['equality_jacobian']*self.scale[None,:]/self.eqscale[:,None],inequalities=r['inequalities'],inequality_jacobian=r['inequality_jacobian']*self.scale[None,:])
 def objective(self,w):
  value,gradient=self.problem.objective(self.original(w));return value,gradient*self.scale
