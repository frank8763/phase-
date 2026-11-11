import importlib.abc,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1045_curvature_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from timed_input import construct
assert not (O/'RESULT.json').exists();assert json.loads((O/'FAST_QUALIFICATION.json').read_text())['passed'];assert json.loads((R/'runs/v1044_curvature_speed_prediction/COMPLETION.json').read_text())['passed'];x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());result=construct(x['packet'],x['source'],x['goal'],x['setup'],time.time()+300)
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['path','state_path','actions','planned_body_requests','predicted_actuator_controls']}))
