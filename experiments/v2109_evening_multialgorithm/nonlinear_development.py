"""Three preregistered numerical strategies on the same explicit unicycle NLP."""
def states_and_jac(np,u,x0,N=8):
 x=np.asarray(x0,float);J=np.zeros((3,2*N));states=[x.copy()];jac=[J.copy()]
 for i,(v,w)in enumerate(np.asarray(u).reshape(N,2)):
  yaw=x[2];A=np.array([[1.,0.,-.1*v*np.sin(yaw)],[0.,1.,.1*v*np.cos(yaw)],[0.,0.,1.]])
  J=A@J;J[:,2*i]+=[.1*np.cos(yaw),.1*np.sin(yaw),0.];J[:,2*i+1]+=[0.,0.,.1]
  x=x+np.array([.1*v*np.cos(yaw),.1*v*np.sin(yaw),.1*w]);states.append(x.copy());jac.append(J.copy())
 return np.asarray(states),np.asarray(jac)
def constraint_values_jac(np,u,x0,kind):
 states,jac=states_and_jac(np,u,x0);values=[];rows=[]
 for i in range(8):
  values.append(float(states[i,:2]@states[i,:2]-1.+(.005*i if kind=='PCBF'else 0.)))
  rows.append(2*states[i,:2]@jac[i,:2])
 values.append(float(states[-1,:2]@states[-1,:2]-.25**2));rows.append(2*states[-1,:2]@jac[-1,:2])
 return np.asarray(values),np.asarray(rows)
def solve(np,minimize,*,strategy,kind,x0,nominal,observe):
 assert strategy in ['analytic_jacobian','analytic_jacobian_scaled_objective','analytic_jacobian_positive_slack_start']and kind in ['PSF','PCBF']
 if kind=='PSF'and sum(x*x for x in x0[:2])>1.+1e-12:return dict(passed=False,expected_hard_initial_refusal=True,models=0,physical_authority=False)
 options=dict(maxiter=400,ftol=1e-10,disp=False);u=np.zeros(16);bounds=[(-.25,.25)]*16
 if strategy.endswith('positive_slack_start'):u[::2]=-.25 if x0[0]>0 else .0
 weights=np.r_[np.ones(8),100.];slack=np.zeros(9);aux=None
 def call(stage,fn,x0,kwargs):
  value=minimize(fn,x0,**kwargs)
  g=kwargs['constraints'][0]['fun'](value.x);res=float(-np.min(g));observe(dict(stage=stage,success=bool(value.success),status=int(value.status),message=str(value.message),nit=int(value.nit),nfev=int(value.nfev),njev=int(value.njev),fun=float(value.fun),x=value.x.tolist(),maximum_primal_residual=res))
  return value,res
 if kind=='PCBF':
  v,j=constraint_values_jac(np,u,x0,kind);z=np.r_[u,np.maximum(v,0.)+.1];scale=1. if strategy=='analytic_jacobian'else 100.
  def fun(z):return float(weights@z[16:]/scale)
  def grad(z):return np.r_[np.zeros(16),weights/scale]
  def g(z):return z[16:]-constraint_values_jac(np,z[:16],x0,kind)[0]
  def gj(z):return np.c_[-constraint_values_jac(np,z[:16],x0,kind)[1],np.eye(9)]
  aux,res=call('AUXILIARY',fun,z,dict(method='SLSQP',jac=grad,bounds=bounds+[(0.,None)]*9,constraints=[dict(type='ineq',fun=g,jac=gj)],options=options))
  if not aux.success or res>1e-7 or min(aux.x[16:])< -1e-7:return dict(passed=False,refused_stage='AUXILIARY',models=0,physical_authority=False)
  u=aux.x[:16];slack=np.maximum(aux.x[16:],0.)
 def pf(z):return float(np.sum((z[:2]-np.asarray(nominal))**2))
 def pg(z):return np.r_[2*(z[:2]-np.asarray(nominal)),np.zeros(14)]
 def g(z):return slack-constraint_values_jac(np,z,x0,kind)[0]
 def gj(z):return -constraint_values_jac(np,z,x0,kind)[1]
 perf,res=call('PERFORMANCE',pf,u,dict(method='SLSQP',jac=pg,bounds=bounds,constraints=[dict(type='ineq',fun=g,jac=gj)],options=options))
 states,_=states_and_jac(np,perf.x,x0)
 # Independent direct scalar rollout/residual, not derivative implementation.
 import math
 x=list(x0);rows=[x[:]]
 for i in range(8):
  v,w=map(float,perf.x[2*i:2*i+2]);x=[x[0]+.1*v*math.cos(x[2]),x[1]+.1*v*math.sin(x[2]),x[2]+.1*w];rows.append(x[:])
 independent=[rows[i][0]**2+rows[i][1]**2-1.+(.005*i if kind=='PCBF'else 0.)-float(slack[i])for i in range(8)]+[rows[-1][0]**2+rows[-1][1]**2-.25**2-float(slack[-1])]
 bound=max(abs(float(v))-.25 for v in perf.x);passed=bool(perf.success and max(independent)<=1e-7 and bound<=1e-7)
 return dict(passed=passed,solver_success=bool(perf.success),maximum_independent_primal_residual=max(independent),maximum_input_bound_violation=bound,first_input=perf.x[:2].tolist(),slacks=slack.tolist(),original_auxiliary_value=None if kind=='PSF'else float(weights@slack),states=rows,analytic_rollout_matches_independent=bool(np.max(abs(states-np.asarray(rows)))<=1e-12),models=0,physical_authority=False,Phase_vehicle_qualified=False,terminal_invariance_proven=False)
