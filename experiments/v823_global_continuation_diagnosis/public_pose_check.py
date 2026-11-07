"""One fixed zero-model public-pose precision check; preserves prior outputs."""
import copy,gzip,hashlib,importlib.abc,importlib.util,json,math,os,signal,sys,time,traceback
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
root=repo/'runs/v823_global_continuation_diagnosis/public_pose_check'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name=='mujoco' or name.startswith('mujoco.'):raise RuntimeError('PUBLIC_POSE_CHECK_FORBIDS_PHYSICS')
sys.meta_path.insert(0,NoPhysics())
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0,str(repo/'experiments/v821_norm_route_development'))
from exact_footprint import build
from current_guide import attach
from planner import search
spec=importlib.util.spec_from_file_location('public_pose_F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
assert not root.exists();root.mkdir()
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+120,round_closed=False,max_search_calls=4,models=0,integrations=0)
dump(root/'ROUND_WINDOW.json',window)
freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in freeze.items())
guard=(repo/'REVIEW_PENDING').read_bytes();rows=[];queries=[];status='RUNNING'
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIXED_PUBLIC_POSE_120S_LIMIT')));signal.alarm(120)
try:
 cell=repo/'runs/v821_norm_route_development/main_slot02/paired/geometry_memory'
 states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets={x['step']:x for x in map(json.loads,f)}
 protocol=read(cell.parent/'STATIC_PROTOCOL.json');template=read(cell/'planning_0265.json')['causal_route_input']
 def construct(step):
  world=copy.deepcopy(template);world['rectangles']=[*protocol['known_rectangles'],states[step]['current_outer_rectangle']];world['circles']=copy.deepcopy(protocol['known_circles'])
  packet=packets[step];pose=np.r_[packet['xy'],packet['yaw']];world['start']=pose.tolist()
  field=build(F,world);field.base_heuristic=F.base._heuristic_grid;attach(field,states[step])
  field.free=field.clearance>=.15-field.config.resolution/math.sqrt(2)
  guide=field.base_heuristic(field,np.asarray(world['goal']));idx=field.indices([pose[:2]])[0]
  finite=bool((idx>=0).all()and(idx<guide.shape).all()and np.isfinite(guide[tuple(idx)]))
  return world,pose,field,finite
 for step in range(266,501):
  if not states[step]['observed_this_frame']:continue
  world,pose,field,finite=construct(step)
  rows.append(dict(step=step,goal_guide_finite=finite))
 first=next((r['step']for r in rows if r['goal_guide_finite']),None)
 dump(root/'OBSERVATION_CONNECTIVITY.json',dict(first_finite_observed_step=first,records=rows))
 for step in (282,500):
  world,pose,field,finite=construct(step);old=read(root.parent/f'renewal_probe/INPUT_{step:04d}.json')
  delta=float(np.max(abs(np.asarray(old['pose'])-pose)))
  assert np.array_equal(np.asarray(old['pose'])[:2].astype(np.float32).astype(float),pose[:2])
  assert old['pose'][2]==pose[2]and states[step]['time']==packets[step]['time']
  dump(root/f'INPUT_{step:04d}.json',dict(world=world,pose=pose.tolist(),motion_state=states[step],source='ACTUAL_PUBLIC_SENSOR_PACKET_POSE'))
  path,stats=search(field,pose,world['goal'],world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
  records=[dict(role='ORIGINAL_PREFERRED4000',stats=stats,path=None if path is None else path.tolist())]
  if stats['status']!='GLOBAL_GOAL_PATH':
   second,ss=search(field,pose,world['goal'],world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
   records.append(dict(role='ORIGINAL_FALLBACK16000',stats=ss,path=None if second is None else second.tolist()))
   if second is not None or path is None:path,stats=second,ss
  record=dict(step=step,selected_status=stats['status'],records=records,prior_double_pose_max_difference_m=delta,
   remaining_goal_m=None if path is None else float(np.linalg.norm(path[-1,:2]-world['goal'])),original_search_calls=len(records),
   no_dynamic_tail_or_native_execution_qualified=True,models=0,integrations=0)
  dump(root/f'ORIGINAL_SEARCH_{step:04d}.json',record)
  queries.append({k:v for k,v in record.items()if k!='records'});print(json.dumps(queries[-1]),flush=True)
 status='PUBLIC_POSE_ORIGINAL_REFERENCE_CHECK_COMPLETE'
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',window)
 dump(root/'COMPLETION.json',dict(status=status,observed_grid_queries=len(rows),queries=queries,models=0,integrations=0,
  source_and_input_hashes_unchanged=all(sha(repo/p)==h for p,h in freeze.items()),review_guard_bytes_unchanged=(repo/'REVIEW_PENDING').read_bytes()==guard,
  source_sha256=sha(Path(__file__))))
print(json.dumps(read(root/'COMPLETION.json')),flush=True)
