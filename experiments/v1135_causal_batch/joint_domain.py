"""Cross-direction coefficient consistency, support bounds with dual witnesses."""
import sys,math,warnings
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
import numpy as np
from scipy.spatial import ConvexHull
from scipy.optimize import linprog
NORMALS=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)]
EPS=1e-6
class Domain:
 def __init__(self,vertices):
  assert len(vertices)==8;self.vertices=[np.asarray(v,float)for v in vertices];rows=[];right=[];self.maps=[]
  for i,v in enumerate(self.vertices):
   assert v.ndim==2 and v.shape[1]==3 and np.isfinite(v).all();nx,ny=NORMALS[i];P=np.array([[nx,0,0,ny,0,0],[0,nx,0,0,ny,0],[0,0,nx,0,0,ny]]);self.maps.append(P);assert np.linalg.matrix_rank(v-v.mean(axis=0),tol=1e-10)==3,'DEGENERATE_PRIOR_COEFFICIENT_HULL';h=ConvexHull(v).equations;rows.extend(h[:,:3]@P);right.extend(-h[:,3]+EPS)
  vx,vy=self.vertices[0],self.vertices[4];lower_x=vx.min(axis=0)-EPS;upper_x=vx.max(axis=0)+EPS;guard=abs(NORMALS[4,0])*np.maximum(abs(lower_x),abs(upper_x));self.lower=np.r_[lower_x,vy.min(axis=0)-EPS-guard];self.upper=np.r_[upper_x,vy.max(axis=0)+EPS+guard];self.A=np.vstack([rows,np.eye(6),-np.eye(6)]);self.b=np.r_[right,self.upper,-self.lower];self.calls=0;self.max_residual=0.;r=self.optimize(np.zeros(6));assert r.success,'JOINT_CAUSAL_DOMAIN_EMPTY';self.witness=r.x
 def optimize(self,c):
  with warnings.catch_warnings():
   warnings.filterwarnings('ignore',message='Unrecognized options detected')
   r=linprog(c,A_ub=self.A,b_ub=self.b,bounds=[(None,None)]*6,method='highs',options={'threads':1,'time_limit':5.})
  self.calls+=1;return r
 def certified_upper(self,direction):
  w=np.asarray(direction,float);assert w.shape==(6,)and np.isfinite(w).all();r=self.optimize(-w);assert r.success,'JOINT_SUPPORT_LP_FAILED';lam=np.maximum(0.,-r.ineqlin.marginals);residual=w-self.A.T@lam;upper=float(self.b@lam+np.where(residual>=0,residual*self.upper,residual*self.lower).sum()+1e-8);self.max_residual=max(self.max_residual,float(abs(residual).max()));assert upper>=float(w@r.x)-1e-7,'DUAL_UPPER_BELOW_PRIMAL';return upper,lam,residual
 def support(self,normal,time):
  nx,ny=normal;s=math.sin(.32*time);c=math.cos(.32*time);return self.certified_upper(np.array([nx,nx*s,nx*c,ny,ny*s,ny*c]))
 def table(self,centers):
  bounds=[];dual=[];residual=[]
  for t in centers:
   br=[];dr=[];rr=[]
   for n in NORMALS:
    value,lam,r=self.support(n,float(t));br.append(value);dr.append(lam);rr.append(r)
   bounds.append(br);dual.append(dr);residual.append(rr)
  return np.array(bounds),np.array(dual),np.array(residual)
