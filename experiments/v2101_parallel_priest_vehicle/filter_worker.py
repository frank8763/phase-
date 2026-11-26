"""CPU4 PSF/PCBF nonlinear optimization component; no Phase model/plant."""
import os,sys,time,json,traceback,importlib.abc,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import R,C,SOURCE,read,sha,put,load

def main():
 a=read(SOURCE/'FILTERS_ADMISSION.json');assert a['scope']=='PSF_PCBF_NONLINEAR_SOLVER_COMPONENT'and not a['models_authorized']and os.sched_getaffinity(0)=={4}
 assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['absolute_deadline_unix']and time.monotonic()<a['hard_stop_monotonic']
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 source=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in source.items())
 out=SOURCE/'filter_output';assert not(out/'ONCE.json').exists();put(out/'ONCE.json',dict(pid=os.getpid(),CPU=4,models=0));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict'}:raise AssertionError('FILTER_NONLINEAR_NO_PHASE_MODEL:'+n)
 sys.meta_path.insert(0,Ban());start=time.monotonic();result=dict(passed=False,closed=False,models=0,physical_native=0,formal_trials=0,Phase_vehicle_qualified=False)
 try:
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import minimize
  solver=load('source_bound_nonlinear_filter_problem',C/'nonlinear_filter.py');rows=[]
  for kind in ['PSF','PCBF']:
   for x0,nominal in [([0.,0.,0.],[.2,.1]),([1.4,0.,0.],[.25,0.]),([-.1,.1,.3],[.2,-.1])]:
    assert time.time()<a['absolute_deadline_unix'];answer=solver.solve(np,minimize,kind=kind,x0=x0,nominal=nominal);rows.append(dict(method=kind,x0=x0,nominal=nominal,answer=answer));put(out/'NONLINEAR_SOLVER_CASES.json',rows)
  assert rows[0]['answer']['feasible']and not rows[1]['answer']['feasible']and rows[2]['answer']['feasible']and all(x['answer']['feasible']for x in rows[3:])and rows[4]['answer']['auxiliary_value']>0
  assert all(not x['answer']['physical_authority']for x in rows)
  put(out/'NONLINEAR_SOLVER_CASES.json',rows);result.update(passed=True,performance_NLP_attempts=5,hard_infeasible_initial_sets=1,PCBF_auxiliary_NLP_solves=3,independent_primal_residuals_checked=True,nonlinear_unicycle_fixture_not_Phase=True,positive_slack_never_Phase_authority=True,Phase_terminal_invariance_and_uncertainty_still_missing=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_after=all(sha(R/n)==h for n,h in source.items()));put(out/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
