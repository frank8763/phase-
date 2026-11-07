"""Exact frozen actuator function and saved-reference controller interface."""
import ast,copy,hashlib,json,math,os,sys
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
repo=Path(os.environ.get('PHASE_REPO',Path(__file__).resolve().parents[2]))
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1','runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','runtime/mk-mini/training/phase14_lidar_depth_nav/envs','experiments/v733_early_low_translation_scan','experiments/v753_coupled_progress_repaired','experiments/v821_norm_route_development']:
 sys.path.insert(0,str(repo/p))
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pair=repo/'runs/v821_norm_route_development/main_slot02/paired';cell=pair/'geometry_memory'
def pose(q):
 q=np.asarray(q);return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
def poses(q):
 return np.asarray([pose(x)for x in np.asarray(q)])
def serial(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,Path):return str(x)
 raise TypeError(type(x).__name__)
def dump(path,x):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2,default=serial,allow_nan=False)+'\n')
source=repo/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase5_wheel_astar_sac_env.py'
tree=ast.parse(source.read_text());klass=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='MkMiniRealIndoorPhase5WheelAStarSACEnv')
method=next(x for x in klass.body if isinstance(x,ast.FunctionDef)and x.name=='_ackermann_from_steer_speed')
namespace={'np':np,'math':math};exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),namespace)
def environment(model,data):
 contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids']
 # Frozen Phase14 wrapper sets max_wheel_speed48 (constructor alone is24).
 inner=SimpleNamespace(wheel_radius=.12,wheel_base=.60,track_width=.54,max_steer=float(read(cell/'planning_0265.json')['causal_input']['control_candidate_max_steer']),max_wheel_speed=48.,diff_gain=8.,id_lf_steer=ids[0],id_rf_steer=ids[1],id_lr_wheel=ids[2],id_rr_wheel=ids[3])
 inner._ackermann_from_steer_speed=MethodType(namespace['_ackermann_from_steer_speed'],inner)
 return SimpleNamespace(model=model,data=data,inner=inner)
def new_reference(step):
 p=repo/f'runs/v823_global_continuation_diagnosis/renewal_probe/ORIGINAL_SEARCH_{step:04d}.json'
 x=read(p);record=next(a for a in reversed(x['records'])if a['path']is not None)
 assert record['stats']['status']=='GLOBAL_GOAL_PATH'
 return np.asarray(record['path']),p
def controls_for_reference(path,current,env,goal):
 gear=int(path[1,3]);k=1;arc=0.
 while k<len(path)-1 and arc<.45 and int(path[k+1,3])==gear:
  arc+=float(np.linalg.norm(path[k+1,:2]-path[k,:2]));k+=1
 rel=path[k,:2]-current[:2];lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
 steer=float(np.clip(math.atan2(2*env.inner.wheel_base*lateral,max(float(rel@rel),.02)),-env.inner.max_steer,env.inner.max_steer))
 speed=gear*min(.60,.50/(1+abs(steer)))
 if np.linalg.norm(current[:2]-goal)<1.:speed*=.65
 return steer,speed
def fixed_inputs():
 traces={r['step']:r for r in map(json.loads,(cell/'v648_execution.jsonl').read_text().splitlines())}
 states={r['step']:{k:v for k,v in r.items()if k!='step'} for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 decisions={};routes={}
 for l in(cell/'control_decisions.jsonl').open():
  r=json.loads(l)
  if r['step']in(282,500)and r['stage']=='NOMINAL':decisions[r['step']]=r
 for l in(cell/'route_revalidation.jsonl').open():
  r=json.loads(l)
  if r['step']in(282,500):routes[r['step']]=r
 return traces,states,decisions,routes
