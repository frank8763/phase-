"""One original saved-state source probe, never grants reverse actuation."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1033_saved_task_diagnosis'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1022_full_route_planner'))
from reversible_route import construct
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());result=construct(row['packet'],row['source'],row['plan']['original_goal'],setup['known'],time.time()+120,allow_reverse=True)
result.update(original_task=True,physical_ready=False,new_navigation_authorized=False,reverse_dynamics_qualified=False,actuation_authority=False)
(O/'REVERSE_GEOMETRY_PROBE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['state_path','path','actions']}))
