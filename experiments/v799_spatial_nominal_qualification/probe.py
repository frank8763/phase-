"""Frozen same-input-class appendability diagnostic; no new navigation."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent;source=repo/'experiments/v793_complete_joint_navigation'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(source))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from motion_tracker import install_time_gate
from motion_evaluator import check_forecast
root=repo/'runs/v799_spatial_nominal_qualification';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
started=float(os.environ['PHASE_V799_STARTED']);deadline=float(os.environ['PHASE_V799_DEADLINE']);assert abs(deadline-started-600)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=600,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window)
def timeout(*_):raise TimeoutError('V799_FIXED_600S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
replay=validation=validation_repeat=0;predictor=None;records=[];status='RUNNING';min_actual=float('inf');min_self=float('inf');bad=0;max_replay=max_validation=0.
def pose(q):return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
def equal(a,b):
 if isinstance(a,dict):assert isinstance(b,dict)and set(a)==set(b);return max([equal(a[k],b[k])for k in a]or[0.])
 if isinstance(a,list):assert isinstance(b,list)and len(a)==len(b);return max([equal(x,y)for x,y in zip(a,b)]or[0.])
 if type(a)in(float,int)and type(b)in(float,int):return abs(a-b)
 assert a==b;return 0.
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v793_complete_joint_navigation/main_slot01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
  rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};decisions=[json.loads(s)for s in(cell/'control_decisions.jsonl').read_text().splitlines()]
  plan=read(own/'FIXED_COMMANDS.json');m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
  geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);fixed_geom=m.geom_pos.copy()
  static=dict(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  prefix_q=[];prefix_v=[];prefix_bounds=[]
  def private_native(model,data):
   mujoco.mj_step(model,data);mujoco.mj_kinematics(model,data);prefix_q.append(data.qpos.copy());prefix_v.append(data.qvel.copy());prefix_bounds.append(predictor.self_geometry.actual(model,data).copy())
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,private_native);ids=predictor.command_map.ids
  contact_log=gzip.open(root/'ACTUAL_CONTACTS.jsonl.gz','wt')
  def physical(data,public):
   global min_actual,min_self,bad
   actual_bounds=geometry.actual(m,data);margin=float(containment_margin(actual_bounds,bounds));truthfield=SimpleNamespace(**{**static,'half':(actual_bounds[2:]-actual_bounds[:2])/2,'center_local':(actual_bounds[2:]+actual_bounds[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),config['radius_m']]])})
   clearance=float(pose_values(truthfield,[pose(data.qpos)])[0]);min_actual=min(min_actual,clearance);min_self=min(min_self,margin)
   contacts=[catalog.classify(c,replay+validation+validation_repeat,public,float(data.time))for c in data.contact];bad+=sum(x['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for x in contacts)
   contact_log.write(json.dumps(dict(account_step=replay+validation+validation_repeat,public=public,time=float(data.time),qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),ctrl=data.ctrl.tolist(),mocap=data.mocap_pos.tolist(),clearance=clearance,self_margin=margin,actual_bounds=actual_bounds.tolist(),contacts=contacts))+'\n')
   assert clearance>=.15 and margin>=0 and bad==0 and np.array_equal(m.geom_pos,fixed_geom),'ACTUAL_SAFETY_OR_MODEL_EXCEPTION'
   return clearance,margin
  snapshots={};rq=[];rv=[];rc=[];rm=[];rs=[]
  state_spec=mujoco.mjtState.mjSTATE_INTEGRATION
  def full_state(data):
   value=np.empty(mujoco.mj_stateSize(m,state_spec));mujoco.mj_getState(m,data,value,state_spec);return value
  with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as stream:original_native=[json.loads(s)for s in stream]
  for row in rows[:617]:
   if row['step']in[404,541,617]:
    snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[row['step']]=snap
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);nr=original_native[replay-1];max_replay=max(max_replay,float(np.max(abs(d.qpos-nr['qpos_full']))),float(np.max(abs(d.qvel-nr['qvel_full']))),float(np.max(abs(d.ctrl-nr['actual_ctrl']))));assert max_replay<=1e-8,'FULL_NATIVE_ORIGINAL_REPLAY_MISMATCH';safe=physical(d,row['step']);rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl.copy());rm.append(d.mocap_pos.copy());rs.append(safe)
   max_replay=max(max_replay,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert max_replay<=1e-8,'ORIGINAL_REPLAY_MISMATCH'
  snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[617]=snap
  np.savez_compressed(root/'ORIGINAL_4936_NATIVE_REPLAY.npz',qpos=rq,qvel=rv,ctrl=rc,mocap=rm,safety=rs)
  validated=set();witnesses=[]
  from serial_predictor import project_to_segment_path
  for entry in plan['checkpoints']:
   step=entry['step'];snap=snapshots[step];mujoco.mj_copyData(d,m,snap)
   state={k:v for k,v in beliefs[step].items()if k!='step'};assert state['center']is None and abs(state['time']-d.time)<1e-10
   field=SimpleNamespace(**static);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
   coverage=check_forecast(config,state);assert coverage['passed'];dump('COVERAGE_%03d.json'%step,coverage)
   reference=np.asarray(entry['reference_path']);segments=reference[entry['index']:min(len(reference),entry['index']+40),:3]
   for rank,candidate in enumerate(entry['candidates']):
    label='S%03d_R%02d'%(step,rank);mujoco.mj_copyData(d,m,snap)
    command=np.asarray(candidate['first_command']);target=np.asarray(candidate['target_command'])
    predictor.command_map.assert_first(command,d.ctrl[ids]);assert np.array_equal(command,predictor.command_map.step(target,d.ctrl[ids]))
    ordinary=predictor.predict(d,target,ids,d.ctrl[ids],240,80)
    ordinary_values=field.trajectory_values(ordinary,.01);ordinary_static=pose_values(SimpleNamespace(**static),ordinary)
    ordinary_margin=predictor.prediction_self_margin;ordinary_speed=predictor.terminal_speed
    assert candidate['reason']=='TIME_CLEARANCE'and ordinary_values.min()<.155
    assert max(abs(float(ordinary_values.min())-candidate['minimum_clearance_m']),abs(ordinary_margin-candidate['self_domain_margin_m']),abs(ordinary_speed-candidate['terminal_speed_m_s']))<=1e-8,'OLD_NOMINAL_FORECAST_MISMATCH'
    spatial_ok=bool(ordinary_static.min()>=.155 and ordinary_margin>=.002 and ordinary_speed<=.025)
    goal_progress=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy'])-np.linalg.norm(ordinary[-1,:2]-protocol['goal_xy']))
    np.savez_compressed(root/(label+'_ORDINARY.npz'),qpos=predictor.last_forecast_qpos,qvel=predictor.last_forecast_qvel,poses=ordinary,controls=predictor.command_map.sequence(target,d.ctrl[ids],240,80),self_bounds=predictor.last_self_bounds)
    prefix_q.clear();prefix_v.clear();prefix_bounds.clear();tails=[];original_predict=predictor.predict
    def recording(real,target_command,ids_,last_command,horizon=240,brake_after=None):
     trajectory=original_predict(real,target_command,ids_,last_command,horizon,brake_after);i=len(tails)
     np.savez_compressed(root/(label+'_TAIL_%02d.npz'%i),qpos=predictor.last_forecast_qpos,qvel=predictor.last_forecast_qvel,poses=trajectory,controls=predictor.command_map.sequence(target_command,last_command,horizon,brake_after),self_bounds=predictor.last_self_bounds)
     complete=np.vstack([ReservedRecovery.poses(prefix_q),trajectory]);from unseen_prior import clearance as unknown_clearance
     tails.append(dict(index=i,target_command=np.asarray(target_command).tolist(),brake_after=brake_after,static_minimum_m=float(pose_values(SimpleNamespace(**static),complete).min()),unknown_future_minimum_m=float(unknown_clearance(field,complete,state,np.arange(1,329)*.01).min())));return trajectory
    predictor.predict=recording;reserved=ReservedRecovery(predictor,mujoco,ids,root)
    before=predictor.prediction_steps;original_state=full_state(d).copy()
    summary=reserved.admit_nominal(d,command,field,state,step);predictor.predict=original_predict
    assert np.array_equal(full_state(d),original_state),'QUALIFICATION_MUTATED_REAL'
    assert len(prefix_q)==8 and len(tails)==len(reserved.last_attempt['candidates'])
    np.savez_compressed(root/(label+'_PREFIX.npz'),qpos=prefix_q,qvel=prefix_v,controls=np.repeat([command],8,axis=0),self_bounds=prefix_bounds)
    prefix_arc=float(project_to_segment_path(ReservedRecovery.poses(prefix_q)[-1:],segments)[0][0]-project_to_segment_path([pose(snap.qpos)],segments)[0][0])
    prefix_goal=float(np.linalg.norm(snap.qpos[:2]-protocol['goal_xy'])-np.linalg.norm(prefix_q[-1][:2]-protocol['goal_xy']))
    record=dict(step=step,rank=rank,label=label,ordinary_candidate=candidate,ordinary_goal_progress_m=goal_progress,nominal_static_minimum_m=float(ordinary_static.min()),nominal_spatial_eligible=spatial_ok,actual_prefix_arc_progress_m=prefix_arc,actual_prefix_goal_progress_m=prefix_goal,append_summary=summary,detail=reserved.last_attempt,tail_files=tails,private_steps=predictor.prediction_steps-before+240,validation_steps=0,validation_repeat_steps=0,qualified_short_prefix_witness=False)
    if summary is not None and spatial_ok and prefix_goal>=.001 and step not in validated:
     cache=reserved.cache;q=np.vstack([prefix_q,cache['qpos']]);v=np.vstack([prefix_v,cache['qvel']]);controls=np.vstack([np.repeat([command],8,axis=0),cache['controls']]);first=None;first_events=None
     for repeating in [False,True]:
      mujoco.mj_copyData(d,m,snap);aq=[];av=[];ac=[];am=[];safety=[];states=[];events=[];error=0.
      for tick,c in enumerate(controls):
       if tick%8==0:predictor.command_map.assert_first(c,d.ctrl[ids])
       d.ctrl[:]=0.;d.ctrl[ids]=c;mujoco.mj_step(m,d)
       if repeating:validation_repeat+=1
       else:validation+=1
       motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);safety.append(physical(d,step+tick//8));error=max(error,float(np.max(abs(d.qpos-q[tick]))),float(np.max(abs(d.qvel-v[tick]))));assert error<=1e-8,'NATIVE_BRANCH_FORECAST_MISMATCH'
       aq.append(d.qpos.copy());av.append(d.qvel.copy());ac.append(c.copy());am.append(d.mocap_pos.copy());states.append(full_state(d))
       events.append([{k:v for k,v in catalog.classify(c,0,step+tick//8,float(d.time)).items()if k!='physics_step'}for c in d.contact])
      name=label+('_REPEAT'if repeating else'')+'_ACTUAL.npz'
      np.savez_compressed(root/name,qpos=aq,qvel=av,controls=ac,mocap=am,safety=safety,integration=states)
      if repeating:
       repeat_error=float(np.max(abs(np.asarray(states)-first)));assert repeat_error<=1e-8 and events==first_events,'COMPLETE_BRANCH_REPEAT_MISMATCH'
      else:first=np.asarray(states);first_events=events
     validated.add(step);max_validation=max(max_validation,error)
     witness=bool(prefix_goal>=.001)
     record.update(validation_steps=328,validation_repeat_steps=328,full_native_state_error=error,complete_repeat_error=repeat_error,qualified_short_prefix_witness=witness,selected_target=cache['target'].tolist(),selected_tail_goal_progress_m=float(np.linalg.norm(snap.qpos[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy'])))
     if witness:witnesses.append(dict(step=step,rank=rank,first_prefix_arc_m=prefix_arc,first_prefix_goal_m=prefix_goal))
    records.append(record);dump('CANDIDATES.json',records);dump('ACTIVE.json',dict(status='RUNNING',step=step,rank=rank,completed_commands=len(records),private_steps=predictor.prediction_steps,replay_steps=replay,validation_steps=validation,repeat_steps=validation_repeat));print(json.dumps(dict(step=step,rank=rank,spatial_eligible=spatial_ok,joint=summary is not None,actual_witness=record['qualified_short_prefix_witness'])),flush=True)
  contact_log.close();assert replay==4936 and predictor.prediction_steps<=522600 and validation<=984 and validation_repeat==validation and len(records)==75
  assert all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED_AFTER_RUN'
  status='FIXED_SPATIAL_PREFIX_JOINT_QUALIFICATION_COMPLETE'
  dump('RESULT.json',dict(status=status,records=records,original_replay_steps=replay,private_integrations=predictor.prediction_steps,scene_validation_integrations=validation,scene_repeat_integrations=validation_repeat,maximum_replay_error=max_replay,maximum_validation_error=max_validation,minimum_actual_native_clearance_m=min_actual,minimum_actual_self_margin_m=min_self,bad_contacts=bad,new_navigation_samples=0,new_confirmation_samples=0,training_updates=0,physically_verified_positive_witnesses=witnesses,qualification_passed=bool(witnesses)))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_steps=replay,private_integrations=None if predictor is None else predictor.prediction_steps,scene_validation_integrations=validation,scene_repeat_integrations=validation_repeat,completed_commands=len(records),new_navigation_samples=0))
