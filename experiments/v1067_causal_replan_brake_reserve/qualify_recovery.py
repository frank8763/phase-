import importlib.abc,sys,json,time,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C))
from handoff import prepare
from atomic import allocate
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());started=time.monotonic();p=prepare(x['setup'],x['packet'],x['source'],x['goal'],x['actions'],x['elapsed']);buffers=allocate(p);assert p['passed']and all(p['complete_profile_checks'].values());assert p['source_kind']in ['INFORMATION_RECOVERY_NOT_ARRIVAL','SAFE_PROGRESS_RECOVERY_NOT_ARRIVAL']and not p['functional_goal_source']and p['information_never_counts_as_arrival'];assert p['pre_adoption_hold_native']==800 and len(p['cross_requests'])>=200 and np.array_equal(np.asarray(p['cross_requests'])[-200:],np.zeros((200,3))) ;dump(O/'NS_ACTUAL_RECOVERY_SOURCE.json',p);result=dict(passed=True,scope='FINITE_SAFE_RECOVERY_CORRIDOR_NOT_ARRIVAL',source_kind=p['source_kind'],minimum_raw_m=p['launch_bounds'][0],complete_profile_checks=p['complete_profile_checks'],terminal_goal_upper_m=p['terminal_goal_upper_m'],full_goal_source_found=False,original_full_goal_failure_retained=True,wall_s=time.monotonic()-started,models=0,integrations=0);dump(O/'NS_RECOVERY_QUALIFICATION.json',result);print(json.dumps(result),flush=True)
