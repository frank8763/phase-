"""Exact logged-control replay + fixed actuator-grid diagnostic; no new navigation."""
import os,sys,json,math,time,signal,hashlib
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v670_dynamic_empty_samples'
sys.path.insert(0,str(src));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor,SELF_DOMAIN
from motion_tracker import install_time_gate
sys.path.insert(0,str(repo/'experiments/v671_dynamic_consistency_diagnosis'))
from union_belief import clearance as union_clearance
with __import__('gzip').open(repo/'runs/v671_dynamic_consistency_diagnosis/validated_union_states.jsonl.gz','rt')as stream:
 union_records={s['step']:s for s in map(json.loads,stream)if s['dataset'].startswith('v670_')}
root=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired';out=repo/'runs/v671_dynamic_consistency_diagnosis/private_probe';out.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text())
def dump(name,d): (out/name).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PROBE_175S')));signal.alarm(175)
round_ledger=read(repo/'runs/v671_dynamic_consistency_diagnosis/ROUND_WINDOW.json');assert time.time()+180<round_ledger['absolute_deadline_unix']
protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
rows=[json.loads(s)for s in(root/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
beliefs={r['step']:r for r in map(json.loads,(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())}
assert len(rows)==843
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml')
env=SimpleNamespace(model=m,data=d);predictor=RobotPredictor(env,repo/'runtime/mk-mini',mujoco,mujoco.mj_step)
ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,n)for n in ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']]
assert min(ids)>=0
records=[];steps=0;worst_q=worst_v=worst_mocap=0.;minclear=float('inf');selfmargin=float('inf');badcontacts=0;status='RUNNING';error=None
bounds=np.asarray(protocol['footprint_bounds']);half=(bounds[2:]-bounds[:2])/2;center=(bounds[2:]+bounds[:2])/2
static=dict(half=half,center_local=center,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
def pose():
 q=d.qpos;return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
def target(steer,wheel):
 if abs(steer)<1e-9:return np.asarray([0.,0.,wheel,wheel])
 radius=.60/math.tan(abs(steer));inner=math.atan2(.60,radius-.54/2);outer=math.atan2(.60,radius+.54/2)
 return np.asarray([inner,outer,wheel,wheel]if steer>0 else[-outer,-inner,wheel,wheel])
def probe(k):
 field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,beliefs[k],'predictive',protocol['known_circles'],protocol['known_rectangles'])
 current=pose();last=d.ctrl[ids].copy();begin=time.monotonic()
 for steer in [-.42722137342572125,-.2136106867128606,0.,.2136106867128606,.42722137342572125]:
  for wheel in [-12.,-6.,0.,6.,12.]:
   for brake_after in [80]:
    horizon=max(240,brake_after+160);command=target(steer,wheel);trajectory=predictor.predict(d,command,ids,last,horizon=horizon,brake_after=brake_after)
    minimum=float(np.min(field.trajectory_values(trajectory,.01)));terminal=predictor.terminal_speed
    union_minimum=float(np.min(np.minimum(pose_values(field,trajectory),union_clearance(field,trajectory,union_records[k]['cells'],np.arange(1,len(trajectory)+1)*.01))))
    goal=np.asarray(protocol['goal_xy']);goal_progress=float(np.linalg.norm(current[:2]-goal)-np.linalg.norm(trajectory[-1,:2]-goal))
    progress=float((trajectory[-1,:2]-current[:2])@np.asarray([math.cos(current[2]),math.sin(current[2])]))
    records.append({'checkpoint':k,'steer':steer,'symmetric_rear_target':wheel,'brake_after_native_ticks':brake_after,'horizon_native_ticks':horizon,'minimum_causal_predicted_clearance_m':minimum,'self_domain_margin_m':predictor.prediction_self_margin,'terminal_speed_m_s':terminal,'signed_forward_displacement_m':progress,'terminal_pose':trajectory[-1].tolist(),'admissible_015':bool(minimum>=.15 and predictor.prediction_self_margin>=.002 and terminal<=.025),'admissible_0155':bool(minimum>=.155 and predictor.prediction_self_margin>=.002 and terminal<=.025),'union_minimum_causal_clearance_m':union_minimum,'goal_progress_m':goal_progress,'admissible_union_0155':bool(union_minimum>=.155 and predictor.prediction_self_margin>=.002 and terminal<=.025),'actual_future_used_for_selection':False})
 dump('CANDIDATE_RESULTS.json',{'status':'PARTIAL','records':records,'simulation_navigation_tasks':0})
 print('CHECKPOINT',k,'candidates',len([r for r in records if r['checkpoint']==k]),'safe',sum(r['admissible_015']for r in records if r['checkpoint']==k),'wall_s',time.monotonic()-begin,flush=True)
try:
 for i,row in enumerate(rows):
  if i>650:break
  if i in [48,192,300,650]:probe(i)
  if i==650:break
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
   actual=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(actual,bounds)))
   actualfield=SimpleNamespace(**{**static,'half':(actual[2:]-actual[:2])/2,'center_local':(actual[2:]+actual[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
   clearance=float(pose_values(actualfield,[pose()])[0]);minclear=min(minclear,clearance)
   for c in d.contact:badcontacts+=catalog.classify(c,steps,i,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert selfmargin>=0 and clearance>=.15-1e-8 and badcontacts==0,'PHYSICAL_REPLAY_SAFETY_ANOMALY'
  worst_q=max(worst_q,float(np.max(abs(d.qpos-row['qpos_full']))));worst_v=max(worst_v,float(np.max(abs(d.qvel-row['qvel_full']))));worst_mocap=max(worst_mocap,float(np.max(abs(d.mocap_pos-row['mocap_pos']))))
  assert max(worst_q,worst_v,worst_mocap)<=1e-8,'REPLAY_STATE_MISMATCH'
 status='COMPLETE_FIXED_GRID'
except BaseException as e:status='FAILED_OR_INTERRUPTED';error={'type':type(e).__name__,'message':str(e)}
finally:
 signal.alarm(0)
 output={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps,'candidate_count':len(records),'new_navigation_tasks':0,'worst_full_qpos_qvel_mocap_errors':[worst_q,worst_v,worst_mocap],'minimum_replay_actual_native_clearance_m':minclear,'minimum_replay_self_domain_margin_m':selfmargin,'obstacle_unknown_contact_records':badcontacts,'round_deadline_unix':round_ledger['absolute_deadline_unix'],'records':records,'scope':'actuator-grid diagnostic at3causal checkpoints, no executed navigation alternative'}
 dump('COMPLETION.json',output);print(json.dumps({k:v for k,v in output.items()if k!='records'},indent=2),flush=True)
