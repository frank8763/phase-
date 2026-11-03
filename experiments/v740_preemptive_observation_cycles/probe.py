"""Fixed old-state two-cycle observation/advance diagnostic."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(source));sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'));sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from recursive_domain import RecursiveDomain
from renewal_state import decode,encode
from sensor_model import packet as sensed_packet
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v740_preemptive_observation_cycles';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def clone(domain):
 copy=RecursiveDomain(domain.origin);copy.time=domain.time;copy.possible=domain.possible.copy();copy.distance=domain.distance.copy();copy.last=dict(domain.last);return copy
started=float(os.environ['PHASE_V740_STARTED']);deadline=float(os.environ['PHASE_V740_DEADLINE']);assert abs(deadline-started-900)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=900,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def timeout(*_):raise TimeoutError('V740_FIXED_900S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
replay=validation=packets=0;predictor=None;records=[];status='RUNNING';min_actual=min_self=float('inf');max_replay=max_validation=0.;bad=0
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:old_packets=[json.loads(s)for s in stream]
  for packet in old_packets:
   regenerated=sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,initial_calls)
   assert all(np.array_equal(packet[k],regenerated[k])for k in['lidar','depth']),'ORIGINAL_SENSOR_BACKEND_NOT_EXACT'
  dump('SENSOR_CALIBRATION.json',dict(status='ALL_ORIGINAL_177_NOISY_PACKETS_EXACT',packets=len(old_packets),model_initializations=0,new_integrations=0))
  assert len(old_packets)==177
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);fixed_geom=m.geom_pos.copy()
  static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;contactlog=gzip.open(root/'ACTUAL_CONTACTS.jsonl.gz','wt')
  def physical(data,public):
   global min_actual,min_self,bad
   box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),config['radius_m']]])});clearance=float(pose_values(truth,poses(data.qpos[None,:]))[0]);contacts=[catalog.classify(c,replay+validation,public,float(data.time))for c in data.contact];bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts);contactlog.write(json.dumps(dict(account_step=replay+validation,time=float(data.time),public=public,contacts=contacts))+'\n');min_actual=min(min_actual,clearance);min_self=min(min_self,margin)
   assert clearance>=.15 and margin>=0 and bad==0 and np.array_equal(m.geom_pos,fixed_geom),'ACTUAL_SAFETY_OR_STATIC_MODEL_EXCEPTION';return [clearance,margin,*box.tolist()]
  snapshots={};rq=[];rv=[];rc=[];rm=[];rs=[]
  for row in rows[:130]:
   if row['step']in[73,90]:
    c=mujoco.MjData(m);mujoco.mj_copyData(c,m,d);snapshots[row['step']]=c
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);rs.append(physical(d,row['step']));rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl.copy());rm.append(d.mocap_pos.copy())
   max_replay=max(max_replay,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert max_replay<=1e-8,'ORIGINAL_REPLAY_MISMATCH'
  c=mujoco.MjData(m);mujoco.mj_copyData(c,m,d);snapshots[130]=c;np.savez_compressed(root/'ORIGINAL_1040_NATIVE_REPLAY.npz',qpos=rq,qvel=rv,controls=rc,mocap=rm,safety=rs)
  def forecast(real,domain,target,label,horizon=328,brake=248,hold_first=False):
   initial_q=real.qpos.copy();initial_v=real.qvel.copy();last=real.ctrl[ids].copy();when=float(real.time);prefix_q=[];prefix_v=[];prefix_bounds=[]
   if hold_first:
    scratch=mujoco.MjData(predictor.model);mujoco.mj_resetData(predictor.model,scratch)
    for n in['qpos','qvel','act','qacc_warmstart']:getattr(scratch,n)[:]=getattr(real,n)
    scratch.time=when;scratch.ctrl[:]=0.;scratch.ctrl[ids]=last;mujoco.mj_forward(predictor.model,scratch);scratch.qacc_warmstart[:]=real.qacc_warmstart
    for _ in range(8):
     mujoco.mj_step(predictor.model,scratch);predictor.prediction_steps+=1;mujoco.mj_kinematics(predictor.model,scratch);prefix_q.append(scratch.qpos.copy());prefix_v.append(scratch.qvel.copy());prefix_bounds.append(predictor.self_geometry.actual(predictor.model,scratch))
    p=predictor.predict(scratch,target,ids,last,320,160);q=np.vstack([prefix_q,predictor.last_forecast_qpos]);v=np.vstack([prefix_v,predictor.last_forecast_qvel]);controls=np.vstack([np.repeat([last],8,axis=0),predictor.command_map.sequence(target,last,320,160)]);self_bounds=np.vstack([prefix_bounds,predictor.last_self_bounds]);brake=168
   else:
    p=predictor.predict(real,target,ids,last,horizon,brake);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();controls=predictor.command_map.sequence(target,last,horizon,brake);self_bounds=predictor.last_self_bounds.copy()
   p=poses(q);values=np.minimum(pose_values(static,p),domain.body_lower(p,when+np.arange(1,329)*.01));minimum=float(values.min());margin=float(containment_margin(self_bounds,bounds).min());speed=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]));progress=float(np.linalg.norm(initial_q[:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
   np.savez_compressed(root/(label+'_PRIVATE.npz'),initial_qpos=initial_q,initial_qvel=initial_v,initial_ctrl=last,initial_time=when,qpos=q,qvel=v,controls=controls,poses=p,self_bounds=self_bounds)
   return dict(label=label,target=target.tolist(),hold_first=hold_first,brake_after_native=brake,minimum_causal_clearance_m=minimum,minimum_causal_tick=int(np.argmin(values))+1,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,admissible=reason is None,reason=reason),q,v,controls
  def execute(real,domain,proof):
   global validation,packets,max_validation
   record,q,v,controls=proof;assert record['admissible'];label=record['label'];updated=clone(domain);actual_q=[];actual_v=[];actual_c=[];actual_m=[];safety=[];observations=[];error=0.;public_start=round(real.time/.08);before=poses(real.qpos[None,:])[0]
   for tick,command in enumerate(controls):
    if tick%8==0:predictor.command_map.assert_first(command,real.ctrl[ids])
    real.ctrl[:]=0.;real.ctrl[ids]=command;mujoco.mj_step(m,real);validation+=1;motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real);safety.append(physical(real,public_start+tick//8));error=max(error,float(np.max(abs(real.qpos-q[tick]))),float(np.max(abs(real.qvel-v[tick]))));assert error<=1e-8,'FULL_NATIVE_BRANCH_MISMATCH';actual_q.append(real.qpos.copy());actual_v.append(real.qvel.copy());actual_c.append(real.ctrl[ids].copy());actual_m.append(real.mocap_pos.copy())
    if (tick+1)%8==0:
     pp=poses(real.qpos[None,:])[0];public=public_start+(tick+1)//8;packet=sensed_packet(pp[:2].astype(np.float32),pp[2],float(real.time),public,protocol,motion,initial_calls);updated.update(packet);future=updated.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in future]);excess=float(updated.point_lower(truth,future).max());assert excess<=1e-7,'NEW_SENSOR_DOMAIN_EXCLUDED_TRUE_ACTOR';observations.append(dict(packet=packet,domain=encode(updated),maximum_actual_coverage_excess_m=excess));packets+=1
   max_validation=max(max_validation,error);np.savez_compressed(root/(label+'_ACTUAL.npz'),qpos=actual_q,qvel=actual_v,controls=actual_c,mocap=actual_m,safety=safety)
   with gzip.open(root/(label+'_OBSERVATIONS.json.gz'),'wt')as stream:json.dump(observations,stream)
   actualp=poses(np.asarray(actual_q));now=actualp[-1];future=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);old_hold=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,updated.time+future)).min());fresh_hold=float(np.minimum(pose_values(static,hold),updated.body_lower(hold,updated.time+future)).min())
   record.update(actual_native_steps=328,actual_state_error=error,actual_packets=41,actual_translation_m=float(np.linalg.norm(now[:2]-before[:2])),actual_yaw_sweep_rad=float(np.ptp(np.unwrap(np.r_[before[2],actualp[:,2]]))),actual_goal_progress_m=float(np.linalg.norm(before[:2]-protocol['goal_xy'])-np.linalg.norm(now[:2]-protocol['goal_xy'])),fresh_terminal_hold_geometry_m=fresh_hold,without_new_observation_terminal_hold_geometry_m=old_hold,actual_final_domain_sha256=encode(updated)['possible_bits_sha256'])
   return updated
  for step in[73,90,130]:
   for amplitude in[0.,8.,-8.]:
    branch=dict(step=step,amplitude=amplitude,cycles=[],completed_cycles=0,qualified=False);mujoco.mj_copyData(d,m,snapshots[step]);base=decode(beliefs[step]['free_space_renewal']);domain=clone(base);branch_start_q=d.qpos.copy()
    for cycle in[1,2]:
     stem='S%03d_A%s_C%d'%(step,('P'if amplitude>=0 else'M')+str(int(abs(amplitude))),cycle);scan=forecast(d,domain,np.array([0.,0.,-amplitude,amplitude]),stem+'_SCAN',hold_first=True);result=dict(cycle=cycle,scan=scan[0],successors=[],selected_successor=None);branch['cycles'].append(result)
     if not scan[0]['admissible']:branch['outcome']='SCAN_NOT_CERTIFIED';break
     domain=execute(d,domain,scan);choices=[(0.,4.,4.),(0.,2.,6.),(0.,6.,2.),(-.42722137342572125,4.,4.),(.42722137342572125,4.,4.)];proofs=[]
     for j,(steer,left,right)in enumerate(choices):
      target=ReservedRecovery.target(steer,4.);target[2:]=[left,right];proof=forecast(d,domain,target,stem+'_ADVANCE_%d'%j);candidate=proof[0];candidate['index']=j
      if candidate['reason']is None and candidate['goal_progress_m']<.02:candidate.update(admissible=False,reason='GOAL_PROGRESS')
      result['successors'].append(candidate);proofs.append(proof)
     eligible=[x for x in proofs if x[0]['admissible']]
     if not eligible:branch['outcome']='NO_CONCRETE_SUCCESSOR';break
     selected=max(eligible,key=lambda x:(x[0]['goal_progress_m'],x[0]['minimum_causal_clearance_m'],-x[0]['index']));result['selected_successor']=selected[0]['index'];domain=execute(d,domain,selected);branch['completed_cycles']+=1
    branch['total_goal_progress_m']=float(np.linalg.norm(branch_start_q[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy']));branch['qualified']=branch['completed_cycles']==2 and branch['total_goal_progress_m']>0
    if branch['qualified']:branch['outcome']='TWO_OBSERVATION_ADVANCE_CYCLES_COMPLETED'
    records.append(branch);dump('BRANCHES.json',records);dump('ACTIVE.json',dict(status='RUNNING',completed_branches=len(records),replay=replay,private=predictor.prediction_steps,validation=validation,actual_packets=packets));print(json.dumps(branch),flush=True)
  contactlog.close();assert replay==1040 and predictor.prediction_steps<=35424 and validation<=11808 and packets*8==validation and len(records)==9
  assert all(sha(repo/n)==h for n,h in freeze['files'].items())
  status='FIXED_PREEMPTIVE_OBSERVATION_CYCLES_COMPLETE';dump('RESULT.json',dict(status=status,branches=records,original_replay_steps=replay,private_integrations=predictor.prediction_steps,scene_validation_integrations=validation,actual_new_packets=packets,forecast_coverage_samples=packets*329,maximum_original_replay_error=max_replay,maximum_candidate_state_error=max_validation,minimum_actual_native_clearance_m=min_actual,minimum_actual_self_margin_m=min_self,bad_contacts=bad,qualified_by_state={str(s):sum(x['qualified']and x['amplitude']!=0 for x in records if x['step']==s)for s in[73,90,130]},component_qualified=all(any(x['qualified']and x['amplitude']!=0 for x in records if x['step']==s)for s in[73,130]),new_navigation_samples=0,new_confirmation_samples=0,training_updates=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_steps=replay,private_integrations=None if predictor is None else predictor.prediction_steps,scene_validation_integrations=validation,actual_new_packets=packets,completed_branches=len(records),new_navigation_samples=0))
