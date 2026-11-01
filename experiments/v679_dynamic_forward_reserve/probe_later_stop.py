"""One evidence-locked low-speed later-stop tail at the same three states."""
import os,sys,json,time,signal,math,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from motion_tracker import install_time_gate
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());base=repo/'runs/v679_dynamic_forward_reserve';out=base/'later_stop_diagnostic';out.mkdir(exist_ok=False);old=read(base/'pre_navigation/COMPLETION.json');assert old['status']=='PASS'and old['new_appendable_forward_checkpoints']==0
root=repo/'runs/v676_dynamic_canonical_commands/dev43_95000011_canonical/paired';cell=root/'geometry_memory';rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()][:687];states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d);predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
started=time.monotonic();steps=0;extra=0;records=[];worst=np.zeros(3);minclear=1e9;minself=1e9;bad=0;status='FAILED';error=None
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SECOND_DIAG_180S')));signal.alarm(180)
try:
 for k,row in enumerate(rows):
  if k in [217,227,686]:
   original=next(x for x in old['records']if x['checkpoint']==k);proposal=np.asarray(original['proposal']);field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,states[k],'predictive',protocol['known_circles'],protocol['known_rectangles']);pm=predictor.model;p=mujoco.MjData(pm)
   for n in ['qpos','qvel','act','qacc_warmstart']:getattr(p,n)[:]=getattr(d,n)
   p.time=float(d.time);mujoco.mj_forward(pm,p);p.qacc_warmstart[:]=d.qacc_warmstart;p.ctrl[:]=0.;p.ctrl[ids]=proposal;prefix=[];margin=1e9
   for _ in range(8):mujoco.mj_step(pm,p);extra+=1;mujoco.mj_kinematics(pm,p);prefix.append(p.qpos.copy());margin=min(margin,float(containment_margin(predictor.self_geometry.actual(pm,p),predictor.domain)))
   prefix=ReservedRecovery.poses(prefix);target=ReservedRecovery.target(.2136106867128606,4.);trajectory=predictor.predict(p,target,ids,proposal,horizon=320,brake_after=240);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();controls=predictor.command_map.sequence(target,proposal,320,240);values=field.trajectory_values(np.vstack((prefix,trajectory)),.01);body=min(margin,predictor.prediction_self_margin);end_speed=predictor.terminal_speed;distance=float((trajectory[-1,:2]-prefix[-1,:2])@np.array([math.cos(prefix[-1,2]),math.sin(prefix[-1,2])]))
   accepted=bool(values.min()>=.155 and body>=.002 and end_speed<=.025 and distance>=.02);maxerror=0.
   if accepted:
    for tick,command in enumerate(controls):
     if tick%8==0:predictor.command_map.assert_first(command,p.ctrl[ids])
     p.ctrl[:]=0.;p.ctrl[ids]=command;mujoco.mj_step(pm,p);extra+=1;maxerror=max(maxerror,float(np.max(abs(p.qpos-q[tick]))),float(np.max(abs(p.qvel-v[tick]))));assert maxerror<=1e-8,'LATER_STOP_FULL_STATE_MISMATCH'
   records.append({'checkpoint':k,'accepted':accepted,'minimum_causal_clearance_m':float(values.min()),'limiting_native_tick':int(np.argmin(values))+1,'self_domain_margin_m':body,'terminal_speed_m_s':end_speed,'signed_longitudinal_displacement_m':distance,'maximum_private_executed_full_state_error':maxerror,'target':target.tolist(),'brake_after':240,'tail_native_ticks':320})
   assert predictor.prediction_steps+extra+old['private_prediction_integrations']<=60000,'CUMULATIVE_PRIVATE_CAP'
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);minself=min(minself,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));field=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)});minclear=min(minclear,float(pose_values(field,[[q[0],q[1],yaw]])[0]))
   for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minclear>=.15-1e-8 and minself>=0 and bad==0,'REPLAY_PHYSICAL_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'REPLAY_STATE_MISMATCH'
 assert steps==5496 and len(records)==3;status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps+extra,'cumulative_diagnostic_private_integrations':old['private_prediction_integrations']+predictor.prediction_steps+extra,'records':records,'new_appendable_later_stop_checkpoints':sum(x['accepted']for x in records),'maximum_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_clearance_m':minclear,'minimum_self_margin_m':minself,'bad_contacts':bad,'new_navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')}};(out/'COMPLETION.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item())+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'},indent=2));assert status=='PASS',error
