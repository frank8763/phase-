"""Real campaign policy and worker ordering checked without any model launch."""
import ast,importlib.abc,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from campaign import select_next
rows=[];tasks=json.loads((C/'TASKS.json').read_text());assert [x['task_id']for x in tasks]==['static_we','dynamic_we','repeat_dynamic_we']
assert select_next([],tasks[0]);assert not select_next([dict(passed=False)],tasks[1]);assert select_next([dict(passed=True)],tasks[1]);assert not select_next([dict(passed=True),dict(passed=False)],tasks[2]);assert select_next([dict(passed=True),dict(passed=True)],tasks[2])
source=(C/'worker.py').read_text();tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');lines={}
for node in ast.walk(main):
 if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='authorized':lines['authority']=node.lineno
 if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='create_vehicle':lines['first_model']=node.lineno
assert lines['authority']<lines['first_model'];assert 'FIRST_FAILURE_STOP'in(C/'campaign.py').read_text();assert 'start+5400'in(C/'start.py').read_text()
r=dict(passed=True,production_policy_cases=5,first_failure_blocks_all_dependencies=True,authority_before_first_model=True,single_immutable_root_s=5400,models=0,integrations=0)
(O/'QUEUE_QUALIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
