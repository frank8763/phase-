"""CPU6 finite PSF/PCBF numerical development. No Phase model authority."""
import os,sys,time,json,resource,traceback,importlib.abc
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import evidence as e
R=e.R;C=e.C;S=e.ROOT
def main():
 a=e.read(S/'MATH_ADMISSION.json');assert os.sched_getaffinity(0)=={6}and a['scope']=='FINITE_NON_PHASE_FILTER_DEVELOPMENT'and not a['models_authorized']
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic']
 assert a['source_freeze_sha256']==e.sha(S/'SOURCE_FREEZE.json')and e.read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 files=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in files.items())
 out=S/'math';assert not(out/'ONCE.json').exists();e.put(out/'ONCE.json',dict(pid=os.getpid(),CPU=6,models=0,maximum_NLP_calls=27));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(850,860))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('NON_PHASE_MATH_NO_MODEL:'+n)
 sys.meta_path.insert(0,Ban());start=time.monotonic();rows=[];count=[0];result=dict(closed=False,passed=False,models=0,physics=0,formal_trials=0,Phase_vehicle_qualified=False,first_errors=[])
 try:
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import minimize
  m=e.load('frozen_filter_development',C/'nonlinear_development.py')
  for strategy in e.read(S/'AUTHORIZATION.json')['PSF_PCBF_development_candidates']:
   for kind in ['PSF','PCBF']:
    for x0,nominal in [([0.,0.,0.],[.2,.1]),([1.4,0.,0.],[.25,0.]),([-.1,.1,.3],[.2,-.1])]:
     assert time.time()<a['absolute_end_unix']and time.monotonic()<a['hard_stop_monotonic']
     log=[]
     def observed(v):
      count[0]+=1;assert count[0]<=27;log.append(v);e.put(out/'LAST_NLP_RETURN.json',dict(strategy=strategy,method=kind,x0=x0,return_record=v,count=count[0]))
     try:answer=m.solve(np,minimize,strategy=strategy,kind=kind,x0=x0,nominal=nominal,observe=observed)
     except BaseException as error:answer=dict(passed=False,error=repr(error),traceback=traceback.format_exc());result['first_errors'].append(dict(strategy=strategy,kind=kind,x0=x0,error=repr(error)))
     rows.append(dict(strategy=strategy,method=kind,x0=x0,nominal=nominal,answer=answer,numerical_returns=log));e.put(out/'CASES.json',rows)
  result.update(passed=True,finite_development_complete=True,all_methods_Phase_ready=False,numerical_cases=len(rows),accepted_cases=sum(bool(x['answer'].get('passed'))for x in rows),expected_hard_refusals=sum(bool(x['answer'].get('expected_hard_initial_refusal'))for x in rows),NLP_returns=count[0],original_constraint_tolerance=1e-7,original400iteration_cap=True,no_solver_result_reinterpreted=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_after=all(e.sha(R/n)==h for n,h in files.items()));e.put(out/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
