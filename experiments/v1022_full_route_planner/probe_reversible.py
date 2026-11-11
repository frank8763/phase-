"""Fixed last/earlier V1020 states; zero-model full-route source experiment."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';O.mkdir(exist_ok=True)
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('NO_MODEL_SOURCE_QUALIFICATION '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from reversible_route import construct
route=sys.argv[1];which=sys.argv[2];out=R/'runs/v858_nav2_verified/v1020'/('main_'+route);rows=json.loads((out/'RECOVERY_CORRIDORS.json').read_text());row=rows[0 if which=='first'else-1];setup=json.loads((out/'physics/SETUP.json').read_text())
p=construct(row['search_packet'],row['search_source'],row['original_goal'],setup['known'],time.time()+30.,allow_reverse=True)
(O/(route+'_'+which+'.reversible_geometry.json')).write_text(json.dumps(p,indent=2)+'\n')
print(json.dumps({k:v for k,v in p.items()if k not in ['path','state_path','edge_targets','heuristic']},ensure_ascii=False))
