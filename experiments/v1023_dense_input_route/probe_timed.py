import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from timed_input import construct
route=sys.argv[1];fixture=next(x for x in json.loads((R/'records/nav2_v1022_20261111/DYNAMIC_REJECTION_FIXTURES.json').read_text())if x['route']==route)
r=construct(fixture['packet'],fixture['source'],fixture['original_goal'],fixture['setup'],time.time()+100.)
(R/'runs/v1023_dense_input_route'/(route+'_timed.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['actions','state_path','planned_body_requests','predicted_actuator_controls','path']}))
