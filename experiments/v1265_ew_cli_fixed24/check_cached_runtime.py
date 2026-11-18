"""Actual runtime binding before and after old-module preload; zero models."""
import importlib.abc,sys
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','torch','rclpy'}:raise AssertionError('CACHED_BINDING_ZERO_MODELS '+name)
sys.meta_path.insert(0,NoModels())
from worker_context import *
import types
import route_dispatch

def main(case):
 assert not read(O/'APPROVAL.json')['models_authorized']
 old=science()
 saved={}
 if case=='prebind_then_legacy':
  bound=route_dispatch.current_executor()
 saved['admission']=load('admission',R/'runtime/mk-mini/experiments/phase_rpccr_p0b57_v1/admission.py')
 for name in ['goal_entry','current_goal_source','candidate_search','connection','live_entry','audit_admission']:
  m=types.ModuleType(name);m.__file__='synthetic_wrong_'+name;sys.modules[name]=m;saved[name]=m
 # Full production owner configuration must bind new private code independently
 # of both old module cache and sys.path order. No vehicle factory is called.
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 owner=configure_owner(O,now+1000,window);entry=route_dispatch.current_executor()
 assert callable(owner.navigate)and callable(owner.execute)
 assert entry.goal_entry.__name__=='phase_v1218_goal.goal_entry'
 assert entry.goal_entry.generate.__module__=='phase_v1218_goal.current_goal_source'
 assert entry.goal_entry.predictor_origin.__module__=='phase_v1218_goal.admission'
 if case=='prebind_then_legacy':assert bound is entry
 ns=route_dispatch.ns_executor();assert ns.goal_entry.__name__=='phase_v1246_ns_goal.goal_entry'
 assert ns.goal_entry.generate.__module__=='phase_v1246_ns_goal.current_goal_source'
 assert all(sys.modules[n]is m for n,m in saved.items()),'LEGACY_MODULE_OBJECT_CHANGED'
 ew=route_dispatch.ew_executor();assert callable(ew.initialize_component_adapter)and Path(ew.__file__).resolve()==R/'experiments/v1261_ew_reserved_validation/ew_live.py'
 for name in ['admission','connection','candidate_search','current_goal_source']:
  assert sys.modules['phase_v1218_goal.'+name].R==R,name
 print(json.dumps(dict(passed=True,case=case,production_owner_bound=True,actual_live_entry=str(Path(entry.__file__).relative_to(R)),science_package=entry.goal_entry.__name__,old_modules_untouched=True,models=0,new_mujoco_native=0)))
if __name__=='__main__':main(sys.argv[1])
