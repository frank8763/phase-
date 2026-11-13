"""Deterministic finite whole-source shooting. No physics or source mutation."""
import ctypes,time,math
from pathlib import Path
import numpy as np
from bindings import PARAMETERS,initial,ref,REQUIRED,GAIN
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1115_coupled_complete_source';CAP=.42722137342572125;KNOTS=12
class BudgetEnd(Exception):pass
class FeasibleFound(Exception):pass
class Solver:
 def __init__(self,x,path,gears,initial_guess=None):
  self.x=x;self.sections=[];i=0
  while i<len(gears):
   j=i+1
   while j<len(gears)and gears[j]==gears[i]:j+=1
   q=path[i:j+1];arc=np.r_[0.,np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1).cumsum()];self.sections.append((q,arc,gears[i]));i=j
  self.n=len(self.sections);self.initial_guess=initial_guess;self.calls=0;self.native=0;self.in_call=False;self.best=None;self.deadline=float('inf');self.geometry=ref._old.Geometry(x['setup']['known'],x['source']['periodic']);self.cache={};self.derivative_key=None;self.derivative_value=None
  self.lib=ctypes.CDLL(str(O/'profile.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');it=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
  self.lib.profile.argtypes=[a,a,a,a,it,it,ctypes.c_int,a,a,a,a,a];self.lib.profile.restype=ctypes.c_int
  self.lib.profile_work.argtypes=[];self.lib.profile_work.restype=ctypes.c_int
  inp=initial(x['packet']);self.state=np.array(inp['state']);self.memory=np.r_[inp['last_ctrl'],inp['integral']];self.limits=np.array(x['setup']['limits'],float);self.rates=np.array(x['setup']['slew_per_second'],float);p=PARAMETERS
  self.parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient'],GAIN,0.],float)
  self.base_ticks=np.array([max(100,int(round(arc[-1]/(.03 if d<0 else .08)/.01)))for q,arc,d in self.sections]);self.lower=np.r_[np.full(self.n*KNOTS,-CAP),np.full(self.n,.75)];self.upper=np.r_[np.full(self.n*KNOTS,CAP),np.full(self.n,1.35)]
 def seed(self):
  if self.initial_guess is not None:
   z=np.array(self.initial_guess,float);assert z.shape==self.lower.shape and np.all(z>=self.lower)and np.all(z<=self.upper),'REGISTERED_SOURCE_SEED_BOUNDS';return z
  angles=[];offset=PARAMETERS['lateral_discrete'][0]/PARAMETERS['gain_a'];a=PARAMETERS['gain_a']
  for q,arc,d in self.sections:
   yaw=np.unwrap(q[:,2]);rear=q[:,:2]-offset*np.c_[np.cos(yaw),np.sin(yaw)];rear_arc=np.r_[0.,np.linalg.norm(np.diff(rear,axis=0),axis=1).cumsum()];curvature=np.diff(yaw)/(np.maximum(np.diff(rear_arc),1e-9)*d)
   angles.extend(np.interp(np.linspace(0,rear_arc[-1],KNOTS),(rear_arc[:-1]+rear_arc[1:])/2,np.arctan(.6*curvature/a)))
  return np.clip(np.r_[angles,np.ones(self.n)],self.lower,self.upper)
 def schedule(self,z):
  rows=[];sections=[];cursor=0;angles=z[:self.n*KNOTS].reshape(self.n,KNOTS)
  for i,((q,arc,d),targets)in enumerate(zip(self.sections,angles)):
   if i:rows.append((float(targets[0]),0.,600,1));cursor+=600
   begin=cursor;n=int(round(self.base_ticks[i]*z[self.n*KNOTS+i]));counts=np.diff(np.round(np.linspace(0,n,KNOTS+1)).astype(int))
   for t,k in zip(targets,counts):rows.append((float(t),.08 if d>0 else-.03,int(k),0));cursor+=int(k)
   moving_end=cursor;rows.append((0.,0.,2200,0));cursor+=2200;sections.append((begin,moving_end,cursor))
  return rows,sections
 def simulate(self,z,reserved_final=False):
  if not reserved_final and (self.calls>=1700 or time.monotonic()>self.deadline):raise BudgetEnd()
  rows,sections=self.schedule(z);n=sum(r[2]for r in rows);assert n<=40000
  targets=np.array([r[0]for r in rows]);speeds=np.array([r[1]for r in rows]);ticks=np.array([r[2]for r in rows],np.int32);modes=np.array([r[3]for r in rows],np.int32);ss=np.empty((n,8));uu=np.empty((n,4));self.in_call=True
  code=self.lib.profile(self.state,self.memory,targets,speeds,ticks,modes,len(rows),self.limits,self.rates,self.parameters,ss,uu);work=int(self.lib.profile_work());self.in_call=False;self.calls+=1;self.native+=work
  assert code==n,('ANALYTICAL_PROFILE_CONTRACT',code)
  assert work==n,'ANALYTICAL_WORK_ACCOUNTING'
  return np.vstack([self.state,ss]),uu,rows,sections
 def constraint_terms(self,ss,events):
  bounds=[];cross=[];endpoints=[];mode_envelopes=[];geometry_pose_count=0
  for section,((q,arc,d),(begin,moving,end))in enumerate(zip(self.sections,events)):
   start=begin-600 if section else begin;poses=ss[start:end+1,:3];n=len(poses);bins=256
   mapping=np.minimum(np.arange(n)*bins//n,bins-1);indices=np.minimum(((np.arange(bins)+.5)*n/bins).astype(int),n-1);samples=poses[indices]
   distance=np.linalg.norm(poses[:,:2]-samples[mapping,:2],axis=1)
   angle=np.abs(np.arctan2(np.sin(poses[:,2]-samples[mapping,2]),np.cos(poses[:,2]-samples[mapping,2])))
   xy_envelope=np.zeros(bins);body_envelope=np.zeros(bins)
   np.maximum.at(xy_envelope,mapping,distance);np.maximum.at(body_envelope,mapping,distance+np.hypot(.44,.375)*angle)
   static,dynamic=self.geometry.clearances(samples);bounds.extend(np.minimum(static,dynamic)-body_envelope);geometry_pose_count+=bins
   edge=np.diff(q[:,:2],axis=0);l2=(edge*edge).sum(axis=1);delta=samples[:,None,:2]-q[None,:-1,:2];fraction=np.divide((delta*edge).sum(axis=2),l2,out=np.zeros(delta.shape[:2]),where=l2>0.)
   point_dist=np.linalg.norm(delta-np.clip(fraction,0.,1.)[:,:,None]*edge,axis=2).min(axis=1);cross.extend(point_dist+xy_envelope);endpoints.append(float(np.linalg.norm(ss[end,:2]-q[-1,:2])))
   if section:
    st,dy=self.geometry.clearances(ss[start:start+1,:3]);mode_envelopes.append(float(min(st[0],dy[0]))-.02-math.hypot(.44,.375)*.1);geometry_pose_count+=1
  bounds=np.array(bounds);cross=np.array(cross);endpoints=np.array(endpoints)
  # Restoration targets are stricter than the unchanged final admission gates.
  signed=np.r_[bounds-(REQUIRED+.001),.038-cross,.019-endpoints,np.array(mode_envelopes)-(REQUIRED+.001)]
  return signed,dict(minimum_certified_raw_lower_m=float(bounds.min()),maximum_certified_cross_upper_m=float(cross.max()),endpoint_errors_m=endpoints.tolist(),coupled_mode_envelope_lower_m=mode_envelopes,maximum_restoration_violation_m=float(np.maximum(0.,-signed).max()),restoration_targets_met=bool((signed>=-1e-10).all()),sampled_geometry_poses=geometry_pose_count,explicit_inequality_count=len(signed))
 def evaluate(self,z):
  z=np.clip(np.asarray(z,float),self.lower,self.upper);cache_key=z.tobytes()
  if cache_key in self.cache:return self.cache[cache_key]
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
  signed,report=self.constraint_terms(ss,events);result=np.asarray(residual);cost=float(result@result)
  key=(0 if report['restoration_targets_met']else 1,report['maximum_restoration_violation_m'],cost)
  if self.best is None or key<self.best['key']:self.best=dict(z=z.copy(),cost=cost,endpoint_errors=summary,calls=self.calls,key=key,constraints=report)
  value=(cost,signed,report);self.cache[cache_key]=value
  if len(self.cache)>128:self.cache.pop(next(iter(self.cache)))
  return value
 def derivatives(self,z):
  z=np.clip(np.asarray(z,float),self.lower,self.upper);key=z.tobytes()
  if key==self.derivative_key:return self.derivative_value
  f,g,_=self.evaluate(z);df=np.empty(len(z));dg=np.empty((len(g),len(z)))
  for j in range(len(z)):
   step=.001 if j<self.n*KNOTS else .003;v=z.copy();v[j]=min(self.upper[j],z[j]+step)
   if v[j]==z[j]:v[j]=max(self.lower[j],z[j]-step)
   ff,gg,_=self.evaluate(v);delta=v[j]-z[j];df[j]=(ff-f)/delta;dg[:,j]=(gg-g)/delta
  self.derivative_key=key;self.derivative_value=(df,dg);return df,dg
 def solve(self):
  import sys
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'))
  from scipy.optimize import minimize
  self.deadline=time.monotonic()+120.;z=self.seed();iterations=[]
  def callback(current):
   f,g,r=self.evaluate(current);iterations.append(dict(iteration=len(iterations),cost=f,minimum_inequality_margin_m=float(g.min()),calls=self.calls))
   if (g>=-1e-10).all():raise FeasibleFound()
  try:
   result=minimize(lambda v:self.evaluate(v)[0],z,jac=lambda v:self.derivatives(v)[0],method='SLSQP',bounds=list(zip(self.lower,self.upper)),
      constraints=[dict(type='ineq',fun=lambda v:self.evaluate(v)[1],jac=lambda v:self.derivatives(v)[1])],callback=callback,options=dict(maxiter=40,ftol=1e-8,disp=False))
   self.optimizer_exit=dict(status=int(result.status),success=bool(result.success),message=str(result.message),iterations=int(result.nit),success_never_replaces_original_safety_audit=True)
  except FeasibleFound:self.optimizer_exit=dict(status='TARGET_FEASIBLE_STOP',success=True)
  except BudgetEnd:self.optimizer_exit=dict(status='FIXED_BUDGET_STOP',success=False)
  return self.best,iterations
