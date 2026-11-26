"""One exposed original PCBF auxiliary call, diagnostic only, never a plant."""
import os,sys,json,time,resource,traceback,importlib.abc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import evidence as e
R=e.R;C=e.C;S=e.ROOT
def main():
 a=e.read(S/'MATH_ADMISSION.json')
 assert os.sched_getaffinity(0)=={4}and not a['models_authorized']and a['scope']=='ONE_EXPOSED_ORIGINAL_PCBF_AUXILIARY_DIAGNOSIS'
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['absolute_deadline_unix']and time.monotonic()<a['hard_stop_monotonic']
 assert a['source_freeze_sha256']==e.sha(S/'SOURCE_FREEZE.json')and e.read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 source=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in source.items())
 out=S/'math';assert not(out/'ONCE.json').exists();e.put(out/'ONCE.json',dict(pid=os.getpid(),CPU=4,models=0,NLP_call_cap=1,unix=time.time()))
 resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(80,85))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('NON_PHASE_DIAGNOSTIC_NO_MODEL:'+n)
 sys.meta_path.insert(0,Ban());result=dict(passed=False,closed=False,diagnosis_complete=False,models=0,physics=0,formal_trials=0,NLP_attempts=0,NLP_returns=0,Phase_vehicle_qualified=False,original_failure_reproduced=False);start=time.monotonic()
 try:
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import minimize
  module=e.load('unchanged_original_non_Phase_filter',R/'experiments/v2101_parallel_priest_vehicle/nonlinear_filter.py')
  def observed_minimize(fun,x0,**kwargs):
   assert result['NLP_attempts']==0;result['NLP_attempts']+=1
   initial=dict(x0=np.asarray(x0).tolist(),initial_objective=float(fun(x0)),initial_inequality=kwargs['constraints'][0]['fun'](x0).tolist(),bounds=kwargs['bounds'],method=kwargs['method'],options=kwargs['options'])
   e.put(out/'AUXILIARY_INITIAL.json',initial)
   value=minimize(fun,x0,**kwargs);result['NLP_returns']+=1
   primal=kwargs['constraints'][0]['fun'](value.x);raw=dict(success=bool(value.success),status=int(value.status),message=str(value.message),nit=int(value.nit),nfev=int(value.nfev),njev=int(value.njev),fun=float(value.fun),x=value.x.tolist(),jac=value.jac.tolist(),inequality_at_return=primal.tolist(),maximum_primal_residual=float(-np.min(primal)),solver_success_and_residual_accepted=bool(value.success and -np.min(primal)<=1e-7))
   e.put(out/'AUXILIARY_RAW_RETURN.json',raw);return value
  try:answer=module.solve(np,observed_minimize,kind='PCBF',x0=[1.4,0.,0.],nominal=[.25,0.],N=8)
  except AssertionError as error:
   result.update(first_error=repr(error),traceback=traceback.format_exc(),original_failure_reproduced=str(error)=='NONLINEAR_AUXILIARY_FAILED',diagnosis_complete=result['NLP_returns']==1)
  else:
   e.put(out/'UNEXPECTED_DIFFERENT_RESULT.json',answer);result.update(unexpected_original_failure_not_reproduced=True,diagnosis_complete=True)
  assert result['NLP_attempts']==result['NLP_returns']==1
  result['raw_solver_return_path']=str((out/'AUXILIARY_RAW_RETURN.json').relative_to(R));result['raw_solver_return_sha256']=e.sha(out/'AUXILIARY_RAW_RETURN.json')
 except BaseException as error:result.update(diagnostic_error=repr(error),diagnostic_traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_after=all(e.sha(R/n)==h for n,h in source.items()))
  e.put(out/'RESULT.json',result)
 print(json.dumps(result));return 1 if not result['passed']else 0
if __name__=='__main__':raise SystemExit(main())
