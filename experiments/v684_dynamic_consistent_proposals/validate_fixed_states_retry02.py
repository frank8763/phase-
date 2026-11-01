"""Old49/227/245 exact replay, new target geometry, complete appendable-tail evidence."""
import os,sys,json,gzip,math,time,signal,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent;sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from reserved_recovery import ReservedRecovery
from geometry_predictor import RobotPredictor
from motion_tracker import install_time_gate
from exact_footprint import pose_values
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from serial_predictor import project_to_segment_path
from tracking import switch_if_settled
read=lambda p:json.loads(p.read_text());root=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired';cell=root/'geometry_memory';out=repo/'runs/v684_dynamic_consistent_proposals/pre_navigation_retry02';out.mkdir(parents=True,exist_ok=False);ledgerpath=out.parent/'CONTINUATION_LEDGER.json';ledger=read(ledgerpath);assert not ledger['closed']and time.time()+245<ledger['original_absolute_deadline_unix'];assert read(repo/'runs/v683_dynamic_current_state_diagnosis/VALIDATOR_COUNT_REVIEW.json')['all_actual_state_model_source_information_checks_pass'];assert read(out.parent/'GEOMETRY_VALIDATION.json')['status']=='PASS'
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()][:246];trace=read(cell/'trace.json');states={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()];plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d);inner=SimpleNamespace(wheel_radius=.12,wheel_base=.6,track_width=.54,max_steer=.6108652381980153);env=SimpleNamespace(model=m,data=d,inner=inner);predictor=RobotPredictor(env,repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;inner.id_lf_steer,inner.id_rf_steer,inner.id_lr_wheel,inner.id_rr_wheel=map(int,ids);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));goal=np.asarray(protocol['goal_xy']);started=time.monotonic();steps=extra=bad=0;records=[];worst=np.zeros(3);minimum=1e9;selfmargin=1e9;status='FAILED';error=None;wrap=lambda a:(a+np.pi)%(2*np.pi)-np.pi
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED_TARGET_PROBE_240S')));signal.alarm(240)
def dump(name,x):(out/name).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item(),allow_nan=False)+'\n')
def private_execute(manager,proposal,k):
 global extra
 pm=predictor.model;p=mujoco.MjData(pm)
 for name in ['qpos','qvel','act','qacc_warmstart']:getattr(p,name)[:]=getattr(d,name)
 p.time=float(d.time);mujoco.mj_forward(pm,p);p.qacc_warmstart[:]=d.qacc_warmstart;p.ctrl[:]=0.;p.ctrl[ids]=proposal
 for _ in range(8):mujoco.mj_step(pm,p);extra+=1
 manager.after_public(p);command,_=manager.start(p,k+1)
 for public in range(40):
  predictor.command_map.assert_first(command,p.ctrl[ids]);p.ctrl[:]=0.;p.ctrl[ids]=command
  for _ in range(8):mujoco.mj_step(pm,p);extra+=1
  done=manager.after_public(p)
  if public<39:command,_=manager.command(p)
 assert done
 return {'full_prefix_and320_tail_qpos_qvel_ctrl_match':True,'native_ticks':328}
try:
 for k,row in enumerate(rows):
  if k in [49,227,245]:
   q=d.qpos;current=np.asarray([q[0],q[1],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]);event=max([p for p in plans if p['step']<=k],key=lambda p:p['step']);path=np.asarray(event['path']);assert path is not None
   if event['step']==k:index=0
   else:
    index=int(trace[k-1]['path_index']);gear=int(path[min(index+1,len(path)-1),3]);end=index+1
    while end<len(path)-1 and int(path[end+1,3])==gear:end+=1
    distances=np.linalg.norm(path[index:min(end+1,index+40),:2]-current[:2],axis=1);nearest=index+int(np.argmin(distances));index=min(nearest,end-1)if end<len(path)-1 else nearest;index,_=switch_if_settled(path,index,current,d.qvel)
   gear=int(path[min(index+1,len(path)-1),3]);target_index=index+1;arc=0.
   while target_index<len(path)-1 and arc<.45 and int(path[target_index+1,3])==gear:arc+=float(np.linalg.norm(path[target_index+1,:2]-path[target_index,:2]));target_index+=1
   relative=path[target_index,:2]-current[:2];lateral=-math.sin(current[2])*relative[0]+math.cos(current[2])*relative[1];steer=float(np.clip(math.atan2(1.2*lateral,max(float(relative@relative),.02)),-inner.max_steer,inner.max_steer));speed=gear*min(.6,.5/(1+abs(steer)));field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,states[k],'predictive',protocol['known_circles'],protocol['known_rectangles']);old=next(x for x in decisions if x['step']==k and x['candidate_role']=='ORDINARY'and x['stage']=='NOMINAL')['summary'];before=predictor.prediction_steps;proposal,gate=predictor.select(env,field,path,index,current,steer,speed,d.ctrl[ids]);new_diagnostics=json.loads(json.dumps(predictor.last_diagnostics));old_attempt=next(x for x in decisions if x['step']==k and x['stage']=='BACKUP_APPEND'and x['candidate_role']=='ORDINARY');old_appendable=old_attempt['detail']['status']=='APPENDABLE_BACKUP_FOUND';context_error=0.
   if old['status']=='MODEL_SAFE_COMMAND':
    context_error=float(max(np.max(abs(np.asarray(old['scoring_target'])-gate['scoring_target']))if proposal is not None else 0.,abs(old['current_projected_arc_m']-gate['current_projected_arc_m'])if proposal is not None else 0.));assert context_error<=1e-10,'REFERENCE_CONTEXT_CHANGED'
   summary=check=None;metric_old=metric_new=None;goal_progress=None;manager=None
   if proposal is not None:
    managercell=out/f'checkpoint_{k}';managercell.mkdir();manager=ReservedRecovery(predictor,mujoco,ids,managercell);summary=manager.admit_nominal(d,proposal,field,states[k],k);segments=path[index:min(gate['segment_end_index']+1,index+40),:3]
    def metric(pose):
     _,contour,heading=project_to_segment_path([pose],segments);return float(contour[0]+.2*abs(wrap(pose[2]-heading[0])))
    metric_new=metric(np.asarray(gate['predicted_end_pose']));goal_progress=float(np.linalg.norm(current[:2]-goal)-np.linalg.norm(np.asarray(gate['predicted_end_pose'])[:2]-goal))
    if old['status']=='MODEL_SAFE_COMMAND':metric_old=metric(np.asarray(old['predicted_end_pose']))
    if summary is not None:check=private_execute(manager,proposal,k)
   increment=bool(summary is not None and goal_progress>=.02 and(not old_appendable or(metric_old is not None and metric_old-metric_new>=.02)))
   records.append({'checkpoint':k,'path_source_step':event['step'],'reference_index':index,'maximum_reference_context_error':context_error,'original_nominal_status':old['status'],'original_highest_score_appendable':old_appendable,'new_nominal_gate':gate,'new_candidate_diagnostics':new_diagnostics,'new_appendable':summary is not None,'new_reserve_summary':summary,'new_backup_attempt':None if manager is None else manager.last_attempt,'full_private_execute':check,'predicted_goal_progress_m':goal_progress,'old_reference_terminal_error':metric_old,'new_reference_terminal_error':metric_new,'registered_increment':increment,'private_prediction_integrations_for_checkpoint':predictor.prediction_steps-before});print('CHECKPOINT',k,'appendable',summary is not None,'goal_progress',goal_progress,'tracking',metric_old,metric_new,'increment',increment,flush=True);dump('PROGRESS.json',{'records':records,'forecast_integrations':predictor.prediction_steps,'private_execute_integrations':extra})
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1;b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)));q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));actual=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)});minimum=min(minimum,float(pose_values(actual,[[q[0],q[1],yaw]])[0]))
   for c in d.contact:bad+=catalog.classify(c,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minimum>=.15-1e-8 and selfmargin>=0 and bad==0,'REPLAY_PHYSICAL_SAFETY_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'ORIGINAL_STATE_REPLAY_MISMATCH';assert predictor.prediction_steps+extra<=40000,'PRIVATE_BUDGET'
 assert len(records)==3 and steps==1968;status='PASS_WITH_REGISTERED_INCREMENT'if any(x['registered_increment']for x in records)else'COMPLETE_NO_REGISTERED_INCREMENT'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps+extra,'forecast_integrations':predictor.prediction_steps,'private_execution_integrations':extra,'maximum_old_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_native_clearance_m':minimum,'minimum_replay_self_margin_m':selfmargin,'bad_contacts':bad,'records':records,'registered_increments':sum(x['registered_increment']for x in records),'new_navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'input_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [cell/'v648_execution.jsonl',cell/'motion_estimate.jsonl',cell/'control_decisions.jsonl',root/'scene_model.mjb']},'scope':'three locked old states; target consistency and native appendability; no navigation success'};dump('COMPLETION.json',result);ledger.update(fixed_diagnostic_private_integrations=result['private_prediction_integrations'],status='PRE_NAV_'+status,closed=status!='PASS_WITH_REGISTERED_INCREMENT');ledgerpath.write_text(json.dumps(ledger,indent=2)+'\n');print('VALIDATION_COMPLETE',status,'private',result['private_prediction_integrations'],flush=True);assert status!='FAILED',error
