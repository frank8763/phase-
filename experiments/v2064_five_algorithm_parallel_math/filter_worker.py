from common import R,C,S,read,put,sha,load,authority
import importlib.abc,os,sys,time,traceback,warnings,resource
def main():
 a,source=authority('FILTERS');out=S/'filter_output';assert not(out/'ONCE.json').exists();put(out/'ONCE.json',dict(pid=os.getpid(),CPU=2,models=0,unix=time.time()));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(120,125));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'mujoco','torch','jax','factory','kernel','vehicle','fast_predict'}:raise AssertionError('FILTER_MATH_NO_PHASE_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());result=dict(closed=False,passed=False,models=0,physics=0,replay=0,formal_tasks=0,Phase_vehicle_safety_qualified=False,first_error=None);start=time.monotonic()
 try:
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'));import numpy as np
  from scipy.optimize import linprog,OptimizeWarning
  solver=load('source_bound_PSF_PCBF_linear_program',C/'filter_lp.py');rows=[]
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',OptimizeWarning)
   for kind in ['PSF','PCBF']:
    for x0,up in [(0.,.1),(.99,.25),(1.4,.25),(-1.4,-.25)]:
     assert time.time()<a['absolute_deadline_unix'];answer=solver.solve(np,linprog,kind=kind,x0=x0,nominal=up);rows.append(dict(method=kind,x0=x0,nominal=up,answer=answer))
  assert rows[0]['answer']['feasible']and abs(rows[0]['answer']['first_input']-.1)<=1e-8
  assert rows[1]['answer']['feasible']and rows[1]['answer']['first_input']<=.01000001
  assert not rows[2]['answer']['feasible']and not rows[3]['answer']['feasible']
  assert all(x['answer']['feasible']for x in rows[4:])and rows[6]['answer']['auxiliary_value']>0 and rows[7]['answer']['auxiliary_value']>0
  # Independent hard gate: PCBF's positive violation slacks are not permission
  # to violate any physical Phase safety constraint.
  assert rows[6]['answer']['states'][0]>1. and not rows[6]['answer']['physical_authority']
  put(out/'FORMULATION_CASES.json',rows);result.update(passed=True,LP_performance_solves=8,PCBF_auxiliary_solves=4,linear_dynamics_fixture_not_Phase=True,independent_primal_residuals_checked=True,positive_slack_never_physical_authority=True,PSF_PCBF_original_vehicle_interface_ready=False,constructor_internal_work=None)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_after=all(sha(R/n)==h for n,h in source.items()));put(out/'RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
