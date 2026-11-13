"""Deterministic finite whole-source shooting. No physics or source mutation."""
import ctypes,time,math
from pathlib import Path
import numpy as np
from kernel import PARAMETERS,initial,ref,REQUIRED
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1110_constrained_joint_source';CAP=.42722137342572125;KNOTS=12
class BudgetEnd(Exception):pass
class Solver:
 def __init__(self,x,path,gears):
  self.x=x;self.sections=[];i=0
  while i<len(gears):
   j=i+1
   while j<len(gears)and gears[j]==gears[i]:j+=1
   q=path[i:j+1];arc=np.r_[0.,np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1).cumsum()];self.sections.append((q,arc,gears[i]));i=j
  self.n=len(self.sections);self.calls=0;self.native=0;self.in_call=False;self.best=None;self.deadline=float('inf');self.geometry=ref._old.Geometry(x['setup']['known'],x['source']['periodic'])
  self.lib=ctypes.CDLL(str(O/'profile.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');it=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
  self.lib.profile.argtypes=[a,a,a,a,it,it,ctypes.c_int,a,a,a,a,a];self.lib.profile.restype=ctypes.c_int
  inp=initial(x['packet']);self.state=np.array(inp['state']);self.memory=np.r_[inp['last_ctrl'],inp['integral']];self.limits=np.array(x['setup']['limits'],float);self.rates=np.array(x['setup']['slew_per_second'],float);p=PARAMETERS
  self.parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']],float)
  self.base_ticks=np.array([max(100,int(round(arc[-1]/(.03 if d<0 else .08)/.01)))for q,arc,d in self.sections]);self.lower=np.r_[np.full(self.n*KNOTS,-CAP),np.full(self.n,.75)];self.upper=np.r_[np.full(self.n*KNOTS,CAP),np.full(self.n,1.35)]
 def seed(self):
  import json
  z=np.array(json.loads((R/'runs/v1109_joint_cusp_source/OPTIMIZATION.json').read_text())['z'],float)
  assert z.shape==self.lower.shape and np.all(z>=self.lower)and np.all(z<=self.upper),'PRIOR_SOURCE_BOUNDS'
  return z
 def schedule(self,z):
  rows=[];sections=[];cursor=0;angles=z[:self.n*KNOTS].reshape(self.n,KNOTS)
  for i,((q,arc,d),targets)in enumerate(zip(self.sections,angles)):
   if i:rows.append((float(targets[0]),0.,300,1));cursor+=300
   begin=cursor;n=int(round(self.base_ticks[i]*z[self.n*KNOTS+i]));counts=np.diff(np.round(np.linspace(0,n,KNOTS+1)).astype(int))
   for t,k in zip(targets,counts):rows.append((float(t),.08 if d>0 else-.03,int(k),0));cursor+=int(k)
   moving_end=cursor;rows.append((0.,0.,2200,0));cursor+=2200;sections.append((begin,moving_end,cursor))
  return rows,sections
 def simulate(self,z,reserved_final=False):
  if not reserved_final and (self.calls>=1700 or time.monotonic()>self.deadline):raise BudgetEnd()
  rows,sections=self.schedule(z);n=sum(r[2]for r in rows);assert n<=40000
  targets=np.array([r[0]for r in rows]);speeds=np.array([r[1]for r in rows]);ticks=np.array([r[2]for r in rows],np.int32);modes=np.array([r[3]for r in rows],np.int32);ss=np.empty((n,8));uu=np.empty((n,4));self.in_call=True
  code=self.lib.profile(self.state,self.memory,targets,speeds,ticks,modes,len(rows),self.limits,self.rates,self.parameters,ss,uu);self.in_call=False
  assert code==n,('ANALYTICAL_PROFILE_CONTRACT',code)
  self.calls+=1;self.native+=n
  return np.vstack([self.state,ss]),uu,rows,sections
 def constraint_terms(self,ss,events):
  bounds=[];cross=[];endpoints=[];geometry_pose_count=0
  for section,((q,arc,d),(begin,moving,end))in enumerate(zip(self.sections,events)):
   start=begin-300 if section else begin;poses=ss[start:end+1,:3];n=len(poses);bins=256
   mapping=np.minimum(np.arange(n)*bins//n,bins-1);indices=np.minimum(((np.arange(bins)+.5)*n/bins).astype(int),n-1);samples=poses[indices]
   distance=np.linalg.norm(poses[:,:2]-samples[mapping,:2],axis=1)
   angle=np.abs(np.arctan2(np.sin(poses[:,2]-samples[mapping,2]),np.cos(poses[:,2]-samples[mapping,2])))
   xy_envelope=np.zeros(bins);body_envelope=np.zeros(bins)
   np.maximum.at(xy_envelope,mapping,distance);np.maximum.at(body_envelope,mapping,distance+np.hypot(.44,.375)*angle)
   static,dynamic=self.geometry.clearances(samples);bounds.extend(np.minimum(static,dynamic)-body_envelope);geometry_pose_count+=bins
   edge=np.diff(q[:,:2],axis=0);l2=(edge*edge).sum(axis=1);delta=samples[:,None,:2]-q[None,:-1,:2];fraction=np.divide((delta*edge).sum(axis=2),l2,out=np.zeros(delta.shape[:2]),where=l2>0.)
   point_dist=np.linalg.norm(delta-np.clip(fraction,0.,1.)[:,:,None]*edge,axis=2).min(axis=1);cross.extend(point_dist+xy_envelope);endpoints.append(float(np.linalg.norm(ss[end,:2]-q[-1,:2])))
  bounds=np.array(bounds);cross=np.array(cross);endpoints=np.array(endpoints)
  # Restoration targets are stricter than the unchanged final admission gates.
  violation=np.r_[np.maximum(0.,REQUIRED+.003-bounds),np.maximum(0.,cross-.035),np.maximum(0.,endpoints-.018)]
  return violation,dict(minimum_certified_raw_lower_m=float(bounds.min()),maximum_certified_cross_upper_m=float(cross.max()),endpoint_errors_m=endpoints.tolist(),maximum_restoration_violation_m=float(violation.max()),restoration_targets_met=bool((violation<=1e-10).all()),sampled_geometry_poses=geometry_pose_count)
 def residual(self,z):
  ss,uu,rows,events=self.simulate(z);residual=[];summary=[]
  for (q,arc,d),(begin,moving,end)in zip(self.sections,events):
   indices=begin+np.linspace(0,moving-begin,49);samples=np.array([np.interp(indices,np.arange(len(ss)),ss[:,k])for k in range(3)]).T
   desired=np.linspace(0,arc[-1],49);ref=np.c_[np.interp(desired,arc,q[:,0]),np.interp(desired,arc,q[:,1])]
   residual.extend(((samples[:,:2]-ref)/math.sqrt(49)).ravel())
   # The next parked-steering segment is propagated, so its yaw effect feeds
   # every following residual; no cusp is independently reset or optimized.
   residual.extend((8*(ss[end,:2]-q[-1,:2])).tolist());heading=np.arctan2(np.sin(ss[end,2]-q[-1,2]),np.cos(ss[end,2]-q[-1,2]));residual.append(.3*heading)
   summary.append(float(np.linalg.norm(ss[end,:2]-q[-1,:2])))
  residual.extend((.001*np.diff(z[:self.n*KNOTS].reshape(self.n,KNOTS),axis=1)).ravel())
  violation,report=self.constraint_terms(ss,events);result=np.r_[.1*np.asarray(residual),50*violation];cost=float(result@result)
  key=(0 if report['restoration_targets_met']else 1,report['maximum_restoration_violation_m'],cost)
  if self.best is None or key<self.best['key']:self.best=dict(z=z.copy(),cost=cost,endpoint_errors=summary,calls=self.calls,key=key,constraints=report)
  return result
 def solve(self):
  self.deadline=time.monotonic()+120.;z=self.seed();damping=.001;iterations=[];r=self.residual(z)
  for iteration in range(30):
   try:
    jac=np.empty((len(r),len(z)))
    for j in range(len(z)):
     step=.001 if j<self.n*KNOTS else .003;v=z.copy();v[j]=min(self.upper[j],z[j]+step)
     if v[j]==z[j]:v[j]=max(self.lower[j],z[j]-step)
     jac[:,j]=(self.residual(v)-r)/(v[j]-z[j])
    gradient=jac.T@r;h=jac.T@jac;scale=np.maximum(np.diag(h),1e-5);delta=np.linalg.solve(h+damping*np.diag(scale),-gradient);accepted=False
    for fraction in [1.,.5,.25,.125,.0625]:
     candidate=np.clip(z+fraction*delta,self.lower,self.upper);rr=self.residual(candidate)
     if rr@rr<r@r:z=candidate;r=rr;accepted=True;break
    iterations.append(dict(iteration=iteration,cost=float(r@r),accepted=accepted,calls=self.calls));damping=max(1e-6,damping/2)if accepted else min(1e6,damping*10)
    if np.linalg.norm(gradient,np.inf)<1e-7:break
   except BudgetEnd:break
  return self.best,iterations
