import sys,importlib.abc,json,resource
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parents[1];sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from joint_source import tighten
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());new,proof=tighten(x['source'],phase_planes=16);dump(O/'JOINT_SOURCE.json',new);dump(O/'JOINT_SOURCE_PROOF.json',proof);print(json.dumps({k:v for k,v in proof.items()if k not in ['A','b','planes']},ensure_ascii=False),flush=True)
from planner import construct
plan=construct(x['setup'],x['packet'],new,x['goal'],wall_s=30.);dump(O/'NS_JOINT_SOURCE_REPLAN.json',plan);print(json.dumps({k:v for k,v in plan.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']},ensure_ascii=False),flush=True)
