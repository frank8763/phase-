import hashlib,importlib.abc,json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v937_rpccr_timed_corridor'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C));from timed_schedule import schedule
prior=R/'runs/v936_rpccr_corridor_search';case=json.loads((prior/'CASE_7000.json').read_text());route=json.loads((prior/'STATIC_COUNTERFACTUAL.json').read_text());assert route['passed'];known=json.loads((prior/'saved/SETUP.json').read_text())['known']
files=[C/'timed_schedule.py',C/'run.py',C/'PROTOCOL.md',prior/'CASE_7000.json',prior/'STATIC_COUNTERFACTUAL.json',prior/'saved/SETUP.json'];(O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(models=0,integrations=0,at=time.time(),files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}),indent=2)+'\n')
source=case['original_source'];origin=source['source_scan_sim_time']+source['source_age_s']+.05;result=schedule(route['path'],known,source['periodic'],origin);result.update(source_tick=case['actual_body_tick'],origin_sim_time=origin,path=route['path'],prior=source['periodic'],physical_candidate_ready=False);(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['path','prior','schedule']},indent=2))
