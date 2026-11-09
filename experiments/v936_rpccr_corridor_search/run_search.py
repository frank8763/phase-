"""Fixed actual V934 stalled states, same budgets, no model imports."""
import gzip,hashlib,importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v936_rpccr_corridor_search'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*a):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C));from corridor_search import search
S=O/'saved';rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'SETUP.json').read_text())['known'];task=json.loads((S/'TASK.json').read_text());routes=json.loads((S/'ROUTER_REQUESTS.json').read_text());targets=[7000,11000,17000];(O/'SEARCH_FREEZE.json').write_text(json.dumps(dict(models=0,integrations=0,targets=targets,sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [C/'corridor_search.py',C/'run_search.py',C/'PROTOCOL.md']}),indent=2)+'\n')
results=[]
for target in targets:
 row=[x for x in rows if x['packet']['native_tick']<=target][-1];source=row['source'];start=row['packet']['body'][:3];result=search(start,task['goal_xy'],known,source['periodic']);result.update(target_tick=target,actual_body_tick=row['packet']['native_tick'],original_wanted=row['wanted'],original_source=source,actual_packet=row['packet']);(O/f'CASE_{target}.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(target,result['status'],result.get('expanded'),result.get('nominal_length_m'),result['wall_s'],flush=True)
(O/'SEARCH_RESULTS.json').write_text(json.dumps(dict(passed=all(r['passed']for r in results),cases=results,models=0,integrations=0,physical_candidate_ready=False),indent=2)+'\n')
