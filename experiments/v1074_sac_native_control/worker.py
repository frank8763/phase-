"""Real SAC prefix125 + unchanged2200 stop, one actuator owner and own replay."""
import sys,json,time,signal,traceback,fcntl,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths();from resource_policy import apply
RESOURCE=apply()
import numpy as np
from measurements import NativeMeasurements
from integration import ShieldedSAC
from observation import assemble
from kernel import law,virtual
causal=load('v1074_causal_packet',R/'experiments/v1024_full_route_execution/causal.py');corruption=load('v1074_original_noise',R/'experiments/v733_early_low_translation_scan/sensor_model.py');primary=load('v1074_original_primary',R/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs/phase14_sensor_utils.py')
def main():
 task=json.loads(Path(sys.argv[1]).read_text());window=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task in json.loads((C/'TASKS.json').read_text())and task['task_id']in approval['allowed_task_ids'];assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());end=min(window['absolute_deadline_unix']-30,time.time()+300);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=Path(task['output']);assert out==RAW/task['task_id'];out.mkdir(parents=True,exist_ok=False);v=None;reader=None;creating=False;inside=False;f=factory();result=dict(passed=False,vehicle_initializations=0,replay_state_initializations=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0,historical_replay_native=0,training_updates=0,sac_proposed=0,sac_admitted=0,sac_executed_native=0,scope='SAC controller component, not a route or goal trial',resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('SAC_COMPONENT_OR_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;assert v.count==0 and v.d.time==0.;setup=json.loads((out/'physics/SETUP.json').read_text());expected=json.loads((R/'records/nav2_v1073_20261112/FINAL_SUMMARY.json').read_text())['sensor_success']['model_sha256'];assert setup['model_sha256']==expected,'CANONICAL_MODEL_CHANGED'
  import mujoco as mj
  old=v.adapter;before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};v.adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=old.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());assert Path(v.adapter.compute.__func__.__code__.co_filename).resolve()==R/'experiments/v1035_signed_timed_input_source/signed_control.py';native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<2325,'NATIVE_BUDGET';assert time.time()<end-60,'OWN_REPLAY_WALL_RESERVE';inside=True;answer=native(*args);inside=False;return answer
  v.native=counted;scan=v.scan();packet=causal.packet(v,False);goal=np.asarray(task['goal_xy']);xy=np.asarray(v.body()[:2]);waypoint=xy+.9*(goal-xy)/np.linalg.norm(goal-xy)
  def measured32(proxy,tick):
   raw=primary.get_lidar_features(proxy,num_rays=32,max_range=3.);values=corruption.corrupt(raw,v.seed,v.noise['lidar_call']+tick//5,'lidar',3.);assert tick==0 and np.max(abs(values*3-np.asarray(scan['ranges'])))<=1e-6,'PRIMARY_MEASUREMENT_CHANGED';return values
  reader=NativeMeasurements(v.m,v.d,setup['known'],goal,waypoint,primary32_reader=measured32);frame=reader.read(v);shield=ShieldedSAC();obs=assemble(frame['blocks'],shield.policy.base,v.count,frame['native_tick']);proposal=shield.propose(setup,packet,None,frame['blocks'],frame['native_tick'],[.08,0.,False],prefix_native=125);result['sac_proposed']=1;result['sac_admitted']=int(proposal['admitted']);assert proposal['admitted'],'FIXED_SAC_PREFIX_REJECTED';plan=proposal['certificate'];rr=np.asarray(plan['planned_body_requests']);ss=np.asarray(plan['state_path']);assert len(rr)==2325 and np.array_equal(rr[-2200:],np.zeros((2200,3)));assert abs(rr[:125,1]).max()>1e-5,'SAC_ACTION_HAS_NO_EFFECT';dump(out/'PLAN.json',plan);dump(out/'POLICY.json',{k:x for k,x in proposal.items()if k!='certificate'});np.savez_compressed(out/'SAC_OBSERVATION.npz',observation=obs,depth_image=frame['depth_image'],**frame['blocks']);reader.close();reader=None;maximum=np.zeros(3)
  for i,request in enumerate(rr):
   v.step(*request);b=np.asarray(v.body());angle=b[2]-ss[i+1,2];error=np.array([np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,error);assert np.all(maximum<=[.04,.035,.015]),'NATIVE_LOCAL_TRACKING_FAILED';assert abs(b[3])<=.13 and abs(b[4])<=.16,'ACTUAL_BODY_CAP'
   if i<125:result['sac_executed_native']+=1
   if v.count%5==0:v.scan()
  assert np.linalg.norm(v.body()[3:])<=.03,'COMPLETE_ACTUAL_STOP_REQUIRED';result.update(passed=True,maximum_local_tracking=maximum.tolist(),actual_motion_m=float(np.linalg.norm(np.asarray(v.body()[:2])-xy)),complete_stop_native=2200,actual_control_owner='V1035 signed Adapter via vehicle.step only',policy_sha256=proposal['proposal']['policy_sha256'],complete_prefix_source='SAC combined action, original goal-direction nominal',initial_model_sha256=setup['model_sha256'])
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  if reader is not None:
   try:reader.close()
   except BaseException as e:result.update(passed=False,renderer_error=repr(e))
  if v is not None:
   result['navigation_native']=None if inside else v.count
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-10:
    try:v.native=native;result['replay_state_initializations']=None;result['own_replay_native']=None;rep=f.replay(v,end,out/'physics');result['replay_state_initializations']=1;result['replay']=rep;result['own_replay_native']=rep['replay_native'];result['passed']=result['passed']and rep['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('v1074_guarded_result',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
