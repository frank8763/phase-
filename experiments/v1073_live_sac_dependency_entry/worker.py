"""Exactly one archived-scene sensor reconstruction; native integration forbidden."""
import sys,os,json,time,hashlib,fcntl,signal,traceback,gzip,math
from pathlib import Path
from types import SimpleNamespace
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1073_live_sac_dependency_entry';sys.path[:0]=[str(R/'experiments/v1067_causal_replan_brake_reserve')]
from resource_policy import apply
RESOURCE=apply();sys.path[:0]=[str(C),str(R/'experiments/v1070_frozen_sac_proposals'),str(R/'runtime/mk-mini'),str(R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs')]
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
w=json.loads((O/'ROUND_WINDOW.json').read_text());assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic'];assert json.loads((O/'APPROVAL.json').read_text())['archived_sensor_model_authorized'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
result=dict(passed=False,model_initializations=0,archived_state_restorations=0,navigation_native=0,replay_native=0,private_mujoco_native=0,training_updates=0,real_vehicle_steps=0,resource_policy=RESOURCE);reader=None;creating=False
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('SENSOR_COMPONENT_120S')));signal.setitimer(signal.ITIMER_REAL,min(120,w['absolute_deadline_unix']-time.time()))
try:
 import mujoco as mj
 def forbidden(*args,**kwargs):raise AssertionError('NATIVE_INTEGRATION_FORBIDDEN_SENSOR_COMPONENT')
 mj.mj_step=mj.mj_step1=mj.mj_step2=forbidden
 raw=R/'runs/v858_nav2_verified/v1067/t0_dev_west_east/physics';setup=json.loads((raw/'SETUP.json').read_text());assert sha(raw/'scene_model.mjb')==setup['model_sha256'];creating=True;m=mj.MjModel.from_binary_path(str(raw/'scene_model.mjb'));result['model_initializations']=1;creating=False;d=mj.MjData(m);state=np.load(raw/'INITIAL_STATE.npz')['state'];assert len(state)==mj.mj_stateSize(m,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_setState(m,d,state,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_forward(m,d);result['archived_state_restorations']=1;assert d.time==0.;before={k:np.asarray(getattr(d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
 meta=json.loads((R/'runs/v1067_causal_replan_brake_reserve_preparation/WEST_EAST_T0_METADATA.json').read_text());packet=meta['packet'];packet['body_measured_at']=time.monotonic()
 def body():
  q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));return [q[0],q[1],yaw,d.qvel[0]*math.cos(yaw)+d.qvel[1]*math.sin(yaw),d.qvel[5]]
 assert np.max(abs(np.asarray(body())-packet['body']))<=1e-8
 with gzip.open(raw/'SENSORS.json.gz','rt')as f:archived_scan=json.load(f)[-1]
 from measurements import NativeMeasurements,load
 corruption=load('v1071_original_sensor_corruption',R/'experiments/v733_early_low_translation_scan/sensor_model.py');original_sensor=load('v1071_original_primary_lidar',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py');primary_comparison={}
 def primary32(proxy,tick):
  values=original_sensor.get_lidar_features(proxy,num_rays=32,max_range=3.);normalized=corruption.corrupt(values,setup['seed'],setup['noise']['lidar_call']+tick//5,'lidar',3.);primary_comparison['raw_error']=float(np.max(abs(values-np.asarray(archived_scan['raw_lidar']))));primary_comparison['corrupted_error']=float(np.max(abs(normalized*3-np.asarray(archived_scan['ranges']))));assert primary_comparison['raw_error']<=1e-6 and primary_comparison['corrupted_error']<=1e-6,'PRIMARY_SENSOR_GEOMETRY_OR_NOISE_CHANGED';return normalized
 goal=np.asarray(setup['case']['goal_xy']);xy=np.asarray(body()[:2]);direction=goal-xy;waypoint=xy+.9*direction/np.linalg.norm(direction);v=SimpleNamespace(m=m,d=d,count=0,body=body,adapter=SimpleNamespace(last=np.asarray(packet['controller_memory']['last_ctrl']),integral=packet['controller_memory']['integral']));reader=NativeMeasurements(m,d,setup['known'],goal,waypoint,primary32_reader=primary32);frame=reader.read(v)
 from observation import assemble
 from integration import ShieldedSAC
 shield=ShieldedSAC();obs=assemble(frame['blocks'],shield.policy.base,0,frame['native_tick']);proposal=shield.propose(setup,packet,None,frame['blocks'],0,[.08,0.,False]);assert obs.shape==(186,)and np.isfinite(obs).all();assert d.time==0 and all(np.array_equal(x,np.asarray(getattr(d,k)))for k,x in before.items())
 np.savez_compressed(O/'REAL_SENSOR_FRAME.npz',depth_image=frame['depth_image'],policy_observation=obs,**frame['blocks']);(O/'POLICY_PROPOSAL.json').write_text(json.dumps({k:v for k,v in proposal.items()if k!='certificate'},indent=2)+'\n')
 result.update(passed=True,status='ARCHIVED_REAL_SENSOR_TO_SAC_AND_SAFETY_GATE_CONNECTED',camera_names=[mj.mj_id2name(m,mj.mjtObj.mjOBJ_CAMERA,i)for i in range(m.ncam)],legacy_camera_id=mj.mj_name2id(m,mj.mjtObj.mjOBJ_CAMERA,'d435i_depth'),bound_camera_id=mj.mj_name2id(m,mj.mjtObj.mjOBJ_CAMERA,'d435i_depth_camera'),primary32_parity=primary_comparison,depth_min_m=float(frame['depth_image'].min()),depth_max_m=float(frame['depth_image'].max()),depth24_variance=float(np.var(frame['blocks']['phase5_base'][-24:])),policy_observation_dimensions=len(obs),sac_admitted=proposal['admitted'],sac_executed=0,goal_reached=False,physical_state_unchanged=True,policy_sha256=proposal['proposal']['policy_sha256'],model_sha256=setup['model_sha256'],waypoint_scope='Declared public goal-direction test waypoint, not a navigation run',richer_observation_contract=True,current_worker_integration_verified=False)
except BaseException as e:
 result.update(error=repr(e),traceback=traceback.format_exc())
 if creating:result['model_initializations']=None
finally:
 if reader is not None:
  try:reader.close()
  except BaseException as e:result['renderer_close_error']=repr(e);result['passed']=False
 signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
sys.exit(0 if result['passed']else 1)
