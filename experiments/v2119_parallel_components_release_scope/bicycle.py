"""Explicit ideal speed-curvature fixture. No Phase model or solver imports."""
import math
N=8;DT=.1;KMAX=1/1.32
def rollout_jac(z,x0,gear):
 assert gear in(-1,1)and len(z)==2*N and len(x0)==3
 x=list(map(float,x0));J=[[0.]*16 for _ in range(3)];states=[x[:]];jacs=[[r[:]for r in J]]
 for i in range(N):
  s,k=z[2*i:2*i+2];v=gear*s;yaw=x[2];co,si=math.cos(yaw),math.sin(yaw)
  a=DT*v;new=[[J[0][j]-a*si*J[2][j]for j in range(16)],[J[1][j]+a*co*J[2][j]for j in range(16)],J[2][:]]
  new[0][2*i]+=DT*gear*co;new[1][2*i]+=DT*gear*si
  new[2][2*i]+=DT*gear*k;new[2][2*i+1]+=DT*v
  x=[x[0]+a*co,x[1]+a*si,x[2]+DT*v*k];J=new
  states.append(x[:]);jacs.append([r[:]for r in J])
 return states,jacs
def values_jac(z,x0,gear,kind):
 states,jacs=rollout_jac(z,x0,gear);v=[];g=[]
 for i in range(N+1):
  r2=states[i][0]**2+states[i][1]**2
  v.append(r2-(.25**2 if i==N else 1.)+(.005*i if kind=='PCBF'and i<N else 0.))
  g.append([2*states[i][0]*jacs[i][0][j]+2*states[i][1]*jacs[i][1][j]for j in range(16)])
 return v,g
def solve(np,minimize,case,kind,observe):
 x0=case['state'];gear=case['gear'];nominal=case['nominal_twist'];assert kind in['PSF','PCBF']
 if kind=='PSF':
  if math.hypot(*x0[:2])>1.+1e-12:return dict(passed=False,expected_refusal='INITIAL_HARD_SET')
  if math.hypot(*x0[:2])-N*DT*.1>.25+1e-12:return dict(passed=False,expected_refusal='NECESSARY_TERMINAL_REACHABILITY_BOUND')
 bounds=[(.005,.1),(-KMAX,KMAX)]*N;u=np.asarray([.05,0.]*N);slack=np.zeros(N+1)
 options=dict(maxiter=400,ftol=1e-10,disp=False)
 def call(stage,fn,initial,grad,bounds,fun,jac):
  q=minimize(fn,initial,jac=grad,method='SLSQP',bounds=bounds,constraints=[dict(type='ineq',fun=fun,jac=jac)],options=options)
  residual=float(-np.min(fun(q.x)));observe(dict(stage=stage,success=bool(q.success),status=int(q.status),message=str(q.message),nit=int(q.nit),nfev=int(q.nfev),x=q.x.tolist(),fun=float(q.fun),maximum_constraint_residual=residual))
  return q,residual
 if kind=='PCBF':
  weights=np.asarray([1.]*N+[100.]);v,_=values_jac(u,x0,gear,kind);initial=np.r_[u,np.maximum(v,0.)+.1]
  fn=lambda z:float(weights@z[16:]);grad=lambda z:np.r_[np.zeros(16),weights]
  gf=lambda z:z[16:]-np.asarray(values_jac(z[:16],x0,gear,kind)[0])
  gj=lambda z:np.c_[-np.asarray(values_jac(z[:16],x0,gear,kind)[1]),np.eye(N+1)]
  aux,res=call('AUXILIARY',fn,initial,grad,bounds+[(0.,None)]*(N+1),gf,gj)
  if not aux.success or res>1e-7 or min(aux.x[16:])< -1e-7:return dict(passed=False,refused_stage='AUXILIARY')
  slack=np.maximum(aux.x[16:],0.);u=aux.x[:16]
 def perf(z):
  v=gear*z[0];w=v*z[1];return float((v-nominal[0])**2+(w-nominal[1])**2)
 def pg(z):
  v=gear*z[0];w=v*z[1];g=np.zeros(16);g[0]=2*(v-nominal[0])*gear+2*(w-nominal[1])*gear*z[1];g[1]=2*(w-nominal[1])*v;return g
 gf=lambda z:slack-np.asarray(values_jac(z,x0,gear,kind)[0])
 gj=lambda z:-np.asarray(values_jac(z,x0,gear,kind)[1])
 q,res=call('PERFORMANCE',perf,u,pg,bounds,gf,gj)
 # Separate scalar reconstruction, not reuse of the derivative transition.
 x=list(x0);states=[x[:]];commands=[]
 for i in range(N):
  s,k=map(float,q.x[2*i:2*i+2]);v=gear*s;w=v*k;commands.append([v,w,False]);x=[x[0]+.1*v*math.cos(x[2]),x[1]+.1*v*math.sin(x[2]),x[2]+.1*w];states.append(x[:])
 values=[states[i][0]**2+states[i][1]**2-(.25**2 if i==N else 1.)+(.005*i if kind=='PCBF'and i<N else 0.)-float(slack[i])for i in range(N+1)]
 deadband=max([0.]+[abs(w)-1e-6 for v,w,_ in commands if abs(v)<.005])
 domain=max([deadband]+[abs(v)-.1 for v,w,_ in commands]+[abs(w)-abs(v)*KMAX for v,w,_ in commands]+[-gear*v for v,w,_ in commands])
 rollout,_=rollout_jac(q.x,x0,gear);error=max(abs(a-b)for x,y in zip(states,rollout)for a,b in zip(x,y));assert error<=1e-12 and abs(max(values)-res)<=1e-10
 return dict(passed=bool(q.success and max(values)<=1e-7 and domain<=1e-7),solver_success=bool(q.success),states=states,commands=commands,terminal_zero_command=[0.,0.,False],slacks=slack.tolist(),maximum_independent_residual=max(values),maximum_command_domain_violation=domain,scalar_transition_error=error,hard_terminal_residual=x[0]**2+x[1]**2-.25**2,hard_terminal_passed=x[0]**2+x[1]**2<=.25**2+1e-7,Phase_vehicle_qualified=False,full2200stop_qualified=False,uncertainty_qualified=False,steering_slew_qualified=False,terminal_policy_scope='Ideal static kinematic zero-input hold only')
