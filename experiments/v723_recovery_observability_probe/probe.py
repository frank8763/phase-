"""Fixed two-state full-tail diagnostic. No new navigation, no truth for selection."""
import fcntl,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import cv2
import numpy as np
import mujoco
REPO=Path(os.environ['PHASE_REPO']);OWN=Path(__file__).parent;SOURCE=REPO/'experiments/v721_recursive_unseen_navigation'
sys.path.insert(0,str(REPO/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(SOURCE));sys.path.insert(1,str(REPO/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from renewal_state import decode
from recursive_domain import AXIS,GRID,LOWER
from free_certificate import free_samples
from phase14_sensor_utils import ray_cast_distance
cv2.setNumThreads(1)
root=REPO/'runs/v723_recovery_observability_probe';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text())
def write(name,x):(root/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+240,limit_s=240,round_closed=False,pid=os.getpid());write('ROUND_WINDOW.json',window)
def stop(*_):raise TimeoutError('V723_240S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,stop);signal.alarm(240);replay_steps=validation_steps=0;predictor=None;records=[];status='RUNNING'
try:
 freeze=read(OWN/'SOURCE_FREEZE.json');assert all(hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
 with(REPO/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=REPO/'runs/v721_recursive_unseen_navigation/main01/paired';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);cell=pair/'geometry_memory';rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
  geom=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.array(protocol['footprint_bounds']);static=dict(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),REPO/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;worst=0.;actual_min=float('inf');self_min=float('inf');bad=0
  def pose(q):return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
  def physical(data,step,public):
   global actual_min,self_min,bad
   box=geom.actual(m,data);self_min=min(self_min,float(containment_margin(box,bounds)));field=SimpleNamespace(**{**static,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),.10]])});actual_min=min(actual_min,float(pose_values(field,[pose(data.qpos)])[0]))
   for c in data.contact:bad+=catalog.classify(c,step,public,float(data.time))['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert actual_min>=.15 and self_min>=0 and bad==0,'ACTUAL_SCENE_SAFETY_EXCEPTION'
  def visibility(terminal,possible):
   angles=np.r_[np.arange(32)*2*np.pi/32,np.linspace(-np.deg2rad(35),np.deg2rad(35),15)]+terminal[2]
   sensor=SimpleNamespace(robot_xy=np.asarray(terminal[:2],np.float32),map_min=-5.,map_max=5.,rect_obstacles=np.asarray(protocol['known_rectangles'],np.float32),circle_obstacles=np.asarray(protocol['known_circles'],np.float32))
   rays=[]
   for i,a in enumerate(angles):
    known=ray_cast_distance(sensor,float(a),3.,.08);b=.06 if i<32 else .09
    rays.append([*terminal[:2],math.cos(a),math.sin(a),known,b,.02 if i<32 else .03])
   points=free_samples(np.asarray(rays));covered=np.zeros_like(possible);r=.10
   for pt in points:
    lo=np.maximum(0,np.ceil((pt-r-LOWER)/GRID).astype(int));hi=np.minimum(len(AXIS)-1,np.floor((pt+r-LOWER)/GRID).astype(int))
    if np.any(lo>hi):continue
    x=AXIS[lo[0]:hi[0]+1];y=AXIS[lo[1]:hi[1]+1];covered[lo[0]:hi[0]+1,lo[1]:hi[1]+1]|=(x[:,None]-pt[0])**2+(y[None,:]-pt[1])**2<r*r
   return dict(potential_unknown_visible_cells=int(np.sum(covered&possible)),potential_unknown_visible_area_m2=float(np.sum(covered&possible))*GRID*GRID,known_map_only=True,future_measurement_assumed_for_safety=False)
  def probe(step):
   global validation_steps
   checkpoint=mujoco.MjData(m);mujoco.mj_copyData(checkpoint,m,d);current=pose(d.qpos);state=beliefs[step];domain=decode(state['free_space_renewal']);assert abs(domain.time-d.time)<1e-10
   proposal=np.asarray(rows[step]['ctrl'])[ids];last=d.ctrl[ids];predictor.command_map.assert_first(proposal,last)
   scratch=mujoco.MjData(predictor.model);mujoco.mj_resetData(predictor.model,scratch)
   for name in ['qpos','qvel','act','qacc_warmstart']:getattr(scratch,name)[:]=getattr(d,name)
   scratch.time=d.time;scratch.ctrl[:]=0.;scratch.ctrl[ids]=proposal;mujoco.mj_forward(predictor.model,scratch);scratch.qacc_warmstart[:]=d.qacc_warmstart
   pq=[];pv=[];prefix_margin=float('inf')
   for _ in range(8):
    predictor.native(predictor.model,scratch);predictor.prediction_steps+=1;mujoco.mj_kinematics(predictor.model,scratch);pq.append(scratch.qpos.copy());pv.append(scratch.qvel.copy());prefix_margin=min(prefix_margin,float(containment_margin(predictor.self_geometry.actual(predictor.model,scratch),bounds)))
   pq=np.array(pq);pv=np.array(pv);prefix=np.array([pose(q)for q in pq]);future_possible=cv2.dilate(domain.possible.astype(np.uint8),np.ones((81,81),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=1).astype(bool)
   steers=[-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125];choices=[(None,0.)]+[(st,w)for st in steers for w in[-12.,-8.,-4.,4.,8.]]
   for index,(st,wheel)in enumerate(choices):
    target=np.r_[proposal[:2],0.,0.]if st is None else ReservedRecovery.target(st,wheel);kind='BRAKE_ONLY'if st is None else'FORWARD_BRAKE'if wheel>0 else'REVERSE_BRAKE';brake=240 if wheel>0 else 160
    trajectory=predictor.predict(scratch,target,ids,proposal,horizon=320,brake_after=brake);q=np.vstack([pq,predictor.last_forecast_qpos]);v=np.vstack([pv,predictor.last_forecast_qvel]);controls=np.vstack([np.repeat([proposal],8,axis=0),predictor.command_map.sequence(target,proposal,320,brake)]);allposes=np.vstack([prefix,trajectory]);times=state['time']+np.arange(1,329)*.01
    static_values=pose_values(SimpleNamespace(**static),allposes);dynamic=domain.body_lower(allposes,times);minimum=float(np.minimum(static_values,dynamic).min());signed=float((trajectory[-1,:2]-pq[-1,:2])@np.array([math.cos(prefix[-1,2]),math.sin(prefix[-1,2])]))
    margin=min(prefix_margin,predictor.prediction_self_margin);terminal=float(predictor.terminal_speed);reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if terminal>.025 else'INSUFFICIENT_FORWARD'if kind=='FORWARD_BRAKE'and signed<.02 else'INSUFFICIENT_REVERSE'if kind=='REVERSE_BRAKE'and signed>-.02 else None
    record=dict(checkpoint=step,index=index,kind=kind,target_command=target.tolist(),brake_after_native=brake,minimum_causal_clearance_m=minimum,minimum_static_clearance_m=float(static_values.min()),minimum_dynamic_clearance_m=float(dynamic.min()),minimum_clearance_tick=int(np.argmin(np.minimum(static_values,dynamic)))+1,self_domain_margin_m=margin,terminal_speed_m_s=terminal,signed_displacement_m=signed,goal_progress_m=float(np.linalg.norm(current[:2]-protocol['goal_xy'])-np.linalg.norm(trajectory[-1,:2]-protocol['goal_xy'])),reason=reason,admissible=reason is None,validation_steps=0)
    if reason is None:
     record['visibility_heuristic']=visibility(trajectory[-1],future_possible);mujoco.mj_copyData(d,m,checkpoint);error=0.
     for tick,c in enumerate(controls):
      d.ctrl[:]=0.;d.ctrl[ids]=c;mujoco.mj_step(m,d);validation_steps+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);physical(d,validation_steps,step+tick//8);error=max(error,float(np.max(abs(d.qpos-q[tick]))),float(np.max(abs(d.qvel-v[tick]))));assert error<=1e-8,'FULL_NATIVE_VALIDATION_MISMATCH'
     record.update(validation_steps=328,full_native_state_error=error)
    np.savez_compressed(root/('CHECKPOINT_%03d_CANDIDATE_%02d.npz'%(step,index)),qpos=q,qvel=v,controls=controls,poses=allposes);records.append(record);write('CANDIDATES.json',records)
   mujoco.mj_copyData(d,m,checkpoint)
  for row in rows[:133]:
   if row['step'] in[92,133]:probe(row['step'])
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay_steps+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);physical(d,replay_steps,row['step'])
   worst=max(worst,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert worst<=1e-8,'ORIGINAL_REPLAY_MISMATCH'
  probe(133)
  status='FIXED_TWO_STATE_RECOVERY_DIAGNOSIS_COMPLETE';write('RESULT.json',dict(status=status,candidates=len(records),records=records,original_replay_steps=replay_steps,private_prediction_integrations=predictor.prediction_steps,candidate_scene_validation_integrations=validation_steps,original_replay_full_state_error=worst,minimum_actual_native_clearance_m=actual_min,minimum_actual_self_domain_margin_m=self_min,bad_contacts=bad,new_navigation_tasks=0,training_updates=0,safe_forward_by_checkpoint={str(k):sum(r['admissible']and r['kind']=='FORWARD_BRAKE'for r in records if r['checkpoint']==k)for k in[92,133]},scope='Finite old-state control and geometric visibility potential diagnostic, not a new navigation task or a promise of future observations.'))
except BaseException as error:
 status='STOPPED_EXCEPTION';write('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-begun);write('ROUND_WINDOW.json',window);write('COMPLETION.json',dict(status=status,round_closed=True,original_replay_steps=replay_steps,private_prediction_integrations=0 if predictor is None else predictor.prediction_steps,candidate_scene_validation_integrations=validation_steps,new_navigation_tasks=0));print(json.dumps(dict(status=status,elapsed_s=window['elapsed_s'])))
