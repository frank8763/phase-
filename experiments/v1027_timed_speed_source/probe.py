import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from timed_input import construct
P=R/'runs/v858_nav2_verified/v1024/dynamic_we';x=json.loads((P/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((P/'physics/SETUP.json').read_text())
r=construct(x['packet'],x['source'],x['plan']['original_goal'],setup,time.time()+120.)
(R/'runs/v1027_timed_speed_source/PROBE.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['actions','state_path','planned_body_requests','predicted_actuator_controls','path']}))
