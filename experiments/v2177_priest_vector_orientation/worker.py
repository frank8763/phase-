"""At most two nonphysical projection NLP calls; missing authority refuses FIRST."""
import os,sys,time,signal,importlib.abc
from context import R,C,ROOT,O,read,put,sha,authority,remaining

def main():
 auth,files=authority()
 with(O/'WORKER_ONCE.json').open('x')as f:f.write('{"claimed":true,"models":0}\n')
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*a):
   if n.split('.')[0]in{'mujoco','torch','jax','OpenGL','factory','kernel','vehicle','fast_predict','coupled_model'}:raise AssertionError('IDEAL_MATH_NO_PLANT_POLICY_OR_MODEL:'+n)
 sys.meta_path.insert(0,Ban());signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FINITE_PROJECTION_MATH_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(auth)))
 from context import load
 from write_budget import Budget
 budget=Budget(O)
 io=load('unchanged_original_math_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
 with io.OutputBoundary(O,budget.reserve):
  sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'))
  import numpy as np
  import scipy
  from scipy.optimize import minimize
  assert scipy.__version__=='1.14.1'
  import runner
  result=runner.run(np,minimize,lambda name,value:put(O/name,value))
  result['all_source_SHA_after']=all(sha(R/n)==h for n,h in files.items())
  if not result['all_source_SHA_after']:result.update(passed=False,source_changed=True)
  result['known_charged_write_bytes_before_terminal']=budget.charged
  result['cumulative_write_limit_bytes']=budget.limit
  put(O/'RESULT.json',result)
 # Summary contains only builtin scalars, not raw np.bool_/arrays.
 print(__import__('json').dumps(dict(passed=bool(result['passed']),closed=True,NLP_returns=int(result['NLP_returns']),attempted_calls=int(result['attempted_calls']),first_error=result.get('first_error'))))
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
