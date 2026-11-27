"""Source-guarded fixed projection cases. Backend injected only for software probes."""
from context import ROOT,O,read,put,authority

def run(np,minimize,record):
 authority() # unadmitted direct calls cannot execute a real optimizer
 from collocation import Projection,geometry,VMAX,AMAX,KMAX
 from normalized import Normalized
 import time,math
 locked=read(ROOT/'CASES_LOCKED.json');known=read(ROOT/'PUBLIC_VECTOR_INPUT.json')
 result=dict(passed=False,closed=False,models=0,physics=0,replay=0,formal_tasks=0,attempted_calls=0,attempted_case_ids=[],accepted_case_ids=[],NLP_returns=0,inflight_unknown=False,cases=[],unexecuted_positive_case_ids=[x['id']for x in locked['positive_cases']],internal_optimizer_work=None,compiled_SLSQP_FFI_calls=None)
 def durable():record('MATH_PROGRESS.json',result)
 try:
  blocked=dict(known,known_circles=known['known_circles']+[locked['occupied_negative_circle']]);p=Projection(blocked);b=p.evaluate(p.initial)
  assert b['minimum_sampled_clearance']<geometry.REQUIRED
  result['occupied_negative']=dict(refused_before_optimizer=True,minimum_clearance_m=b['minimum_sampled_clearance'],NLP_calls=0);record('OCCUPIED_NEGATIVE.json',result['occupied_negative']);durable()
  for case in locked['positive_cases']:
   p=Projection(known)
   if case['reference']=='CURVATURE_BUDGET_LEFT_BUMP':
    delta=KMAX*.6**2/(8*math.pi**2)
    for i,t in enumerate(np.linspace(0,p.H,p.N+1)):p.reference[3*i+1]+=(delta*math.sin(math.pi*float(t)/p.H)**2)
   else:assert case['reference']=='STRAIGHT_BERNSTEIN'
   normalized=Normalized(p);w0=np.zeros(len(p.initial));lo,hi=normalized.bounds();first=p.evaluate(p.initial)
   assert first['minimum_sampled_clearance']>=geometry.REQUIRED and abs(first['equalities']).max()<=1e-12 and first['inequalities'].min()>=-1e-12
   geometry_width=len(geometry.feature([-4.,-2.,0.],known)[0]);geometry_rows=np.ones(len(normalized.evaluate(w0)['inequalities']),dtype=bool);geometry_rows[(p.N+1)*geometry_width+np.arange(p.N)*(geometry_width+1)+geometry_width]=False
   geometry_buffer_scaled=10*1e-8 # optimizer-only tightening; original hard geometry acceptance stays exact
   evaluations=dict(objective=0,objective_jacobian=0,equality=0,equality_jacobian=0,inequality=0,inequality_jacobian=0);cache={}
   def arrays(w):
    key=np.asarray(w,float).tobytes()
    if cache.get('key')!=key:cache.clear();cache.update(key=key,result=normalized.evaluate(w))
    return cache['result']
   def fun(w):evaluations['objective']+=1;return normalized.objective(w)[0]
   def jac(w):evaluations['objective_jacobian']+=1;return normalized.objective(w)[1]
   def eq(w):evaluations['equality']+=1;return arrays(w)['equalities']
   def eqjac(w):evaluations['equality_jacobian']+=1;return arrays(w)['equality_jacobian']
   def ing(w):
    evaluations['inequality']+=1;value=arrays(w)['inequalities'].copy();value[geometry_rows]-=geometry_buffer_scaled;return value
   def ingjac(w):evaluations['inequality_jacobian']+=1;return arrays(w)['inequality_jacobian']
   initial_objective=float(normalized.objective(w0)[0]);record(case['id']+'_INPUT.json',dict(case=case,known=known,initial_free=p.initial,normalized_initial=w0,initial_objective=initial_objective,reference=p.reference,physical_authority=False))
   result['attempted_calls']+=1;result['attempted_case_ids'].append(case['id']);result['unexecuted_positive_case_ids'].remove(case['id']);assert result['attempted_calls']<=2;result['inflight_unknown']=True;durable();start=time.monotonic()
   answer=minimize(fun,w0,jac=jac,bounds=list(zip(lo,hi)),constraints=[dict(type='eq',fun=eq,jac=eqjac),dict(type='ineq',fun=ing,jac=ingjac)],method='SLSQP',options=dict(maxiter=200,ftol=1e-10,disp=False))
   result['NLP_returns']+=1;result['inflight_unknown']=False
   raw_x=np.asarray(answer.x,float);raw_fun=float(answer.fun)
   returned=dict(success=bool(answer.success),status=int(answer.status),message=str(answer.message),x=raw_x.tolist()if np.isfinite(raw_x).all()else None,fun=raw_fun if math.isfinite(raw_fun)else None,raw_x_dtype=str(raw_x.dtype),raw_x_shape=list(raw_x.shape),raw_x_bytes_hex=raw_x.tobytes().hex(),raw_fun_float_hex=raw_fun.hex(),nonfinite_return=not(np.isfinite(raw_x).all()and math.isfinite(raw_fun)),nit=int(answer.nit),nfev=int(answer.nfev),njev=int(answer.njev),wall_s=time.monotonic()-start,callback_evaluations=evaluations.copy(),internal_compiled_work=None)
   record(case['id']+'_RAW_RETURN.json',returned) # durable BEFORE any acceptance assertion
   assert np.asarray(answer.x).shape==w0.shape and np.isfinite(answer.x).all()and math.isfinite(answer.fun),'NONFINITE_OR_WRONG_SOLVER_RETURN'
   z=normalized.original(answer.x);checked=p.evaluate(z);objective=float(p.objective(z)[0]);max_eq=float(abs(checked['equalities']).max());min_ineq=float(checked['inequalities'].min());min_clear=checked['minimum_sampled_clearance'];speed=float(max(checked['speeds']));min_speed=float(min(checked['speeds']));accel=float(abs(np.diff(checked['speeds'])/p.h).max());curvature=float(abs(checked['curvatures']).max())
   gates=dict(solver_success=bool(answer.success),solver_status_zero=int(answer.status)==0,kinematic_residual=max_eq<=1e-8,mathematical_inequality_residual=min_ineq>=-1e-8,unchanged_hard_geometry=min_clear>=geometry.REQUIRED,tightened_proposal_geometry=float((checked['inequalities'][geometry_rows]-geometry_buffer_scaled).min())>=-1e-8,unit_bounds=bool((answer.x>=lo-1e-10).all()and(answer.x<=hi+1e-10).all()),objective_not_increased=objective<=initial_objective+1e-10)
   row=dict(id=case['id'],optimizer_only_geometry_buffer_m=geometry_buffer_scaled*geometry.REQUIRED,passed=bool(all(gates.values())),gates=gates,maximum_equality_residual=max_eq,minimum_scaled_inequality=min_ineq,minimum_sampled_clearance_m=min_clear,required_clearance_m=geometry.REQUIRED,max_speed=speed,min_speed=min_speed,max_acceleration=accel,max_curvature=curvature,objective_initial=initial_objective,objective_final=objective,original_free=z,poses=checked['poses'],speeds=checked['speeds'],curvatures=checked['curvatures'],source_math_only_not_vehicle_or_author_PRIEST=True)
   record(case['id']+'_CHECKED_RETURN.json',row);result['cases'].append(dict(id=case['id'],passed=row['passed'],status=returned['status'],nit=returned['nit'],residual=max_eq,minimum_clearance_m=min_clear));durable()
   assert row['passed'],'STRICT_PROJECTION_SOLVER_OR_RESIDUAL_GATE_REFUSED'
   result['accepted_case_ids'].append(case['id'])
  result.update(passed=True,all_fixed_positive_cases_completed=True,occupied_negative_before_NLP=True)
 except BaseException as e:
  import traceback
  result.update(first_error=repr(e),traceback=traceback.format_exc())
 result['closed']=True;result['finished_unix']=time.time();return result
