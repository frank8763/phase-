"""Locked217/225 alternate-input appendability; exact old prefix, no new nav."""
import os,sys,json,time,signal,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v674_dynamic_renewable_backup';sys.path.insert(0,str(src));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from reserved_recovery import ReservedRecovery
from geometry_predictor import RobotPredictor
from motion_tracker import install_time_gate
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text())
base=repo/'runs/v674_dynamic_renewable_backup';out=base/'selection_probe';out.mkdir(exist_ok=False)
root=base/'dev41_95000011_renewable/paired';cell=root/'geometry_memory';started=time.monotonic();ledger=read(base/'ROUND_WINDOW.json');assert not ledger['round_closed']and time.time()+185<ledger['absolute_deadline_unix']
freeze=read(base/'development01/SOURCE_FREEZE.json');assert all(hashlib.sha256((src/n).read_bytes()).hexdigest()==h for n,h in freeze.items())
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()][:226];decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config);m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=list(range(4));geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
steps=0;extra=0;records=[];worst=np.zeros(3);minclear=1e9;minself=1e9;bad=0;status='FAILED';error=None
def dump(name,x):(out/name).write_text(json.dumps(x,indent=2,default=lambda x:x.item(),allow_nan=False)+'\n')
def private_verify(manager,command):
 global extra
 pm=predictor.model;p=mujoco.MjData(pm)
 for name in ['qpos','qvel','act','qacc_warmstart']:getattr(p,name)[:]=getattr(d,name)
 p.time=float(d.time);mujoco.mj_forward(pm,p);p.qacc_warmstart[:]=d.qacc_warmstart;p.ctrl[:]=0.;p.ctrl[ids]=command
 for _ in range(8):mujoco.mj_step(pm,p);extra+=1
 manager.after_public(p);command,_=manager.start(p,9999)
 for i in range(40):
  p.ctrl[:]=0.;p.ctrl[ids]=command
  for _ in range(8):mujoco.mj_step(pm,p);extra+=1
  done=manager.after_public(p)
  if i<39:command,_=manager.command(p)
 assert done
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SELECTION_PROBE_180S')));signal.alarm(180)
try:
 for k,row in enumerate(rows):
  if k in [217,225]:
   entry=next(x for x in decisions if x['step']==k and x['candidate_role']=='ORDINARY'and x['stage']=='NOMINAL');backup=next(x for x in decisions if x['step']==k and x['candidate_role']=='ORDINARY'and x['stage']=='BACKUP_APPEND')
   ranked=sorted([x for x in entry['candidates']if x['reason']is None],key=lambda x:x['score'],reverse=True);unique=[];seen=set()
   for x in ranked:
    key=tuple(x['first_command'])
    if key not in seen:seen.add(key);unique.append(x)
   f=SimpleNamespace(**static);f.pose_values=MethodType(pose_values,f);install_time_gate(f,beliefs[k],'predictive',protocol['known_circles'],protocol['known_rectangles'])
   values=[]
   for rank,c in enumerate(unique[:3 if k==217 else 2]):
    command=np.asarray(c['first_command']);delta=command-d.ctrl[ids];assert np.max(abs(delta[:2]))<=.1+1e-10 and np.max(abs(delta[2:]))<=.7+1e-10
    manager=ReservedRecovery(predictor,mujoco,ids,out/f'point{k}_rank{rank}');summary=manager.admit_nominal(d,command,f,beliefs[k],k)
    best=max(x['minimum_clearance_m']for x in manager.last_attempt['candidates']);oldbest=max(x['minimum_clearance_m']for x in backup['detail']['candidates'])
    if rank==0:assert summary is None and abs(best-oldbest)<=1e-10,'ORIGINAL_REJECTION_NOT_REPRODUCED'
    if summary is not None:private_verify(manager,command)
    values.append({'distinct_command_rank':rank,'score':c['score'],'first_command':command.tolist(),'appendable':summary is not None,'summary':summary,'backup_attempt':manager.last_attempt,'private_prefix_and_tail_full_state_match':summary is not None})
    assert predictor.prediction_steps+extra<=30000,'PRIVATE_CAP'
   records.append({'checkpoint':k,'ordinary_safe_candidates':len(ranked),'distinct_safe_commands':len(unique),'tested':values,'untested_distinct_commands':len(unique)-len(values)})
   dump('PROGRESS.json',{'records':records,'private_integrations':predictor.prediction_steps+extra});print('CHECKPOINT',k,'appendable ranks',[v['distinct_command_rank']for v in values if v['appendable']],flush=True)
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);minself=min(minself,float(containment_margin(b,bounds)));q=d.qpos;yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
   actual=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
   minclear=min(minclear,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
   for contact in d.contact:bad+=catalog.classify(contact,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minself>=0 and minclear>=.15-1e-8 and bad==0,'PHYSICAL_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'REPLAY_MISMATCH'
 assert steps==1808 and len(records)==2;status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps+extra,'maximum_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_clearance_m':minclear,'minimum_self_domain_margin_m':minself,'bad_contacts':bad,'records':records,'concrete_missed_appendable_commands':sum(x['appendable']and x['distinct_command_rank']>0 for r in records for x in r['tested']),'new_navigation_tasks':0,'source_sha256':freeze,'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};dump('COMPLETION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['records','source_sha256']},indent=2));assert status=='PASS',error
