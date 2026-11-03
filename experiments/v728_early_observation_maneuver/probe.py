"""One early fixed-state experiment; deterministic risk, actual observed rays."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent;source=repo/'experiments/v721_recursive_unseen_navigation'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(source));sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from recursive_domain import RecursiveDomain
from renewal_state import decode,encode
from sensor_model import packet as sensed_packet
root=repo/'runs/v728_early_observation_maneuver';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();started=float(os.environ['PHASE_V728_STARTED']);deadline=float(os.environ['PHASE_V728_DEADLINE']);assert abs(deadline-started-300)<1e-6 and begun<deadline;window=dict(started_unix=started,actual_probe_started_unix=begun,absolute_deadline_unix=deadline,limit_s=300,pid=os.getpid(),round_closed=False)
dump('ROUND_WINDOW.json',window);replay=validation=0;predictor=None;records=[];status='RUNNING';maximum_replay_error=0.;maximum_validation_error=0.;actual_min=float('inf');self_min=float('inf');bad=0
def timeout(*_):raise TimeoutError('V728_FIXED_ABSOLUTE_300S_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 assert read(repo/'runs/v728_sensor_calibration/RESULT.json')['status']=='ORIGINAL_65_RAW_NOISY_PACKETS_EXACT'
 with (repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);rows=[json.loads(s)for s in (cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old_packets=[json.loads(s)for s in f][:65]
  original_domain=decode(beliefs[64]['free_space_renewal']);m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geom=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
  static=dict(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids
  def pose(q):return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
  def physical(data,public):
   global actual_min,self_min,bad
   box=geom.actual(m,data);self_min=min(self_min,float(containment_margin(box,bounds)));field=SimpleNamespace(**{**static,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),.10]])});actual_min=min(actual_min,float(pose_values(field,[pose(data.qpos)])[0]));assert np.array_equal(m.geom_pos,model_geom_pos),'STATIC_MODEL_CHANGED'
   for c in data.contact:bad+=catalog.classify(c,replay+validation,public,float(data.time))['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert actual_min>=.15 and self_min>=0 and bad==0,'ACTUAL_SAFETY_EXCEPTION'
  model_geom_pos=m.geom_pos.copy();replay_q=[];replay_v=[];replay_ctrl=[]
  for row in rows[:64]:
   d.ctrl[:]=row['ctrl']
   for _ in range(8):mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);physical(d,row['step']);replay_q.append(d.qpos.copy());replay_v.append(d.qvel.copy());replay_ctrl.append(d.ctrl.copy())
   maximum_replay_error=max(maximum_replay_error,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert maximum_replay_error<=1e-8
  np.savez_compressed(root/'ORIGINAL_512_NATIVE_REPLAY.npz',qpos=replay_q,qvel=replay_v,ctrl=replay_ctrl)
  checkpoint=mujoco.MjData(m);mujoco.mj_copyData(checkpoint,m,d);assert abs(original_domain.time-d.time)<1e-10
  proposal=np.asarray(rows[64]['ctrl'])[ids];predictor.command_map.assert_first(proposal,d.ctrl[ids]);scratch=mujoco.MjData(predictor.model);mujoco.mj_resetData(predictor.model,scratch)
  for n in ['qpos','qvel','act','qacc_warmstart']:getattr(scratch,n)[:]=getattr(d,n)
  scratch.time=d.time;scratch.ctrl[:]=0.;scratch.ctrl[ids]=proposal;mujoco.mj_forward(predictor.model,scratch);scratch.qacc_warmstart[:]=d.qacc_warmstart;pq=[];pv=[];prefix_margin=float('inf')
  for _ in range(8):predictor.native(predictor.model,scratch);predictor.prediction_steps+=1;mujoco.mj_kinematics(predictor.model,scratch);pq.append(scratch.qpos.copy());pv.append(scratch.qvel.copy());prefix_margin=min(prefix_margin,float(containment_margin(predictor.self_geometry.actual(predictor.model,scratch),bounds)))
  pq=np.asarray(pq);pv=np.asarray(pv);before=pose(checkpoint.qpos);choices=[(None,0.)]+[(s,w)for s in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]for w in [4.,8.]]
  for index,(steer,wheel)in enumerate(choices):
   target=np.r_[proposal[:2],0.,0.]if steer is None else ReservedRecovery.target(steer,wheel);brake=160 if steer is None else 240;trajectory=predictor.predict(scratch,target,ids,proposal,horizon=320,brake_after=brake);q=np.vstack([pq,predictor.last_forecast_qpos]);v=np.vstack([pv,predictor.last_forecast_qvel]);poses=np.vstack([[pose(x)for x in pq],trajectory]);controls=np.vstack([np.repeat([proposal],8,axis=0),predictor.command_map.sequence(target,proposal,320,brake)]);values=np.minimum(pose_values(SimpleNamespace(**static),poses),original_domain.body_lower(poses,checkpoint.time+np.arange(1,329)*.01));minimum=float(values.min());signed=float((poses[-1,:2]-pose(pq[-1])[:2])@np.array([math.cos(pose(pq[-1])[2]),math.sin(pose(pq[-1])[2])]))
   reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if min(prefix_margin,predictor.prediction_self_margin)<.002 else'TERMINAL_SPEED'if predictor.terminal_speed>.025 else'FORWARD_PROGRESS'if steer is not None and signed<.02 else None
   row=dict(index=index,steer=steer,wheel=wheel,target_command=target.tolist(),minimum_causal_clearance_m=minimum,self_domain_margin_m=min(prefix_margin,predictor.prediction_self_margin),terminal_speed_m_s=predictor.terminal_speed,reason=reason,admissible=reason is None,validation_steps=0,initial_state_public_step=64,terminal_pose=poses[-1].tolist())
   np.savez_compressed(root/('CANDIDATE_%02d_PRIVATE.npz'%index),qpos=q,qvel=v,poses=poses,controls=controls)
   if reason is None:
    domain=RecursiveDomain(original_domain.origin);domain.possible=original_domain.possible.copy();domain.distance=original_domain.distance.copy();domain.time=original_domain.time;domain.last=dict(original_domain.last);mujoco.mj_copyData(d,m,checkpoint);actual_q=[];actual_v=[];actual_ctrl=[];packets=[];coverage=[];error=0.
    for tick,ctrl in enumerate(controls):
     d.ctrl[:]=0.;d.ctrl[ids]=ctrl;mujoco.mj_step(m,d);validation+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);physical(d,65+tick//8);actual_q.append(d.qpos.copy());actual_v.append(d.qvel.copy());actual_ctrl.append(d.ctrl[ids].copy());error=max(error,float(np.max(abs(d.qpos-q[tick]))),float(np.max(abs(d.qvel-v[tick]))));assert error<=1e-8
     if (tick+1)%8==0:
      public_step=64+(tick+1)//8;pp=pose(d.qpos);packet=sensed_packet(pp[:2],pp[2],float(d.time),public_step,protocol,motion,initial_calls);domain.update(packet);packets.append(dict(packet=packet,domain=encode(domain)));times=domain.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in times]);excess=float(domain.point_lower(truth,times).max());coverage.append(excess);assert excess<=1e-7,'ACTUAL_FUTURE_ACTOR_EXCLUDED'
    maximum_validation_error=max(maximum_validation_error,error);now=pose(d.qpos);future=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);advance=hold.copy();advance[:,:2]+=np.minimum(future/1.6,1)[:,None]*.30*np.array([math.cos(now[2]),math.sin(now[2])]);hold_min=float(np.minimum(pose_values(SimpleNamespace(**static),hold),domain.body_lower(hold,domain.time+future)).min());advance_min=float(np.minimum(pose_values(SimpleNamespace(**static),advance),domain.body_lower(advance,domain.time+future)).min());yawchange=float((now[2]-before[2]+np.pi)%(2*np.pi)-np.pi)
    row.update(validation_steps=328,full_native_state_error=error,actual_yaw_change_rad=yawchange,actual_goal_progress_m=float(np.linalg.norm(before[:2]-protocol['goal_xy'])-np.linalg.norm(now[:2]-protocol['goal_xy'])),terminal_fresh_hold_3_28s_lower_m=hold_min,terminal_fresh_geometric_forward_0_30m_lower_m=advance_min,geometric_forward_witness_passed=advance_min>=.155,actual_new_sensor_packets=len(packets),actual_forecast_coverage_samples=len(coverage)*329,maximum_actual_coverage_excess_m=max(coverage),terminal_domain_sha256=encode(domain)['possible_bits_sha256'])
    np.savez_compressed(root/('CANDIDATE_%02d_ACTUAL.npz'%index),qpos=actual_q,qvel=actual_v,controls=actual_ctrl)
    with gzip.open(root/('CANDIDATE_%02d_OBSERVATIONS.json.gz'%index),'wt')as f:json.dump(packets,f)
   records.append(row);dump('CANDIDATES.json',records);print(json.dumps(row),flush=True)
  assert replay==512 and predictor.prediction_steps==3528 and validation<=3608
  assert all(sha(repo/n)==h for n,h in freeze['files'].items())
  status='FIXED_EARLY_OBSERVATION_NATIVE_DIAGNOSIS_COMPLETE';dump('RESULT.json',dict(status=status,candidates=records,original_replay_steps=replay,private_prediction_integrations=predictor.prediction_steps,candidate_scene_validation_integrations=validation,maximum_original_replay_error=maximum_replay_error,maximum_candidate_state_error=maximum_validation_error,minimum_actual_native_clearance_m=actual_min,minimum_actual_self_domain_margin_m=self_min,bad_contacts=bad,new_navigation_samples=0,training_updates=0,probabilistic_domain_used=False))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_steps=replay,private_prediction_integrations=None if predictor is None else predictor.prediction_steps,candidate_scene_validation_integrations=validation,new_navigation_samples=0))
