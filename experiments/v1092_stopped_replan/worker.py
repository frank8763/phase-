"""One fresh route worker with a bounded measured-state active recovery policy."""
import sys,types,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));sys.path.insert(0,str(C))
def load_prior():
 sp=importlib.util.spec_from_file_location('active_recovery_prior_worker',R/'experiments/v1089_route_scene_contract/worker.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def configure():
 import pipeline
 sys.modules['fresh_pipeline']=pipeline
 import owner
 original=owner.navigate
 def navigate(v,setup,task,end,out,result):
  # The same actual segment list is created inside the old owner before recovery.
  owner._active_corridor_result=result
  return original(v,setup,task,end,out,result)
 owner.navigate=navigate
def patched_source():
 prior=load_prior();s=prior.patched_source();assert s.count('time.time()+900')==1;s=s.replace('time.time()+900','time.time()+1200');return prior.ORIGINAL,s
def load_worker():
 configure();prior=load_prior();prior.configure();original,s=patched_source();m=types.ModuleType('active_corridor_worker');m.__file__=str(original);exec(compile(s,str(original),'exec'),m.__dict__);return m
if __name__=='__main__':
 configure();prior=load_prior();prior.configure();original,s=patched_source();exec(compile(s,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
