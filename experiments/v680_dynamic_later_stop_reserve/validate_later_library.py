"""Fixed old217/227/686; original-vs-forward tails and exact logged replay."""
import os,sys,json,gzip,math,time,signal,hashlib,importlib.util,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from reserved_recovery import ReservedRecovery
from geometry_predictor import RobotPredictor
from motion_tracker import install_time_gate
from exact_footprint import pose_values
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
spec=importlib.util.spec_from_file_location('original_v676_reserve',repo/'experiments/v676_dynamic_canonical_commands/reserved_recovery.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
read=lambda p:json.loads(p.read_text());root=repo/'runs/v676_dynamic_canonical_commands/dev43_95000011_canonical/paired';cell=root/'geometry_memory';out=repo/'runs/v680_dynamic_later_stop_reserve/pre_navigation';out.mkdir(parents=True,exist_ok=False);ledger=read(repo/'runs/v679_dynamic_forward_reserve/ROUND_WINDOW.json');assert not ledger['round_closed']and time.time()+185<ledger['absolute_deadline_unix']
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()][:687];states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d);predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
started=time.monotonic();steps=0;extra=0;records=[];worst=np.zeros(3);minimum=1e9;selfmargin=1e9;bad=0;status='FAILED';error=None
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FORWARD_PROBE_180S')));signal.alarm(180)
def dump(name,x):(out/name).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item(),allow_nan=False)+'\n')
def verify_private(manager,proposal,k):
 global extra
 pm=predictor.model;p=mujoco.MjData(pm)
 for name in ['qpos','qvel','act','qacc_warmstart']:getattr(p,name)[:]=getattr(d,name)
 p.time=float(d.time);mujoco.mj_forward(pm,p);p.qacc_warmstart[:]=d.qacc_warmstart;p.ctrl[:]=d.ctrl;p.ctrl[:]=0.;p.ctrl[ids]=proposal
 for _ in range(8):mujoco.mj_step(pm,p);extra+=1
 manager.after_public(p);command,_=manager.start(p,k+1)
 for public in range(40):
  predictor.command_map.assert_first(command,p.ctrl[ids]);p.ctrl[:]=0.;p.ctrl[ids]=command
  for _ in range(8):mujoco.mj_step(pm,p);extra+=1
  done=manager.after_public(p)
  if public<39:command,_=manager.command(p)
 assert done
try:
 for k,row in enumerate(rows):
  if k==686:
   nominal=next(x for x in decisions if x['step']==k and x['candidate_role']=='ORDINARY'and x['stage']=='NOMINAL');chosen=max([x for x in nominal['candidates']if x['reason']is None],key=lambda x:x['score']);proposal=np.asarray(chosen['first_command']);field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,states[k],'predictive',protocol['known_circles'],protocol['known_rectangles']);old=baseline.ReservedRecovery(predictor,mujoco,ids,out/f'original_{k}');new=ReservedRecovery(predictor,mujoco,ids,out/f'forward_{k}');before=predictor.prediction_steps;original=old.admit_nominal(d,proposal,field,states[k],k);assert original is None,'LOCKED_ORIGINAL_REJECTION_NOT_REPRODUCED'
   previous=next(x for x in decisions if x['step']==k and x['candidate_role']=='ORDINARY'and x['stage']=='BACKUP_APPEND'and x.get('distinct_command_rank')==0);assert abs(max(x['minimum_clearance_m']for x in old.last_attempt['candidates'])-max(x['minimum_clearance_m']for x in previous['detail']['candidates']))<=1e-10
   summary=new.admit_nominal(d,proposal,field,states[k],k);checks=None
   if summary is not None:
    assert new.cache['recovery_kind']=='FORWARD_BRAKE'and new.cache['signed_longitudinal_displacement_m']>=.02
    saved={key:(value.tolist()if isinstance(value,np.ndarray)else value)for key,value in new.cache.items()};dump(f'new_certificate_{k}.json',saved);verify_private(new,proposal,k);checks={'full_prefix_and_320_tail_qpos_qvel_ctrl_match':True,'native_ticks':328}
   record={'checkpoint':k,'ordinary_score':chosen['score'],'proposal':proposal.tolist(),'original_appendable':False,'new_forward_appendable':summary is not None,'new_summary':summary,'original_attempt':old.last_attempt,'new_attempt':new.last_attempt,'private_execute_check':checks,'private_prediction_integrations':predictor.prediction_steps-before};records.append(record);dump('PROGRESS.json',{'records':records,'forecast_integrations':predictor.prediction_steps,'private_execute_integrations':extra});print('CHECKPOINT',k,'new_forward',summary is not None,flush=True)
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));actual=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
   minimum=min(minimum,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
   for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minimum>=.15-1e-8 and selfmargin>=0 and bad==0,'REPLAY_PHYSICAL_SAFETY_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'ORIGINAL_STATE_REPLAY_MISMATCH'
  assert predictor.prediction_steps+extra+46472<=60000,'PRIVATE_BUDGET'
 assert len(records)==1 and steps==5496;status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps+extra,'forecast_integrations':predictor.prediction_steps,'private_execution_integrations':extra,'maximum_old_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_native_clearance_m':minimum,'minimum_replay_self_margin_m':selfmargin,'bad_contacts':bad,'records':records,'new_appendable_forward_checkpoints':sum(x['new_forward_appendable']for x in records),'cumulative_diagnostic_private_integrations':46472+predictor.prediction_steps+extra,'new_navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'input_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [cell/'v648_execution.jsonl',cell/'motion_estimate.jsonl',cell/'control_decisions.jsonl',root/'scene_model.mjb']},'scope':'single preregistered686 implementation validation, no new navigation; original3point negatives retained'};dump('COMPLETION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['records','source_sha256','input_sha256']},indent=2));assert status=='PASS',error
