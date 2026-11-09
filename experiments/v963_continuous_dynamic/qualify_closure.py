"""No-model import closure, forward-only recovery graph and fixed-night table checks."""
import importlib.abc
import json
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','vehicle','factory','physical','rclpy'}:raise RuntimeError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import native_worker
sys.path.insert(0,str(C))
import supervise,watchdog,transaction,recovery,corridor_search,polygon_geometry
checks=dict(actual_native_dependency_closure=native_worker.engine.C==C,
 actual_supervision_dependency_closure=all(Path(m.__file__).parent==C for m in [supervise,watchdog,transaction,recovery,corridor_search,polygon_geometry]))
result=corridor_search.search([0.,0.,0.],[.6,0.],{'known_rectangles':[],'known_circles':[]},None)
checks['forward_recovery_graph_no_reverse']=result['passed']and all(d==1 for d in result['edge_directions'])
tasks=json.loads((C/'NIGHT_TASKS.json').read_text());main=[x for x in tasks if x['stage']=='confirmation']
checks.update(unique31tasks=len(tasks)==31==len({x['run_id']for x in tasks}),all24=len(main)==24,
 new_unique_seeds=len({x['seed']for x in main})==24,
 balanced_routes=all(sum(x['route']==r for x in main)==8 for r in ['we','ns','ew']),
 balanced_directions=all(sum(x['initial_axis_direction']==d for x in main)==12 for d in [-1,1]),
 repeat_slots=[x['slot']for x in tasks if x['stage']=='confirmation_repeat']==[1,9,17],
 per_task180plus2=all(x['wall_limit_s']==180 and x['brake_s']==2 for x in tasks))
p=R/'runs/v963_continuous_dynamic/ZERO_MODEL_QUALIFICATION.json';q=json.loads(p.read_text());q['checks'].update(checks);q['passed']=all(q['checks'].values());p.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(dict(passed=q['passed'],checks=len(q['checks']),models=0,integrations=0)));assert q['passed']
