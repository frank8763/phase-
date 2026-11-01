"""One exact old-control replay, four registered private probes, transaction unit."""
import os,sys,json,gzip,time,signal,math,hashlib,traceback
from pathlib import Path
from types import SimpleNamespace,MethodType
import numpy as np
import mujoco
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from factory import initialize
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from recovery_supervisor import RecoverySupervisor
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from motion_tracker import install_time_gate
base=repo/'runs/v674_dynamic_renewable_backup';out=base/'validation_attempt02';old=repo/'runs/v673_dynamic_joint_forecast/dev40_95000011_joint/paired'
read=lambda p:json.loads(p.read_text())
def dump(name,x):
 (out/name).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item(),allow_nan=False)+'\n')
assert not (out/'PRE_NAV_VALIDATION.json').exists(),'NO_DUPLICATE_VALIDATION'
ledger=read(base/'ROUND_WINDOW.json');assert not ledger['round_closed'] and time.time()+185<ledger['absolute_deadline_unix']
started=time.monotonic();steps=0;extra=0;worst=np.zeros(3);minclear=1e9;selfmargin=1e9;bad=0;records=[];unit={};status='FAILED';error=None;predictor=None
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('VALIDATION_180S')));signal.alarm(180)
try:
 # Load the actual frozen controller for its pure actuator mapping, not an approximation.
 original_native=mujoco.mj_step;reset_steps=[0]
 def count_reset(*a,**kw):reset_steps[0]+=1;return original_native(*a,**kw)
 mujoco.mj_step=count_reset
 context,_=initialize(95000011,out);mujoco.mj_step=original_native
 assert reset_steps[0]==0,'RESET_INTEGRATED_UNACCOUNTED_STEPS'
 inner=context['env'].inner
 controller={k:float(getattr(inner,k))for k in ['wheel_radius','wheel_base','track_width','max_steer','max_wheel_speed','diff_gain']}
 controller['mapping']=inner._ackermann_from_steer_speed.__func__.__module__+'.'+inner._ackermann_from_steer_speed.__func__.__qualname__
 assert 'phase5_wheel_astar_sac_env' in controller['mapping'],'UNEXPECTED_ACTUATOR_MAPPING'
 dump('CONTROLLER_PROVENANCE.json',controller)
 protocol=read(old/'STATIC_PROTOCOL.json');config=read(old/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
 rows=[json.loads(s)for s in(old/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];assert len(rows)==940
 beliefs={r['step']:r for r in map(json.loads,(old/'geometry_memory/motion_estimate.jsonl').read_text().splitlines())}
 trace=read(old/'geometry_memory/trace.json')
 contracts=[]
 for f in sorted((old/'geometry_memory/recovery_contracts').glob('*.gz')):
  with gzip.open(f,'rt')as stream:c=json.load(stream)
  contracts.append(c)
 m=mujoco.MjModel.from_binary_path(str(old/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
 env=SimpleNamespace(model=m,data=d,inner=inner,goal_xy=np.asarray(protocol['goal_xy']))
 predictor=RobotPredictor(env,repo/'runtime/mk-mini',mujoco,original_native)
 ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,n)for n in ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']]
 assert ids==[inner.id_lf_steer,inner.id_rf_steer,inner.id_lr_wheel,inner.id_rr_wheel]
 geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,old/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
 static=dict(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 def field_at(k):
  f=SimpleNamespace(**static);f.pose_values=MethodType(pose_values,f);install_time_gate(f,beliefs[k],'predictive',protocol['known_circles'],protocol['known_rectangles']);return f
 def pose():
  q=d.qpos;return np.r_[q[:2],math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))]
 def clone(source):
  p=mujoco.MjData(predictor.model)
  for name in ['qpos','qvel','act','qacc_warmstart']:getattr(p,name)[:]=getattr(source,name)
  p.time=float(source.time);p.ctrl[:]=0.;mujoco.mj_forward(predictor.model,p);p.qacc_warmstart[:]=source.qacc_warmstart;return p
 def verify_new(manager,real,command):
  global extra
  p=clone(real);p.ctrl[ids]=command
  for _ in range(8):original_native(predictor.model,p);extra+=1
  manager.after_public(p);command,_=manager.start(p,9999)
  for i in range(40):
   p.ctrl[:]=0.;p.ctrl[ids]=command
   for _ in range(8):original_native(predictor.model,p);extra+=1
   done=manager.after_public(p)
   if i<39:command,_=manager.command(p)
  assert done and manager.cache is None
 # Build an original valid retained tail in a private model, then test both transactions.
 manager=ReservedRecovery(predictor,mujoco,ids,out/'private_unit');proposal=np.array([0.,0.,.7,.7]);summary=manager.admit_nominal(d,proposal,field_at(0),beliefs[0],0);assert summary
 p=clone(d);p.ctrl[ids]=proposal
 for _ in range(8):original_native(predictor.model,p);extra+=1
 manager.after_public(p);manager.executing=True
 saved=(manager.cache,manager.cursor,manager.expected)
 blocked=SimpleNamespace(trajectory_values=lambda poses,dt:np.full(len(poses),-.2))
 rejected=manager.try_handover(p,np.zeros(4),blocked,beliefs[0],1,{'unit':True})
 assert rejected is None and manager.cache is saved[0] and manager.cursor==saved[1] and manager.expected is saved[2] and manager.executing
 accepted=manager.try_handover(p,np.zeros(4),field_at(0),beliefs[0],1,{'unit':True});assert accepted
 verify_new(manager,p,np.zeros(4));unit={'failed_transaction_preserved_old_objects':True,'successful_first_and_320_tail_full_states_match':True,'native_ticks_extra':extra}
 for k,row in enumerate(rows):
  if k in [221,241,924,936]:
   c=next(c for c in contracts if c['activation_step']<=k<c['activation_step']+40)
   manager=ReservedRecovery(predictor,mujoco,ids,out/f'checkpoint_{k}')
   manager.cell.mkdir(exist_ok=True)
   manager.cache={key:np.asarray(v)if key in ['initial_qpos','initial_qvel','qpos','qvel','poses','controls','target','prefix_poses']else v for key,v in c.items()};manager.cursor=8*(k-c['activation_step']);manager.executing=True
   manager.check_current_contract(d)
   pathfile=max((f for f in(old/'geometry_memory').glob('planning_*.json')if int(f.stem.split('_')[-1])<c['activation_step']),key=lambda f:int(f.stem.split('_')[-1]))
   path=np.asarray(read(pathfile)['path']);index=trace[c['activation_step']-1]['path_index'];supervisor=RecoverySupervisor(manager.cell);supervisor.remember(path,index,c['activation_step'])
   before=predictor.prediction_steps;returned=supervisor.try_return(env,field_at(k),beliefs[k],manager,predictor,pose(),d.ctrl[ids].copy(),k)
   if returned is not None:verify_new(manager,d,returned[0])
   record={'checkpoint':k,'activation':c['activation_step'],'causal_reference':pathfile.name,'reference_index':index,'accepted':returned is not None,'private_forecast_integrations':predictor.prediction_steps-before,'first_and_tail_verified':returned is not None}
   records.append(record);print('CHECKPOINT',json.dumps(record),flush=True)
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   original_native(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
   b=geometry.actual(m,d);selfmargin=min(selfmargin,float(containment_margin(b,bounds)))
   f=SimpleNamespace(**{**static,'half':(b[2:]-b[:2])/2,'center_local':(b[2:]+b[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3)})
   minclear=min(minclear,float(pose_values(f,[pose()])[0]))
   for contact in d.contact:bad+=catalog.classify(contact,steps,k,float(d.time))['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']
   assert minclear>=.15-1e-8 and selfmargin>=0 and bad==0,'PHYSICAL_REPLAY_ANOMALY'
  worst=np.maximum(worst,[np.max(abs(d.qpos-row['qpos_full'])),np.max(abs(d.qvel-row['qvel_full'])),np.max(abs(d.mocap_pos-row['mocap_pos']))]);assert worst.max()<=1e-8,'OLD_REPLAY_MISMATCH'
  assert predictor.prediction_steps+extra<=60000,'PRIVATE_INTEGRATION_CAP'
 assert len(records)==4 and steps==7520
 status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0)
 result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'logged_control_replay_native_steps':steps,'private_prediction_integrations':(predictor.prediction_steps if predictor else 0)+extra,'maximum_full_qpos_qvel_mocap_errors':worst.tolist(),'minimum_replay_actual_clearance_m':minclear,'minimum_self_domain_margin_m':selfmargin,'bad_contact_records':bad,'unit':unit,'checkpoints':records,'new_navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')}}
 dump('PRE_NAV_VALIDATION.json',result);print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'},indent=2),flush=True)
 assert status=='PASS',error
