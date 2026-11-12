import sys,importlib.abc,json,time
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1065_preflight_metadata_continuation'))
from kernel import *
pin_threads();sys.path.insert(0,str(Path(__file__).resolve().parent));from timed_replan_fine import construct
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());p=construct(x['packet'],x['source'],x['goal'],x['setup'],time.time()+60)
dump(R/'runs/v1066_actual_route_diagnosis/NS_TIMED_FINE_REPLAN_PROTOTYPE.json',p);print(json.dumps({k:v for k,v in p.items()if k not in ['state_path','path','planned_body_requests','predicted_actuator_controls','input_candidate_checks']},ensure_ascii=False))
