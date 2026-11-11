"""One bounded unchanged original-.03 controller query on fresh causal source."""
import importlib.abc,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1040_approach_information_audit'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from input_route import construct
assert not (O/'ORIGINAL_CYCLE_PROBE.json').exists()
assert json.loads((O/'INFORMATION_AUDIT.json').read_text())['passed']
x=json.loads((O/'REBUILT_SOURCE.json').read_text());y=construct(x['packet'],x['source'],x['goal'],x['setup'],time.time()+100.)
(O/'ORIGINAL_CYCLE_PROBE.json').write_text(json.dumps(y,indent=2)+'\n')
print(json.dumps({k:v for k,v in y.items()if k not in ['state_path','path','planned_body_requests','predicted_actuator_controls','heuristic','edge_targets']}))
