"""Full-body environmental PSF/PCBF engineering NLP, explicitly ideal dynamics."""
import math
from geometry import feature,support_at,REQUIRED
from kinematics import rollout_jac,N,KMAX

def values_jac(z,case,known,kind):
 states,jacs=rollout_jac(z,case['pose'],case['gear']);values=[];derivatives=[];labels=[]
 for i,(p,j)in enumerate(zip(states,jacs)):
  bounds=None
  if case.get('causal')is not None:bounds=support_at(case['causal']['periodic'],case['sim_time']+i*.1,whole_cycle=i==N)
  vv,gg,ll=feature(p,known,bounds)
  tight=.0005*i if kind=='PCBF'and i<N else 0.
  for value,g,label in zip(vv,gg,ll):
   values.append(REQUIRED+tight-value);derivatives.append([-sum(g[a]*j[a][k]for a in range(3))for k in range(16)]);labels.append(f'{i}:{label}')
 return values,derivatives,labels

def solve(np,minimize,case,known,kind,observe):
 assert kind in['PSF','PCBF'];gear=case['gear'];nominal=case['nominal'];bounds=[(.005,.1),(-KMAX,KMAX)]*N;u=np.asarray([.05,0.]*N)
 initial=values_jac(u,case,known,kind)[0];n=len(initial);slack=np.zeros(n)
 if kind=='PSF'and max(initial[:n//(N+1)])>1e-7:return dict(passed=False,expected_refusal='INITIAL_HARD_FULL_BODY_CONSTRAINT',physical_authority=False)
 def call(stage,fn,z,grad,b,fun,jac):
  q=minimize(fn,z,jac=grad,method='SLSQP',bounds=b,constraints=[dict(type='ineq',fun=fun,jac=jac)],options=dict(maxiter=400,ftol=1e-10,disp=False));res=float(-np.min(fun(q.x)))
  observe(dict(stage=stage,success=bool(q.success),status=int(q.status),message=str(q.message),nit=int(q.nit),nfev=int(q.nfev),objective=float(q.fun),x=q.x.tolist(),maximum_constraint_residual=res));return q,res
 if kind=='PCBF':
  width=n//(N+1);weights=np.asarray([1.]*(n-width)+[100.]*width);z=np.r_[u,np.maximum(initial,0.)]
  fun=lambda z:z[16:]-np.asarray(values_jac(z[:16],case,known,kind)[0]);jac=lambda z:np.c_[-np.asarray(values_jac(z[:16],case,known,kind)[1]),np.eye(n)]
  q,res=call('AUXILIARY',lambda z:float(weights@z[16:]),z,lambda z:np.r_[np.zeros(16),weights],bounds+[(0.,None)]*n,fun,jac)
  if not q.success or res>1e-7 or min(q.x[16:])< -1e-7:return dict(passed=False,refused_stage='AUXILIARY',physical_authority=False)
  slack=np.maximum(q.x[16:],0.);u=q.x[:16]
 def cost(z):return float((gear*z[0]-nominal[0])**2+(gear*z[0]*z[1]-nominal[1])**2)
 def cg(z):
  a=gear*z[0]-nominal[0];b=gear*z[0]*z[1]-nominal[1];g=np.zeros(16);g[0]=2*a*gear+2*b*gear*z[1];g[1]=2*b*gear*z[0];return g
 fun=lambda z:slack-np.asarray(values_jac(z,case,known,kind)[0]);jac=lambda z:-np.asarray(values_jac(z,case,known,kind)[1]);q,res=call('PERFORMANCE',cost,u,cg,bounds,fun,jac)
 values,_,labels=values_jac(q.x,case,known,kind);states,_=rollout_jac(q.x,case['pose'],gear);commands=[[gear*float(q.x[2*i]),gear*float(q.x[2*i]*q.x[2*i+1]),False]for i in range(N)]
 # Independent polygon distances are checked separately from the optimizer constraint callback.
 import oracle
 hard=[REQUIRED-min(oracle.distances(p,known))for p in states];domain=max([abs(v)-.1 for v,w,_ in commands]+[abs(w)-abs(v)*KMAX for v,w,_ in commands]+[-gear*v for v,w,_ in commands])
 residual=max(v-float(s)for v,s in zip(values,slack));assert abs(res-residual)<1e-10
 return dict(passed=bool(q.success and residual<=1e-7 and domain<=1e-7),maximum_residual=residual,maximum_command_domain_violation=domain,original_hard_geometry_passed=max(hard)<=1e-7,maximum_exact_hard_static_residual=max(hard),maximum_slack=float(max(slack)),states=states,commands=commands,slacks=slack.tolist(),constraint_labels=labels,terminal_policy='Ideal zero-input geometric hold; no Phase actuator or uncertainty proof',physical_authority=False,Phase_vehicle_qualified=False,full2200stop_qualified=False,formal_task=False)
