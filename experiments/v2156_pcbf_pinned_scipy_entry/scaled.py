"""Fixed bijective variable units; original objective, gates and problem retained."""
SPEED_UNIT=.1;SLACK_UNIT=.004

def minimizer(np,minimize,notify):
 from kinematics import KMAX
 def call(fun,x0,*,jac,method,bounds,constraints,options):
  assert method=='SLSQP'and options==dict(maxiter=400,ftol=1e-10,disp=False)and len(constraints)==1
  units=np.asarray([SPEED_UNIT,KMAX]*8+[SLACK_UNIT]*(len(x0)-16),float);original=np.asarray(x0,float);y0=original/units
  scaled_bounds=[(None if a is None else a/s,None if b is None else b/s)for(a,b),s in zip(bounds,units)]
  c=constraints[0];assert c['type']=='ineq'
  def f(y):return fun(np.asarray(y)*units)
  def g(y):return np.asarray(jac(np.asarray(y)*units))*units
  def cf(y):return np.asarray(c['fun'](np.asarray(y)*units))/SLACK_UNIT
  def cg(y):return np.asarray(c['jac'](np.asarray(y)*units))*units[None,:]/SLACK_UNIT
  # Cheap exact chain-rule/domain tests before each first SLSQP call.
  assert np.allclose(y0*units,original,rtol=0,atol=1e-15)and abs(f(y0)-fun(original))<1e-12
  q=minimize(f,y0,jac=g,method=method,bounds=scaled_bounds,constraints=[dict(type='ineq',fun=cf,jac=cg)],options=options)
  raw_y=np.asarray(q.x).copy();q.x=raw_y*units;q.fun=float(fun(q.x))
  notify(dict(stage='AUXILIARY'if len(x0)>16 else'PERFORMANCE',scipy_success=bool(q.success),scipy_status=int(q.status),nit=int(q.nit),nfev=int(q.nfev),normalized_x=raw_y.tolist(),original_x=q.x.tolist(),variable_units=units.tolist(),original_objective=q.fun,maximum_original_constraint_residual=float(-np.min(c['fun'](q.x))),constraint_unit=SLACK_UNIT))
  return q
 return call
