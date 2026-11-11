"""Exact original polytope clipping; vectorize shared-plane rank/edge discovery.

No constraint, tolerance, rounding or prior is changed. Every candidate vertex
is reconstructed by the same line/plane formula and np.unique(round(...,12)).
"""
import importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1029_original_periodic',R/'experiments/v1020_terminal_two_route_development/periodic_support.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
class Polytope(original.Polytope):
    def clip(self,n,b):
        d=self.v@n-b
        if np.max(d)<=0:return
        if np.min(d)>0:raise ValueError('PERIODIC_PRIOR_INCONSISTENT_WITH_OBSERVATIONS')
        active=np.abs(self.v@self.a.T-self.b)<1e-8;i,j=np.triu_indices(len(self.v),1);cross=d[i]*d[j]<0;i,j=i[cross],j[cross];shared=active[i]&active[j]
        enough=shared.sum(axis=1)>=2;first=shared.argmax(axis=1)if len(shared)else np.empty(0,int)
        # The old loop compares its first shared normal against all the rest.
        # Precompute the exact same cross-product rank test for each plane pair.
        independent=np.linalg.norm(np.cross(self.a[:,None,:],self.a[None,:,:]),axis=2)>=1e-10
        edge=enough&(shared&independent[first]).any(axis=1);i,j=i[edge],j[edge]
        points=self.v[i]+(self.v[j]-self.v[i])*(d[i]/(d[i]-d[j]))[:,None]
        candidate=np.unique(np.round(np.concatenate([self.v[d<=0],points]),12),axis=0)
        if len(candidate)<4:raise ValueError('DEGENERATE_PERIODIC_POLYTOPE')
        self.v=candidate;self.a=np.r_[self.a,n[None,:]];self.b=np.r_[self.b,b];keep=np.any(np.abs(self.v@self.a.T-self.b)<1e-8,axis=0);self.a,self.b=self.a[keep],self.b[keep]
class PeriodicSupport(original.PeriodicSupport):
    def __init__(self):
        super().__init__();self.polytopes=[Polytope()for _ in range(8)]
