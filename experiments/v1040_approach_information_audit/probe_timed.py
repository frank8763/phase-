"""One fixed saved-input query after all actual approach evidence passes."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1040_approach_information_audit'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1035_signed_timed_input_source'))
from timed_input import construct
assert json.loads((O/'INFORMATION_AUDIT.json').read_text())['passed'];row=json.loads((O/'REBUILT_SOURCE.json').read_text());result=construct(row['packet'],row['source'],row['goal'],row['setup'],time.time()+120)
(O/'FULL_TIMED_PROBE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['actions','state_path','planned_body_requests','predicted_actuator_controls','nearest_candidate_actions']}))
