"""Saved real failure input; no model, network, or actuation imports."""
import importlib.abc,json,sys
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL_ONLY '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C))
from planner import construct,library
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());lib=library();rect=np.ascontiguousarray(x['setup']['known']['known_rectangles'],float);circ=np.ascontiguousarray(x['setup']['known']['known_circles'],float);rng=np.random.default_rng(1067);poses=np.c_[rng.uniform(-4.8,4.8,(1000,2)),rng.uniform(-math.pi,math.pi,1000)];native=np.array([lib.static_pose(*p,rect,len(rect),circ,len(circ))for p in poses]);reference=ref._old.Geometry(x['setup']['known'],None).clearances(poses)[0];error=float(abs(native-reference).max());assert error<=1e-10,('STATIC_GEOMETRY_ACCELERATOR_MISMATCH',error);dump(O/'STATIC_GEOMETRY_EQUIVALENCE.json',dict(passed=True,poses=len(poses),maximum_error=error,models=0,integrations=0))
plan=construct(x['setup'],x['packet'],x['source'],x['goal'],wall_s=30.);dump(O/'NS_ACTUAL_STATE_REPLAN.json',plan);print(json.dumps({k:v for k,v in plan.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']},ensure_ascii=False),flush=True)
