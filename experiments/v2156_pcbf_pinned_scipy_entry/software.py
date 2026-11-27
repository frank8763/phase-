"""Coordinate chain rule and original callback diagnostics; no optimizer call."""
import numpy as np,copy,json
from context import R,C,ROOT,read,put,sha
from scaled import minimizer
import filter as f
proof=[];counter=[]
for width in [16,20]:
 x=np.linspace(.01,.04,width);a=np.arange(width,dtype=float)+1;B=np.vstack([a,a[::-1]])
 fun=lambda z:float(np.sum(z*z));grad=lambda z:2*z;cf=lambda z:B@z+1.;cg=lambda z:B
 def toy(fn,y,**kw):
  h=1e-6;g=kw['jac'](y);J=kw['constraints'][0]['jac'](y)
  fd=np.asarray([(fn(y+np.eye(width)[i]*h)-fn(y-np.eye(width)[i]*h))/(2*h)for i in range(width)])
  fj=np.column_stack([(kw['constraints'][0]['fun'](y+np.eye(width)[i]*h)-kw['constraints'][0]['fun'](y-np.eye(width)[i]*h))/(2*h)for i in range(width)])
  assert np.max(abs(fd-g))<1e-8 and np.max(abs(fj-J))<1e-5
  return __import__('types').SimpleNamespace(x=y,success=True,status=0,nit=0,nfev=0,fun=fn(y))
 q=minimizer(np,toy,counter.append)(fun,x,jac=grad,method='SLSQP',bounds=[(0.,None)]*width,constraints=[dict(type='ineq',fun=cf,jac=cg)],options=dict(maxiter=400,ftol=1e-10,disp=False))
 assert np.max(abs(q.x-x))<1e-15 and abs(q.fun-fun(x))<1e-15;proof.append(dict(width=width,chain_rule_positive=True))
# Only original callback evaluations on saved inputs, no SLSQP or model.
for row in read(ROOT/'CASES_LOCKED.json')['cases'][:4]:
 case=row['case'];known=row['known'];z=np.asarray([.05,0.]*8);v,j,_=f.values_jac(z,case,known,'PCBF');J=np.asarray(j);h=1e-6
 fd=np.column_stack([(np.asarray(f.values_jac(z+np.eye(16)[i]*h,case,known,'PCBF')[0])-np.asarray(f.values_jac(z-np.eye(16)[i]*h,case,known,'PCBF')[0]))/(2*h)for i in range(16)])
 proof.append(dict(case=row['id'],original_callback_maximum_FD_error=float(np.max(abs(J-fd))),diagnostic_only=True,no_convergence_claim=True))
for n in ['common.py','geometry.py','kinematics.py','oracle.py','request.py','filter.py']:assert(C/n).read_bytes()==(R/'experiments/v2141_pcbf_progress_scope'/n).read_bytes()
put(ROOT/'SOFTWARE_PROOF.json',dict(passed=True,models=0,optimizer_calls=0,physics=0,replay=0,fixed_units_chain_rule_checks=proof,original_objective_retained=True,original_gate_and_math_bytes_exact=True,coordinate_minimizer_is_new_declared_numerical_adapter=True));print(json.dumps(dict(passed=True,models=0,optimizer_calls=0)))
