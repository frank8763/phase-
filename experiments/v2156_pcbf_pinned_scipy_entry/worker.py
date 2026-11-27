"""At most12 new nonphysical ideal NLP calls, source-authorized before SciPy."""
import os,sys,time,traceback,importlib.abc,signal
from context import R,C,ROOT,O,read,put,sha,authority

def main():
 auth,files=authority();assert not(O/'WORKER_ONCE.json').exists();put(O/'WORKER_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*_):
   if n.split('.')[0]in{'mujoco','torch','jax','factory','vehicle','kernel','fast_predict','OpenGL'}:raise AssertionError('IDEAL_MATH_NO_PLANT_OR_POLICY:'+n)
 sys.meta_path.insert(0,Ban());signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FINITE_IDEAL_NLP_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,auth['absolute_end_unix']-time.time())
 sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'))
 import numpy as np
 from scipy.optimize import minimize
 import filter as f
 from scaled import minimizer
 result=dict(passed=False,closed=False,models=0,physics=0,replay=0,formal_tasks=0,NLP_returns=0,attempted_calls=0,inflight_unknown=False,cases=[]);index=0
 def evaluate(fn,*a,**k):
  result['attempted_calls']+=1;assert result['attempted_calls']<=12 and time.time()<auth['absolute_end_unix']and time.monotonic()<auth['hard_stop_monotonic'];result['inflight_unknown']=True
  q=minimize(fn,*a,**k);result['NLP_returns']+=1;result['inflight_unknown']=False;return q
 try:
  for case in read(ROOT/'CASES_LOCKED.json')['cases']:
   returns=[];transforms=[];start=time.monotonic()
   def observed(z):returns.append(z);put(O/f'CASE_{index:02d}_RETURN_{len(returns):02d}.json',z)
   def transformed(z):transforms.append(z);put(O/f'CASE_{index:02d}_SCALE_{len(transforms):02d}.json',z)
   answer=f.solve(np,minimizer(np,evaluate,transformed),case['case'],case['known'],'PCBF',observed)
   assert not answer['physical_authority'];row=dict(id=case['id'],answer=answer,returns=returns,transforms=transforms,wall_s=time.monotonic()-start,not_a_physical_or_formal_trial=True)
   put(O/f'CASE_{index:02d}_RESULT.json',row);result['cases'].append(dict(id=case['id'],NLP_returns=len(returns),algorithm_passed=answer.get('passed',False),hard_geometry=answer.get('original_hard_geometry_passed',False),refused_stage=answer.get('refused_stage')));index+=1
  assert all(sha(R/n)==h for n,h in files.items());result.update(passed=True,all_finite_cases_completed=True,all_source_SHA_after=True,mathematical_coordinate_revision_not_vehicle_qualified=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 result.update(closed=True,finished_unix=time.time(),internal_optimizer_work=None,total_modelwork=None);put(O/'RESULT.json',result);print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
