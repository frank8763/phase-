"""PSF/PCBF nonlinear solver plumbing on an explicit non-Phase fixture.

This component deliberately supplies only its explicit unicycle transition.
This test's unicycle is only a numerical fixture, never a Phase model/theorem.
"""
def solve(np,minimize,*,kind,x0,nominal,N=8):
 assert kind in {'PSF','PCBF'}and N==8
 def rollout(u):
  x=np.asarray(x0,float);rows=[x.copy()]
  for v,w in u.reshape(N,2):x=x+np.array([.1*v*np.cos(x[2]),.1*v*np.sin(x[2]),.1*w]);rows.append(x.copy())
  return np.asarray(rows)
 def residual(z,slacks=None):
  states=rollout(z[:2*N]);g=np.sum(states[:N,:2]**2,axis=1)-1.+(.005*np.arange(N)if kind=='PCBF'else 0.);terminal=np.sum(states[-1,:2]**2)-.25**2
  return np.r_[g,terminal]-(z[2*N:]if slacks is None else slacks)
 n=2*N+(N+1 if kind=='PCBF'else 0);initial=np.zeros(n);bounds=[(-.25,.25)]*(2*N)+([(0.,None)]*(N+1)if kind=='PCBF'else[]);options=dict(maxiter=400,ftol=1e-10,disp=False)
 if kind=='PSF'and np.sum(np.asarray(x0[:2])**2)>1.+1e-12:return dict(feasible=False,reason='INITIAL_HARD_SET_VIOLATION',physical_authority=False,Phase_model=False)
 auxiliary=None;auxvalue=None
 if kind=='PCBF':
  initial[2*N:]=np.maximum(residual(initial),0.)+.1;weights=np.r_[np.ones(N),100.]
  auxiliary=minimize(lambda z:float(weights@z[2*N:]),initial,method='SLSQP',bounds=bounds,constraints=[dict(type='ineq',fun=lambda z:-residual(z))],options=options);assert auxiliary.success and np.max(residual(auxiliary.x))<=1e-7,'NONLINEAR_AUXILIARY_FAILED'
  slacks=np.maximum(auxiliary.x[2*N:],0.);auxvalue=float(weights@slacks);initial=auxiliary.x[:2*N];bounds=bounds[:2*N]
 else:slacks=np.zeros(N+1)
 performance=minimize(lambda z:float(np.sum((z[:2]-np.asarray(nominal))**2)),initial,method='SLSQP',bounds=bounds,constraints=[dict(type='ineq',fun=lambda z:-residual(z,slacks))],options=options)
 if not performance.success:return dict(feasible=False,reason='FINITE_NONLINEAR_SOLVER_REFUSAL',status=int(performance.status),physical_authority=False,Phase_model=False)
 violation=float(np.max(residual(performance.x,slacks)));assert violation<=1e-7
 return dict(feasible=True,method=kind,first_input=performance.x[:2].tolist(),states=rollout(performance.x).tolist(),slacks=slacks.tolist(),auxiliary_value=auxvalue,maximum_primal_residual=violation,physical_authority=False,Phase_model=False,terminal_invariance_proven=False,only_nonlinear_solver_component=True)
