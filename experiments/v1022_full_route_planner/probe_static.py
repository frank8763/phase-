"""Diagnostic static route only; never an actor-safe execution certificate."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';O.mkdir(exist_ok=True)
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL')
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import full_route as m
route=sys.argv[1];out=R/'runs/v858_nav2_verified/v1020'/('main_'+route);row=json.loads((out/'RECOVERY_CORRIDORS.json').read_text())[0];known=json.loads((out/'physics/SETUP.json').read_text())['known']
original=m.ref._old.Geometry
class StaticOnly(original):
 def __init__(self,k,p):super().__init__(k,None)
m.ref._old.Geometry=StaticOnly
p=m.construct(row['search_packet'],row['search_source'],row['original_goal'],known,time.time()+30.)
p.update(diagnostic_static_only=True,not_dynamic_certificate=True)
(O/(route+'_first.static_counterfactual.json')).write_text(json.dumps(p,indent=2)+'\n');print(json.dumps({k:v for k,v in p.items()if k not in ['path','state_path','edge_targets','heuristic']},ensure_ascii=False))
