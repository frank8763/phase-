"""Exact logged-control replay + fixed actuator-grid diagnostic; no new navigation."""
import os,sys,json,math,time,signal,hashlib
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v669_dynamic_reserved_recovery'
sys.path.insert(0,str(src));sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor,SELF_DOMAIN
from motion_tracker import install_time_gate
root=repo/'runs/v667_dynamic_first_hit/dev36_95000011_firsthit/paired';out=repo/'runs/v669_dynamic_reserved_recovery';out.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text())
def dump(name,d): (out/name).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PROBE_120S')));signal.alarm(120)
round_ledger=read(repo/'runs/v666_dynamic_dense_navigation/ROUND_WINDOW.json');assert time.time()+125<round_ledger['absolute_deadline_unix']
protocol=read(root/'STATIC_PROTOCOL.json');config=read(root/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
rows=[json.loads(s)for s in(root/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
beliefs={r['step']:r for r in map(json.loads,(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())}
assert len(rows)==209
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
from reserved_recovery import ReservedRecovery
prefix_errors=[];contract_replay_checks=[]
def probe(k):
 field=SimpleNamespace(**static);field.pose_values=MethodType(pose_values,field);install_time_gate(field,beliefs[k],'predictive',protocol['known_circles'],protocol['known_rectangles'])
 proposal=np.asarray(rows[k]['ctrl'])[ids] if k<len(rows) else d.ctrl[ids].copy()
 if k==len(rows):proposal[2:]=np.clip(0.,proposal[2:]-.70,proposal[2:]+.70)
 manager=ReservedRecovery(predictor,mujoco,ids,out/'private_contract_checks')
 summary=manager.admit_nominal(d,proposal,field,beliefs[k],k)
 if k<len(rows):
  qerr=float(np.max(abs(manager.last_prefix_qpos-rows[k]['qpos_full'])));verr=float(np.max(abs(manager.last_prefix_qvel-rows[k]['qvel_full'])))
  assert max(qerr,verr)<=1e-8,'PRIVATE_NOMINAL_FIRST_STEP_MISMATCH'
 else:qerr=verr=None
 prefix_errors.append({'checkpoint':k,'maximum_qpos_error':qerr,'maximum_qvel_error':verr})
 coverage_times=np.linspace(0,3.28,165)
 from motion_tracker import future_boxes
 lo,hi=future_boxes(beliefs[k],coverage_times)
 true=np.asarray(config['anchor_xy'])+np.sin((beliefs[k]['time']+coverage_times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
 excess=float(np.maximum(lo-true,true-hi).max());assert excess<=1e-7
 record={'checkpoint':k,'ordinary_proposal_after_step_reservable':summary is not None,'summary':summary,'maximum_future_328_center_box_excess_m':excess}
 records.append(record)
 if summary is not None:
  pm=predictor.model;private=mujoco.MjData(pm);source=manager.scratch
  for name in ['qpos','qvel','act','qacc_warmstart']:getattr(private,name)[:]=getattr(source,name)
  private.time=float(source.time);private.ctrl[:]=0.;mujoco.mj_forward(pm,private);private.qacc_warmstart[:]=source.qacc_warmstart
  command,gate=manager.start(private,k+1)
  for public_step in range(40):
   private.ctrl[:]=0.;private.ctrl[ids]=command
   for _ in range(8):mujoco.mj_step(pm,private);predictor.prediction_steps+=1
   complete=manager.after_public(private)
   if public_step<39:command,gate=manager.command(private)
  assert complete and not manager.executing
  contract_replay_checks.append({'checkpoint':k,'private_executed_native_ticks':320,'all_public_full_states_match':True,'completed':True})
 dump('PRE_NAV_DIAGNOSTIC_PROGRESS.json',{'records':records,'prefix_errors':prefix_errors,'contract_checks':contract_replay_checks})
 print('CHECKPOINT',k,'reservable',summary is not None,'prefix_errors',[qerr,verr],flush=True)

try:
 for i,row in enumerate(rows):
  if i in [160,192]:probe(i)
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
 probe(209);status='COMPLETE_FIXED_GRID'
except BaseException as e:status='FAILED_OR_INTERRUPTED';error={'type':type(e).__name__,'message':str(e)}
finally:
 signal.alarm(0)
 output={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'replay_native_steps':steps,'private_prediction_integrations':predictor.prediction_steps,'checkpoint_count':len(records),'prefix_errors':prefix_errors,'private_contract_replay_checks':contract_replay_checks,'new_navigation_tasks':0,'worst_full_qpos_qvel_mocap_errors':[worst_q,worst_v,worst_mocap],'minimum_replay_actual_native_clearance_m':minclear,'minimum_replay_self_domain_margin_m':selfmargin,'obstacle_unknown_contact_records':badcontacts,'original_round_deadline_unix':round_ledger['absolute_deadline_unix'],'records':records,'scope':'reserved-recovery logic at3locked causal checkpoints; exact logged prefix and private-tail execution, no new navigation'}
 dump('PRE_NAV_DIAGNOSTIC.json',output);print(json.dumps({k:v for k,v in output.items()if k!='records'},indent=2),flush=True)
