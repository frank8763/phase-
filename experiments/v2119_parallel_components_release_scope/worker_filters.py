"""CPU6 finite new constrained NLPs; no Phase models or physical authority."""
import importlib.abc,os,resource,sys,time,traceback
from common import R,C,S,read,put,authority,sha
def main():
 a,files,out=authority(6,'filters');resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(850,860))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('NON_PHASE_COMPONENT_IMPORT_DENIED:'+n)
 sys.meta_path.insert(0,Ban());start=time.monotonic();rows=[];count=0;result=dict(closed=False,finite_batch_complete=False,models=0,physics=0,replay=0,formal_tasks=0,Phase_vehicle_qualified=False)
 try:
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import minimize
  import bicycle
  for case in read(S/'CASES_LOCKED.json')['cases']:
   for kind in ['PSF','PCBF']:
    assert time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic'];returns=[]
    def observe(value):
     nonlocal count
     count+=1;assert count<=18;returns.append(value);put(out/'LAST_RETURN.json',dict(case=case['id'],kind=kind,total_returns=count,value=value))
    try:answer=bicycle.solve(np,minimize,case,kind,observe)
    except BaseException as x:answer=dict(passed=False,error=repr(x),traceback=traceback.format_exc())
    rows.append(dict(case=case,method=kind,answer=answer,numerical_returns=returns));put(out/'CASES.json',rows)
  accepted=[x for x in rows if x['answer'].get('passed')]
  result.update(finite_batch_complete=True,numerical_cases=len(rows),NLP_returns=count,accepted=len(accepted),expected_refusals=sum('expected_refusal'in x['answer']for x in rows),failed=len(rows)-len(accepted)-sum('expected_refusal'in x['answer']for x in rows),accepted_domain_violation_max=max([x['answer']['maximum_command_domain_violation']for x in accepted],default=None),accepted_hard_terminal_failures=sum(not x['answer']['hard_terminal_passed']for x in accepted),original_status_and_residual_criteria_retained=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start,all_frozen_source_SHA_after=all(sha(R/n)==h for n,h in files.items()));put(out/'RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result['finite_batch_complete']and result['all_frozen_source_SHA_after']else 1
if __name__=='__main__':raise SystemExit(main())
