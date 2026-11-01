"""Reproduce only the original final18 predictions; separate static and dynamic causes."""
import os,sys,json,time,signal,hashlib,math,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});repo=Path(os.environ['PHASE_REPO']);base=repo/'runs/v683_dynamic_current_state_diagnosis/diagnosis49_95000011_currentstate/paired';snapshot=base.parent/'source_snapshot';sys.path.insert(0,str(snapshot));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from geometry_predictor import RobotPredictor
from exact_footprint import pose_values
from motion_tracker import install_time_gate
from union_belief import clearance as union_clearance
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
read=lambda p:json.loads(p.read_text());cell=base/'geometry_memory';root=repo/'runs/v685_dynamic_terminal_forensics';assert not(root/'COMPLETION.json').exists();original=read(repo/'runs/v683_dynamic_current_state_diagnosis/ROUND_WINDOW.json');assert original['round_closed']and time.time()+185<original['absolute_deadline_unix'];previous=read(repo/'runs/v684_dynamic_consistent_proposals/pre_navigation_retry02/COMPLETION.json');assert previous['private_prediction_integrations']==20344;assert read(base/'CURRENT_STATE_INFORMATION_AUDIT_V2.json')['status']=='ALL_CURRENT_STATE_INFORMATION_CHECKS_PASS'
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];assert len(rows)==753;states=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()];decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];candidates=next(x['candidates']for x in decisions if x['step']==753 and x['stage']=='NOMINAL'and x['candidate_role']=='ORDINARY');assert len(candidates)==18;protocol=read(base/'STATIC_PROTOCOL.json');config=read(base/'DYNAMIC_PROTOCOL.json');motion=Motion(config);m=mujoco.MjModel.from_binary_path(str(base/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,base/'assets/isolated_indoor.xml');predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;bounds=np.asarray(protocol['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));started=time.monotonic();steps=bad=0;records=[];worst=np.zeros(3);minimum=selfmargin=1e9;status='FAILED';error=None;signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FINAL_REPRODUCTION_180S')));signal.alarm(180)
try:
 for k,row in enumerate(rows):
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   assert np.max(abs(d.ctrl-row['ctrl']))<=1e-12
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));actual=SimpleNamespace(**{**vars(static),'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),.1]]).reshape(-1,3)});minimum=min(minimum,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
   for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minimum>=.15-1e-8 and selfmargin>=0 and bad==0,'PHYSICAL_REPLAY_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'FULL_STATE_REPLAY_MISMATCH'
 assert abs(d.time-states[753]['time'])<=1e-10
 field=SimpleNamespace(**vars(static));field.pose_values=MethodType(pose_values,field);install_time_gate(field,states[753],'predictive',protocol['known_circles'],protocol['known_rectangles']);t=np.arange(1,241)*.01;limits=predictor.command_map.limits;rate=predictor.command_map.rate;current=d.ctrl[ids].copy()
 for index,c in enumerate(candidates):
  target=np.asarray(c['target_command']);trajectory=predictor.predict(d,target,ids,current,horizon=240,brake_after=80);total=field.trajectory_values(trajectory,.01);known=pose_values(static,trajectory);dynamic=union_clearance(field,trajectory,states[753]['outer_state_cells'],t);end_speed=predictor.terminal_speed;body=predictor.prediction_self_margin;difference=max(abs(float(total.min())-c['minimum_clearance_m']),abs(end_speed-c['terminal_speed_m_s']),abs(body-c['self_domain_margin_m']));assert difference<=1e-8 and int(np.argmin(total))+1==c['minimum_clearance_native_tick'],'ORIGINAL_PREDICTION_NOT_REPRODUCED'
  # Known geometry evaluates the same fixed footprint as the original gate.
  truth=known.copy();centers=np.asarray([motion.xy(d.time+dt)for dt in t]);cc,ss=np.cos(trajectory[:,2]),np.sin(trajectory[:,2]);ego=trajectory[:,:2]+np.c_[cc*static.center_local[0]-ss*static.center_local[1],ss*static.center_local[0]+cc*static.center_local[1]];delta=centers-ego;local=np.c_[delta[:,0]*cc+delta[:,1]*ss,-delta[:,0]*ss+delta[:,1]*cc];residual=abs(local)-static.half;actor=np.where(residual.max(axis=1)<=0,residual.max(axis=1),np.linalg.norm(np.maximum(residual,0),axis=1))-.1;truth=np.minimum(truth,actor)
  reasons=[]
  if known.min()<.155:reasons.append('KNOWN_STATIC_GEOMETRY')
  if dynamic.min()<.155:reasons.append('DYNAMIC_MOTION_OUTER_SET')
  per_static=[]
  for j,rectangle in enumerate(protocol['known_rectangles']):
   one=SimpleNamespace(**{**vars(static),'rectangles':np.asarray([rectangle]),'circles':[]});value=pose_values(one,trajectory);per_static.append({'kind':'known_rectangle','index':j,'minimum_m':float(value.min())})
  limited=np.clip(target,limits[:,0],limits[:,1]);steer_periods=np.ceil(np.maximum(abs(limited[:2]-current[:2])-1e-12,0)/rate[:2]).astype(int)
  records.append({'candidate_index':index,'original_reason':c['reason'],'original_total_minimum_m':c['minimum_clearance_m'],'recomputed_total_minimum_m':float(total.min()),'original_prediction_maximum_error':float(difference),'known_static_minimum_m':float(known.min()),'known_static_minimum_tick':int(np.argmin(known))+1,'dynamic_outer_minimum_m':float(dynamic.min()),'dynamic_outer_minimum_tick':int(np.argmin(dynamic))+1,'actual_future_minimum_m':float(truth.min()),'rejecting_components':reasons,'closest_known_rectangle':min(per_static,key=lambda x:x['minimum_m']),'current_command':current.tolist(),'target_command':target.tolist(),'legal_target':limited.tolist(),'front_target_slew_time_lower_bound_s':(steer_periods*.08).tolist(),'nominal_drive_time_s':.8,'terminal_speed_m_s':end_speed,'self_domain_margin_m':body,'predicted_terminal_pose':trajectory[-1].tolist()})
 assert steps==6024 and predictor.prediction_steps==4320;status='ALL_ORIGINAL_FINAL_PREDICTIONS_REPRODUCED'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps,'cumulative_round_fixed_private_integrations':20344+predictor.prediction_steps,'maximum_public_qpos_qvel_mocap_errors':worst.tolist(),'minimum_actual_replay_clearance_m':minimum,'minimum_replay_self_margin_m':selfmargin,'bad_contacts':bad,'new_navigation_tasks':0,'new_algorithm_candidates':0,'original_absolute_deadline_unix':original['absolute_deadline_unix'],'records':records,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'same18already-recorded targets at original unexecuted final decision; actual future evaluator-only; no new control search or success claim'};(root/'COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='records'},indent=2));assert status!='FAILED',error
