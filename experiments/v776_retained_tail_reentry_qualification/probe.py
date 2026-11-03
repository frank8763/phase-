"""Fixed coupled sensing/progress schedules with causal rolling full contracts."""
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
from retained_coupled import prepare_retained
from selection import initial_state,select
sys.path.insert(1,str(repo/'experiments/v769_geometry_reachability_qualification'))
from risk_domain import RiskDomain
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v776_retained_tail_reentry_qualification';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def clone(domain):
 copy=RecursiveDomain(domain.origin);copy.time=domain.time;copy.possible=domain.possible.copy();copy.distance=domain.distance.copy();copy.last=dict(domain.last);return copy
started=float(os.environ['PHASE_V776_STARTED']);deadline=float(os.environ['PHASE_V776_DEADLINE']);assert abs(deadline-started-600)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=600,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def timeout(*_):raise TimeoutError('V776_FIXED_600S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
actual_context='BASELINE';replay=validation=packets=0;predictor=None;records=[];status='RUNNING';min_actual=min_self=float('inf');max_replay=max_validation=0.;bad=0
try:
 assert read(repo/'runs/v771_geometry_audit_environment_recovery/RESULT.json')['status']=='GEOMETRY_REACHABILITY_ALL_SAVED_SETS_AND_QUERIES_VERIFIED'
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:old_packets=[json.loads(s)for s in stream]
  for packet in old_packets:
   regenerated=sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,initial_calls)
   assert packet_equal(packet,regenerated),'ORIGINAL_SENSOR_BACKEND_NOT_EXACT'
  dump('SENSOR_CALIBRATION.json',dict(status='ALL_ORIGINAL_177_NOISY_PACKETS_EXACT',packets=len(old_packets),model_initializations=0,new_integrations=0))
  assert len(old_packets)==177
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);fixed_geom=m.geom_pos.copy()
  static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;contactlog=gzip.open(root/'ACTUAL_CONTACTS.jsonl.gz','wt')
  def physical(data,public):
   global min_actual,min_self,bad
   box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),config['radius_m']]])});clearance=float(pose_values(truth,poses(data.qpos[None,:]))[0]);contacts=[catalog.classify(c,replay+validation,public,float(data.time))for c in data.contact];bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts);contactlog.write(json.dumps(dict(account_step=replay+validation,time=float(data.time),public=public,context=actual_context,qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),controls=data.ctrl[ids].tolist(),mocap=data.mocap_pos.tolist(),safety=[clearance,margin,*box.tolist()],contacts=contacts))+'\n');min_actual=min(min_actual,clearance);min_self=min(min_self,margin)
   assert clearance>=.15 and margin>=0 and bad==0 and np.array_equal(m.geom_pos,fixed_geom),'ACTUAL_SAFETY_OR_STATIC_MODEL_EXCEPTION';return [clearance,margin,*box.tolist()]
  rq=[];rv=[];rc=[];rm=[];rs=[]
  for row in rows[:32]:
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);rs.append(physical(d,row['step']));rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl[ids].copy());rm.append(d.mocap_pos.copy())
   max_replay=max(max_replay,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert max_replay<=1e-8
  checkpoint=mujoco.MjData(m);mujoco.mj_copyData(checkpoint,m,d);base=clone(decode(beliefs[32]['free_space_renewal']))
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
   np.savez_compressed(root/(label+'_PRIVATE.npz'),initial_act=real.act.copy(),initial_warmstart=real.qacc_warmstart.copy(),initial_full_ctrl=real.ctrl.copy(),initial_mocap_pos=real.mocap_pos.copy(),initial_mocap_quat=real.mocap_quat.copy(),initial_qpos=initial_q,initial_qvel=initial_v,initial_ctrl=last,initial_time=when,qpos=q,qvel=v,controls=controls,poses=p,self_bounds=self_bounds)
   return dict(label=label,target=target.tolist(),hold_first=hold_first,brake_after_native=brake,minimum_causal_clearance_m=minimum,minimum_causal_tick=int(np.argmin(values))+1,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,admissible=reason is None,reason=reason),q,v,controls
  def make_proof(record,z,domain):
   return dict(schema='V749_COUPLED_01',created_step=round(float(z['initial_time'])/.08),start_time=float(z['initial_time']),prefix_command=z['initial_ctrl'].tolist(),target=record['target'],controls=z['controls'].tolist(),qpos=z['qpos'].tolist(),qvel=z['qvel'].tolist(),poses=z['poses'].tolist(),forecast_state=dict(center=None,time=domain.time,hidden_world_geometry_used=False,free_space_renewal=encode(domain)),minimum_causal_predicted_clearance_m=record['minimum_causal_clearance_m'],minimum_predicted_self_domain_margin_m=record['self_margin_m'],terminal_speed_m_s=record['terminal_speed_m_s'],terminal_angular_speed_rad_s=record['terminal_angular_speed_rad_s'],total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False)
  def perform(real,command,q,v,public,store,replaying=False):
   global replay,validation,max_replay,max_validation
   predictor.command_map.assert_first(command,real.ctrl[ids]);error=0.
   for j in range(8):
    real.ctrl[:]=0.;real.ctrl[ids]=command;mujoco.mj_step(m,real)
    if replaying:replay+=1
    else:validation+=1
    motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real);safety=physical(real,public);error=max(error,float(np.max(abs(real.qpos-q[j]))),float(np.max(abs(real.qvel-v[j]))));assert error<=1e-8,'FULL_NATIVE_EXECUTION_MISMATCH'
    for key,value in [('qpos',real.qpos),('qvel',real.qvel),('controls',real.ctrl[ids]),('mocap',real.mocap_pos),('safety',safety)]:store[key].append(np.asarray(value).copy())
   if replaying:max_replay=max(max_replay,error)
   else:max_validation=max(max_validation,error)
   return error
  def observe(real,domain,public):
   xy,yaw=sensor_pose(real.qpos);packet=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,initial_calls);domain.update(packet);times=domain.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in times]);excess=float(domain.point_lower(truth,times).max())
   if isinstance(domain,RiskDomain):
    ij=np.rint((motion.xy(float(real.time))+6)/.01).astype(int);assert domain.allowed[tuple(ij)]and domain.possible[tuple(ij)],'ACTUAL_CENTER_OUTSIDE_CONDITIONAL_MAP_DOMAIN'
   assert excess<=1e-7,'CAUSAL_DOMAIN_TRUE_ACTOR_EXCLUSION';return dict(packet=packet,domain=encode(domain),maximum_actual_coverage_excess_m=excess)
  oldroot=repo/'runs/v772_map_conditioned_progress';old=np.load(oldroot/'MAP_HISTORY_MAIN_ACTUAL.npz')
  with gzip.open(oldroot/'MAP_HISTORY_MAIN_OBSERVATIONS.json.gz','rt')as f:original_obs=json.load(f)
  assert read(repo/'runs/v773_map_conditioned_progress_audit/RESULT.json')['status']=='MAP_CONDITIONED_PROGRESS_SAVED_EVIDENCE_VERIFIED'
  np.savez_compressed(root/'BASELINE_REPLAY.npz',qpos=rq,qvel=rv,controls=rc,mocap=rm,safety=rs)
  targets=[dict(index=i,target=[0.,0.,float(mean+diff),float(mean-diff)],mean=mean,difference=diff)for i,(mean,diff)in enumerate((x,y)for x in[0,1,2]for y in[-6,-3,0,3,6])];dump('TARGETS.json',targets)
  for k in [138,140,144]:
   name='TAIL_%03d'%k;actual_context=name;mujoco.mj_copyData(d,m,checkpoint);domain=RiskDomain(base.origin,protocol,'MAP_HISTORY')
   for pk in old_packets[:33]:domain.update(pk)
   store={key:[]for key in ['qpos','qvel','controls','mocap','safety']};observations=[]
   for j in range(k):
    sl=slice(j*8,j*8+8);assert np.all(old['controls'][sl]==old['controls'][j*8]);perform(d,old['controls'][j*8],old['qpos'][sl],old['qvel'][sl],33+j,store,True)
    for key in store:assert np.max(abs(np.asarray(store[key][-8:])-old[key][sl]))<=1e-8,'OLD_TAIL_FULL_STATE_CHANGED'
    ob=observe(d,domain,33+j);assert ob==original_obs[j],'OLD_TAIL_PACKET_OR_DOMAIN_CHANGED';observations.append(ob)
   np.savez_compressed(root/(name+'_REPLAY.npz'),**store)
   with gzip.open(root/(name+'_OBSERVATIONS.json.gz'),'wt')as f:json.dump(observations,f)
   dump(name+'_INITIAL_DOMAIN.json',encode(domain));candidates=[]
   for t in targets:
    before=[getattr(d,key).copy()for key in ['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat']];when=float(d.time);rec,q,v,ctrl=forecast(d,domain,np.asarray(t['target']),name+'_A%02d'%t['index'],hold_first=True)
    assert all(np.array_equal(getattr(d,key),val)for key,val in zip(['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat'],before))and d.time==when,'QUALIFICATION_MUTATED_RETAINED_REAL_STATE'
    z=np.load(root/(rec['label']+'_PRIVATE.npz'));rec.update(action_index=t['index'],static_min_m=float(pose_values(static,z['poses']).min()),unknown_min_m=float(domain.body_lower(z['poses'],when+np.arange(1,329)*.01).min()),initial_state_unmodified=True);candidates.append(rec)
   qualified=sorted([x for x in candidates if x['admissible']],key=lambda x:(-x['goal_progress_m'],-x['minimum_causal_clearance_m'],x['action_index']));record=dict(name=name,local_public=k,old_tail_remaining_native=(161-k)*8,candidates=candidates,admissible_count=len(qualified),positive_progress_count=sum(x['goal_progress_m']>=.05 for x in qualified),best=None if not qualified else qualified[0],ranking=[x['action_index']for x in qualified],new_actual_executed=False);records.append(record);dump('STATES.json',records);print(json.dumps({key:val for key,val in record.items()if key!='candidates'}),flush=True)
  contactlog.close();assert replay==3632 and predictor.prediction_steps==14760 and validation==packets==0
  assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='SAVED_RETAINED_TAIL_REENTRY_QUALIFICATION_COMPLETE';dump('RESULT.json',dict(status=status,states=records,original_replay_native=replay,private_integrations=predictor.prediction_steps,actual_validation_native=0,actual_new_packets=0,old_replayed_packets=422,minimum_actual_clearance_m=min_actual,minimum_actual_self_margin_m=min_self,bad_contacts=bad,maximum_replay_error=max_replay,new_complete_navigation=0,new_confirmation=0,training_updates=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0)
 if 'contactlog'in globals()and not contactlog.closed:contactlog.close()
 window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_native=replay,private_integrations=None if predictor is None else predictor.prediction_steps,actual_validation_native=validation,actual_new_packets=packets,completed_records=len(records),new_navigation=0))
