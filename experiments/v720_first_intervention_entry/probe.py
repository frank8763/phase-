"""Exact old prefix, then fixed three full native candidates. Not navigation."""
import fcntl,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
REPO=Path(os.environ['PHASE_REPO']);OWN=Path(__file__).parent;SOURCE=REPO/'experiments/v712_joint_field_continuation'
sys.path.insert(0,str(REPO/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(SOURCE));sys.path.insert(1,str(REPO/'experiments/v718_recursive_unseen_reachability'))
from recursive_domain import RecursiveDomain
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
root=REPO/'runs/v720_first_intervention_entry';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def write(name,x):(root/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+180,limit_s=180,round_closed=False,pid=os.getpid());write('ROUND_WINDOW.json',window)
def stop(*_):raise TimeoutError('V720_180S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,stop);signal.alarm(180);records=[];replayed=0;validation=0;predictor=None;status='RUNNING'
try:
 freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
 with (REPO/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=REPO/'runs/v712_joint_field_continuation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);rows=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
  model=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));data=mujoco.MjData(model);data.qpos[:]=protocol['start_qpos'];motion.apply(model,data);mujoco.mj_forward(model,data)
  geometry=SelfGeometry(model,mujoco);catalog=GeometryCatalog(model,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.array(protocol['footprint_bounds']);static=dict(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  def pose(q):return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
  actual_min=float('inf');self_min=float('inf');bad=0;worst=0.
  def physical(d,step,public):
   global actual_min,self_min,bad
   realbounds=geometry.actual(model,d);self_min=min(self_min,float(containment_margin(realbounds,bounds)))
   f=SimpleNamespace(**{**static,'half':(realbounds[2:]-realbounds[:2])/2,'center_local':(realbounds[2:]+realbounds[:2])/2,'circles':np.array([*protocol['known_circles'],[*motion.xy(d.time),.10]])});actual_min=min(actual_min,float(pose_values(f,[pose(d.qpos)])[0]))
   for c in d.contact:bad+=catalog.classify(c,step,public,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert actual_min>=.15 and self_min>=0 and bad==0,'PHYSICAL_STATE_SAFETY_EXCEPTION'
  for row in rows[:64]:
   data.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(model,data);replayed+=1;motion.apply(model,data);mujoco.mj_kinematics(model,data);mujoco.mj_collision(model,data);physical(data,replayed,row['step'])
   worst=max(worst,float(np.max(abs(data.qpos-row['qpos_full']))),float(np.max(abs(data.qvel-row['qvel_full']))),float(np.max(abs(data.mocap_pos-row['mocap_pos']))));assert worst<=1e-8,'ORIGINAL_PREFIX_STATE_MISMATCH'
  checkpoint=mujoco.MjData(model);mujoco.mj_copyData(checkpoint,model,data)
  archive=np.load(REPO/'runs/v718_recursive_unseen_reachability/DOMAIN_064.npz');domain=RecursiveDomain(archive['origin']);domain.possible=archive['possible'];domain.distance=archive['distance'];domain.time=float(archive['time']);assert abs(domain.time-data.time)<1e-10
  predictor=RobotPredictor(SimpleNamespace(model=model,data=data),REPO/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;last=data.ctrl[ids].copy();current=pose(data.qpos)
  for wheel in [4.,8.,12.]:
   command=np.array([0.,0.,wheel,wheel]);trajectory=predictor.predict(checkpoint,command,ids,last,horizon=328,brake_after=168);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();controls=predictor.command_map.sequence(command,last,328,168)
   f=SimpleNamespace(**static);minimum=float(np.min(np.minimum(pose_values(f,trajectory),domain.body_lower(trajectory,domain.time+np.arange(1,329)*.01))));signed=float((trajectory[-1,:2]-current[:2])@np.array([math.cos(current[2]),math.sin(current[2])]))
   canonical=all(predictor.command_map.legal(c)for c in controls)and np.all(abs(np.diff(np.vstack([last,controls]),axis=0))<=predictor.command_map.rate+1e-12)
   passed=minimum>=.155 and predictor.prediction_self_margin>=.002 and predictor.terminal_speed<=.025 and signed>=.10 and canonical
   mujoco.mj_copyData(data,model,checkpoint);state_error=0.;start_count=validation
   for tick,c in enumerate(controls):
    data.ctrl[:]=0.;data.ctrl[ids]=c;mujoco.mj_step(model,data);validation+=1;motion.apply(model,data);mujoco.mj_kinematics(model,data);mujoco.mj_collision(model,data);physical(data,validation,64+tick//8)
    state_error=max(state_error,float(np.max(abs(data.qpos-q[tick]))),float(np.max(abs(data.qvel-v[tick]))));assert state_error<=1e-8,'PRIVATE_SCENE_FULL_NATIVE_STATE_MISMATCH'
   records.append(dict(target_command=command.tolist(),horizon_native=328,brake_after_native=168,minimum_causal_full_body_clearance_m=minimum,self_domain_margin_m=float(predictor.prediction_self_margin),terminal_speed_m_s=float(predictor.terminal_speed),signed_forward_displacement_m=signed,canonical_controls=bool(canonical),full_native_state_error=state_error,physical_validation_steps=validation-start_count,admissible=bool(passed)))
   np.savez_compressed(root/('CANDIDATE_WHEEL_%02d.npz'%wheel),qpos=q,qvel=v,controls=controls,poses=trajectory);write('CANDIDATES.json',records)
  status='FIRST_INTERVENTION_NATIVE_CANDIDATE_VALIDATED'if any(r['admissible']for r in records)else'FIRST_INTERVENTION_NO_VALIDATED_FORWARD_CANDIDATE'
  write('RESULT.json',dict(status=status,checkpoint=64,records=records,original_prefix_full_state_error=worst,minimum_actual_native_clearance_m=actual_min,minimum_actual_self_domain_margin_m=self_min,bad_contacts=bad,original_prefix_replay_native=replayed,private_prediction_integrations=predictor.prediction_steps,candidate_state_validation_integrations=validation,new_navigation_tasks=0,training_updates=0,physical_candidate_admissible=status=='FIRST_INTERVENTION_NATIVE_CANDIDATE_VALIDATED',source_original_failed_v712_preserved=True))
except BaseException as error:
 status='STOPPED_EXCEPTION';write('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-start);write('ROUND_WINDOW.json',window);write('COMPLETION.json',dict(status=status,round_closed=True,original_prefix_replay_native=replayed,private_prediction_integrations=0 if predictor is None else predictor.prediction_steps,candidate_state_validation_integrations=validation,new_navigation_tasks=0));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))
