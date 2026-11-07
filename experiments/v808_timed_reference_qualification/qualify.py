"""Five preregistered saved inputs: reference geometry only; no MuJoCo imports."""
import importlib.abc,importlib.util,json,hashlib,pathlib,signal,sys,time
import numpy as np
own=pathlib.Path(__file__).parent;repo=own.parents[1];out=repo/'runs/v808_timed_reference_qualification';out.mkdir(exist_ok=True)
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname=='mujoco'or fullname.startswith('mujoco.'):raise RuntimeError('ZERO_MODEL_QUALIFICATION_FORBIDS_MUJOCO')
sys.meta_path.insert(0,NoPhysics());sys.path.insert(0,str(own));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from planner import search,spatial_search
from timed_reference import attach,route_world,scheduled_samples,HORIZON
spec=importlib.util.spec_from_file_location('qualification_footprint',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
root=repo/'runs/v807_reactive_single_task_continuation/main_slot01/paired';cell=root/'geometry_memory';states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};records=[];started=time.time()
window=dict(started_unix=started,absolute_deadline_unix=min(started+600,read(repo/'GLOBAL_DYNAMIC_OVERNIGHT_LEDGER_20261104.json')['development_absolute_deadline_unix']),round_closed=False,models=0,integrations=0)
(out/'ROUND_WINDOW.json').write_text(json.dumps(window,indent=2)+'\n');signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SAVED_QUALIFICATION_600S')));signal.alarm(max(1,int(window['absolute_deadline_unix']-time.time())))
status='RUNNING'
try:
 for step in [303,375,380,674,714]:
  source=cell/f'planning_{step:04d}.json';old=read(source);state=states[step];world,metadata=route_world(old['causal_input'],state);field=build(F,world);field.base_heuristic=F.base._heuristic_grid;attach(field,state)
  start=np.asarray(old['pose']);goal=np.array([4.,-2.]);wheel=float(world['wheel_base']);steer=float(world['max_steer']);path,stats=search(field,start,goal,wheel,steer,guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
  if stats['status']!='GLOBAL_GOAL_PATH':
   preferred,preferred_stats=path,stats;path,stats=search(field,start,goal,wheel,steer,guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
   if path is None and preferred is not None:path,stats=preferred,dict(preferred_stats)
   stats['preferred_search']=preferred_stats
  row=dict(step=step,input_file=str(source.relative_to(repo)),input_sha256=sha(source),causal_state=state,causal_world=world,start=start.tolist(),goal=goal.tolist(),metadata=metadata,path=None if path is None else path.tolist(),stats=stats,old_status=old['stats']['status'],old_endpoint_goal_distance_m=None if old['path']is None else float(np.linalg.norm(np.asarray(old['path'])[-1,:2]-goal)))
  if path is not None:
   schedule=np.asarray(stats['reference_arrival_times_s']);dense,dtimes=scheduled_samples(path,schedule);value=field.reference_values(dense,dtimes);assert value.min()>=stats['guard_m']-1e-8
   np.savez_compressed(out/f'step{step:04d}.npz',path=path,arrivals=schedule,dense=dense,times=dtimes,values=value);row['saved_arrays']=f'step{step:04d}.npz';row['new_endpoint_goal_distance_m']=float(np.linalg.norm(path[-1,:2]-goal));row['within_horizon_samples']=int(np.sum(dtimes<=HORIZON));row['uncertified_guidance_samples']=int(np.sum(dtimes>HORIZON))
  records.append(row);(out/'RESULTS.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'step':step,'old':row['old_status'],'new':stats['status'],'new_goal_remaining':row.get('new_endpoint_goal_distance_m'),'expanded':stats['expanded']}),flush=True)
 status='SAVED_REFERENCE_SEARCH_COMPLETE'
except BaseException as e:
 import traceback
 status='STOPPED_EXCEPTION';(out/'ERROR.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()},indent=2)+'\n')
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);(out/'ROUND_WINDOW.json').write_text(json.dumps(window,indent=2)+'\n');(out/'COMPLETION.json').write_text(json.dumps({'status':status,'records':records,'models':0,'integrations':0},indent=2)+'\n')
