"""One fixed fresh-packet original forward-time search, no models."""
import importlib.abc,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1042_original_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from timed_input import construct
assert not (O/'RESULT.json').exists();x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());assert json.loads((R/'runs/v1040_approach_information_audit/INFORMATION_AUDIT.json').read_text())['passed'];result=construct(x['packet'],x['source'],x['goal'],x['setup'],time.time()+120)
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['state_path','path','planned_body_requests','predicted_actuator_controls','actions']}))
