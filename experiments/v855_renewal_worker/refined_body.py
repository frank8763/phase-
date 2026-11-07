"""Conservative refinement of full rectangular-body coverage, no actor access.
Every returned value is a lower bound. Refinement cannot weaken original bounds.
"""
import math,numpy as np
GRID=.01
THRESHOLD=.155
HALF=(.44,.375)
def original(domain,poses,times):
 from free_certificate import body_points,old_lower
 points,rho=body_points(poses);value=domain.point_lower(points,np.asarray(times)[:,None]).min(axis=1)-rho-.10
 return np.maximum(value,old_lower(poses,times,domain.origin))
def refined(domain,poses,times):
 p=np.asarray(poses,float).reshape(-1,3);t=np.asarray(times,float).reshape(-1);assert len(t)==len(p)
 lower=original(domain,p,t)
 # 2*domain GRID means each body tile radius <= sqrt(2)*GRID;
 # no narrower obstacle class, changed safety threshold or future observations.
 for spacing in [.04,2*GRID]:
  use=np.flatnonzero(lower<THRESHOLD)
  if not len(use):break
  q=p[use];ax=[np.linspace(-h,h,math.ceil(2*h/spacing)+1)for h in HALF];x,y=np.meshgrid(*ax,indexing='ij');local=np.c_[x.ravel(),y.ravel()];c,s=np.cos(q[:,2]),np.sin(q[:,2]);points=q[:,None,:2]+np.stack((c[:,None]*local[None,:,0]-s[:,None]*local[None,:,1],s[:,None]*local[None,:,0]+c[:,None]*local[None,:,1]),axis=-1);rho=.5*math.hypot(ax[0][1]-ax[0][0],ax[1][1]-ax[1][0])
  values=domain.point_lower(points,t[use,None]).min(axis=1)-rho-.10;lower[use]=np.maximum(lower[use],values)
 return lower
