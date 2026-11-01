"""Locked old prefixes, canonical native schedules and full-state reserve replay."""
import os,sys,json,time,signal,hashlib,math,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
out=repo/'runs/v676_dynamic_canonical_commands/pre_navigation_retry02';out.mkdir(exist_ok=False);roundpath=out.parent/'ROUND_WINDOW.json';ledger=read(roundpath)
assert not ledger['round_closed']and time.time()+185<ledger['absolute_deadline_unix']
started=time.monotonic();steps=0;extra=0;worst=np.zeros(3);private_error=0.;records=[];unit=None;minimum=1e9;minself=1e9;bad=0;predictor=None;status='FAILED';error=None;input_hashes={}
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PRE_NAV_180S')));signal.alarm(180)
def clone(real):
 p=mujoco.MjData(predictor.model)
 for name in ['qpos','qvel','act','qacc_warmstart']:getattr(p,name)[:]=getattr(real,name)
 p.time=float(real.time);mujoco.mj_forward(predictor.model,p);p.qacc_warmstart[:]=real.qacc_warmstart;p.ctrl[:]=real.ctrl;return p
def check_tail(manager,real,proposal):
 global extra
 p=clone(real);p.ctrl[:]=0.;p.ctrl[ids]=proposal
 for _ in range(8):mujoco.mj_step(predictor.model,p);extra+=1
 manager.after_public(p);command,_=manager.start(p,9999)
 for public in range(40):
  predictor.command_map.assert_first(command,p.ctrl[ids]);p.ctrl[:]=0.;p.ctrl[ids]=command
  for _ in range(8):mujoco.mj_step(predictor.model,p);extra+=1
  done=manager.after_public(p)
  if public<39:command,_=manager.command(p)
 assert done and not manager.executing
try:
 for folder,name,limit,checkpoint in [('v674_dynamic_renewable_backup','dev41_95000011_renewable',280,272),('v675_dynamic_joint_admission','dev42_95000011_jointadmission',304,294)]:
  root=repo/'runs'/folder/name/'paired';cell=root/'geometry_memory';protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config);rows=lines(cell/'v648_execution.jsonl')[:limit];beliefs={r['step']:r for r in lines(cell/'motion_estimate.jsonl')};decisions=lines(cell/'control_decisions.jsonl')
  for f in [root/'scene_model.mjb',cell/'v648_execution.jsonl',cell/'motion_estimate.jsonl',cell/'control_decisions.jsonl']:input_hashes[str(f.relative_to(repo))]=hashlib.sha256(f.read_bytes()).hexdigest()
  m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
  if predictor is None:
   predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;assert ids==[0,1,2,3]
   rng=np.random.default_rng(676);mapping_cases=10000
   for _ in range(mapping_cases):
    previous=rng.uniform(predictor.command_map.lower,predictor.command_map.upper);target=rng.uniform(-100,100,4);command=predictor.command_map.step(target,previous)
    assert predictor.command_map.legal(command)and np.all(abs(command-previous)<=predictor.command_map.rate+1e-12)
   assert np.array_equal(predictor.model.actuator_ctrlrange[ids],m.actuator_ctrlrange[ids])
  geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  def field_at(k):
   field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,beliefs[k],'predictive',protocol['known_circles'],protocol['known_rectangles']);return field
  if unit is None:
   manager=ReservedRecovery(predictor,mujoco,ids,out/'initial_tail');proposal=predictor.command_map.step([0,0,.7,.7],d.ctrl[ids]);summary=manager.admit_nominal(d,proposal,field_at(0),beliefs[0],0);assert summary
   check_tail(manager,d,proposal);unit={'complete_328tick_qpos_qvel_ctrl_match':True,'summary':summary}
  for k,row in enumerate(rows):
   if k==checkpoint:
    nominal=next(x for x in decisions if x['step']==k and x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY');old=max([x for x in nominal['candidates']if x['reason']is None],key=lambda x:x['score']);target=np.asarray(old['target_command']);last=d.ctrl[ids].copy();proposal=predictor.command_map.step(target,last)
    trajectory=predictor.predict(d,target,ids,last,horizon=240,brake_after=80);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();self_margin=predictor.prediction_self_margin;end_speed=predictor.terminal_speed;clearance=float(np.min(field_at(k).trajectory_values(trajectory,.01)));schedule=predictor.command_map.sequence(target,last,240,80);p=clone(d);local_error=0.
    for tick,command in enumerate(schedule):
     if tick%8==0:predictor.command_map.assert_first(command,p.ctrl[ids])
     p.ctrl[:]=0.;p.ctrl[ids]=command;mujoco.mj_step(predictor.model,p);extra+=1
     local_error=max(local_error,float(np.max(abs(p.qpos-q[tick]))),float(np.max(abs(p.qvel-v[tick]))));assert local_error<=1e-8,'PRIVATE_NATIVE_SCHEDULE_STATE_MISMATCH'
     assert predictor.command_map.legal(p.ctrl[ids])and np.max(abs(p.ctrl[ids]-command))<=1e-12
    private_error=max(private_error,local_error)
    manager=ReservedRecovery(predictor,mujoco,ids,out/f'checkpoint_{k}');summary=manager.admit_nominal(d,proposal,field_at(k),beliefs[k],k)
    if summary is not None:check_tail(manager,d,proposal)
    records.append({'dataset':folder,'checkpoint':k,'old_raw_first_command':old['first_command'],'actual_previous_command':last.tolist(),'new_canonical_first_command':proposal.tolist(),'native_240tick_qpos_qvel_ctrl_max_error':local_error,'nominal_clearance_m':clearance,'nominal_self_margin_m':self_margin,'nominal_terminal_speed_m_s':end_speed,'appendable':summary is not None,'reserve':summary,'scope':'control consistency check, not navigation or a universally feasible input'})
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);minself=min(minself,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    field=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
    minimum=min(minimum,float(pose_values(field,[[q[0],q[1],yaw]])[0]))
    for contact in d.contact:bad+=catalog.classify(contact,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
    assert minimum>=.15-1e-8 and minself>=0 and bad==0,'OLD_PREFIX_PHYSICAL_ANOMALY'
   worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'OLD_LOG_REPLAY_MISMATCH'
   assert predictor.prediction_steps+extra+896<=60000,'PRIVATE_CAP'
  print('DATASET_REPLAY_COMPLETE',folder,limit,flush=True)
 assert steps==4672 and len(records)==2;status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':(predictor.prediction_steps if predictor else 0)+extra,'old_prefix_qpos_qvel_mocap_errors':worst.tolist(),'private_native_schedule_max_qpos_qvel_error':private_error,'minimum_old_prefix_clearance_m':minimum,'minimum_old_prefix_self_margin_m':minself,'bad_contacts':bad,'mapping_math_cases':10000,'unit':unit,'records':records,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'input_sha256':input_hashes,'new_navigation_tasks':0,'old_failures_reclassified':False,'previous_failed_private_integrations':896,'previous_failed_replay_native_steps':2176};(out/'COMPLETION.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256','records']},indent=2),flush=True);assert status=='PASS',error
