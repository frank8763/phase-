"""Real case dispatcher + original writer with explicit FAKE optimizer only."""
from context import R,C,ROOT,O,read,put,load
from pathlib import Path
from types import SimpleNamespace
import copy,json,os,sys
import numpy as np
assert os.sched_getaffinity(0)=={0}and not(ROOT/'CASE_WORKER_SOFTWARE_PROOF.json').exists()
import runner
calls=[];saved={}
def record(name,value):
 # The production serializer must accept every raw result before gate checks.
 raw=json.dumps(value,allow_nan=False,default=lambda x:x.tolist());saved[name]=json.loads(raw)
def fake_min(fn,w,**kw):
 assert kw['method']=='SLSQP'and kw['options']==dict(maxiter=200,ftol=1e-10,disp=False)
 assert len(w)==92 and kw['constraints'][0]['fun'](w).shape==(60,)and kw['constraints'][1]['fun'](w).shape==(963,)
 assert kw['jac'](w).shape==(92,)and kw['constraints'][0]['jac'](w).shape==(60,92)
 calls.append('EXPLICIT_FAKE_OPTIMIZER_RETURN_NOT_A_SOLVE')
 return SimpleNamespace(x=w.copy(),success=np.bool_(True),status=np.int64(0),message='SOFTWARE_STUB',nit=np.int64(0),nfev=np.int64(1),njev=np.int64(1),fun=np.float64(fn(w)))
# Actual entry must refuse before it reaches the supplied backend.
try:runner.run(np,fake_min,record)
except FileNotFoundError as e:assert Path(e.filename)==O/'NUMERICAL_ADMISSION.json'and not calls
else:raise AssertionError('UNADMITTED_RUNNER_ACCEPTED')
runner.authority=lambda:({'EXPLICIT_SOFTWARE_FIXTURE':True},{})
positive=runner.run(np,fake_min,record);assert positive['passed']and len(calls)==2 and positive['NLP_returns']==2 and positive['occupied_negative']['NLP_calls']==0
negative=[]
for label in ['status8','exception','nonfinite_x','nonfinite_fun','wrong_shape']:
 saved={};count=[]
 def bad(fn,w,**kw):
  count.append(label)
  if label=='exception':raise RuntimeError('EXPLICIT_FAKE_BACKEND_EXCEPTION')
  q=fake_min(fn,w,**kw)
  if label=='status8':q.success=False;q.status=8
  if label=='nonfinite_x':q.x[0]=float('nan')
  if label=='nonfinite_fun':q.fun=float('inf')
  if label=='wrong_shape':q.x=q.x[:-1]
  return q
 out=runner.run(np,bad,record);assert not out['passed']and len(count)==1 and out['unexecuted_positive_case_ids']
 if label=='exception':assert out['NLP_returns']==0 and out['inflight_unknown']
 else:assert out['NLP_returns']==1 and not out['inflight_unknown']and 'straight_RAW_RETURN.json'in saved
 if label.startswith('nonfinite'):assert saved['straight_RAW_RETURN.json']['nonfinite_return']and 'NONFINITE_OR_WRONG_SOLVER_RETURN'in out['first_error']
 negative.append(dict(case=label,only_one_backend_stub_attempt=len(count),first_error=out['first_error'],raw_return_serialized='straight_RAW_RETURN.json'in saved,inflight_unknown=out['inflight_unknown']))
# Actual original Python output boundary + new byte counter; all own test data.
from write_budget import Budget
io=load('C2177_original_IO_software_probe',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');folder=ROOT/'software_writer';folder.mkdir(exist_ok=False);budget=Budget(folder)
with io.OutputBoundary(folder,budget.reserve):
 put(folder/'FINITE_NUMPY_FIXTURE.json',dict(a=np.array([.1,.2]),b=np.bool_(True),status=np.int64(0)))
 assert read(folder/'FINITE_NUMPY_FIXTURE.json')['b']is True
 try:
  with(folder/'OVERFLOW_NOT_WRITTEN.bin').open('wb')as f:f.write(b'x'*1024**2)
 except AssertionError as e:assert str(e)=='MATH_CUMULATIVE_1MIB_WRITE_GRANT'
 else:raise AssertionError('BYTE_LIMIT_NOT_ENFORCED')
 try:(ROOT/'FOREIGN_WRITE_MUST_NOT_EXIST').write_text('forbidden')
 except AssertionError as e:assert str(e)=='BOUNDED_OUTPUT_PATH_ESCAPE'
 else:raise AssertionError('FOREIGN_WRITE_ACCEPTED')
assert not(ROOT/'FOREIGN_WRITE_MUST_NOT_EXIST').exists()and(folder/'OVERFLOW_NOT_WRITTEN.bin').stat().st_size==0
assert 'scipy'not in sys.modules and 'mujoco'not in sys.modules and 'torch'not in sys.modules
put(ROOT/'CASE_WORKER_SOFTWARE_PROOF.json',dict(passed=True,closed=True,scope='ACTUAL_MATH_CASE_DISPATCHER_WITH_EXPLICIT_FAKE_BACKEND',unadmitted_direct_runner_refused=True,positive_stub_returns=2,negative_cases=negative,occupied_negative_before_backend=True,actual_original_OutputBoundary_positive_overflow_escape_and_NumPy_serializer_passed=True,writer_charged_bytes=budget.charged,actual_NLP_solver_model_physics_Source_calls=0))
print(json.dumps(dict(passed=True,positive_return_stubs=2,failure_cases=len(negative),real_NLP_calls=0,real_byte_writer_passed=True)))
