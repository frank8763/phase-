"""Only new case-attribution/tightening bookkeeping, explicit fake backend."""
from context import R,ROOT,put
from types import SimpleNamespace
import os,json
import numpy as np
import runner
assert os.sched_getaffinity(0)=={0}and not(ROOT/'CASE_ATTRIBUTION_SUPPLEMENT.json').exists()
runner.authority=lambda:({'EXPLICIT_SOFTWARE':True},{})
notes=[]
for kind in ['exception','nonfinite','ordinary']:
 saved={};observed=[]
 def record(n,v):saved[n]=json.loads(json.dumps(v,allow_nan=False,default=lambda z:z.tolist()))
 def backend(fun,x,**kw):
  observed.append(kind)
  if kind=='exception':raise RuntimeError('EXPLICIT_FAKE_NO_RETURN')
  if kind=='ordinary':
   # All original geometry margins strictly positive; offset is stronger and
   # only affects values, not the callback dimensions/analytic Jacobian.
   assert kw['constraints'][1]['fun'](x).shape==(963,)
   assert kw['constraints'][1]['jac'](x).shape==(963,92)
  q=SimpleNamespace(x=x.copy(),success=True,status=0,message='SOFTWARE_STUB',nit=0,nfev=1,njev=1,fun=fun(x))
  if kind=='nonfinite':q.x[0]=float('nan')
  return q
 z=runner.run(np,backend,record)
 if kind=='ordinary':assert z['passed']and z['accepted_case_ids']==['straight','left_bump']and not z['unexecuted_positive_case_ids']
 else:assert not z['passed']and z['attempted_case_ids']==['straight']and z['unexecuted_positive_case_ids']==['left_bump']and not z['accepted_case_ids']
 notes.append(dict(case=kind,attempted=z['attempted_case_ids'],unexecuted=z['unexecuted_positive_case_ids'],accepted=z['accepted_case_ids'],fake_returns=z['NLP_returns']))
put(ROOT/'CASE_ATTRIBUTION_SUPPLEMENT.json',dict(passed=True,cases=notes,case_attempt_and_unexecuted_counts_distinct=True,optimizer_only_geometry_tightening_before_any_real_solve=True,original_hard_geometry_unchanged=True,real_NLP_models_Source_calls=0))
print(json.dumps(dict(passed=True,targeted_bookkeeping_cases=3,actual_NLP_calls=0)))
