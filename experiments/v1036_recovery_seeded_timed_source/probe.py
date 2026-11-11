import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1036_recovery_seeded_timed_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from timed_input import construct
assert json.loads((O/'CONTROL_QUALIFICATION.json').read_text())['passed']
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());result=construct(row['packet'],row['source'],row['plan']['original_goal'],setup,time.time()+120)
(O/'PROBE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['actions','state_path','planned_body_requests','predicted_actuator_controls','nearest_candidate_actions']}))
