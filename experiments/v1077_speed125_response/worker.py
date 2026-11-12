"""Fixed .125 response, exact canonical scene, signed owner, full own replay."""
import sys,math,signal,fcntl,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths();from resource_policy import apply
RESOURCE=apply()
import numpy as np
from kernel import law,virtual
from fresh import finite_plan
causal=load('v1077_original_packet',R/'experiments/v1024_full_route_execution/causal.py')
def contracts(task):
 assert task in json.loads((C/'TASKS.json').read_text());assert Path(task['output'])==RAW/task['task_id'];assert task['prefix_native']==125 and task['stop_native']==2200 and task['speed']==.125
 assert task['case_id']=='NORTH_SOUTH'and task['seed']==10010002;return Path(task['output'])
def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute(),'ABSOLUTE_TASK_PATH_REQUIRED';task=json.loads(Path(sys.argv[1]).read_text());out=contracts(task);w=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'];assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);end=min(w['absolute_deadline_unix']-30,time.time()+300);v=None;creating=False;inside=False;native=None;f=factory();result=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',response_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,historical_replay_native=0,training_updates=0,scope='Fixed .125 speed/steering response, not a whole route',resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('RESPONSE_OR_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;assert v.count==0 and v.d.time==0.;setup=json.loads((out/'physics/SETUP.json').read_text());expected=json.loads((R/'runs/v858_nav2_verified/v1067/t0_dev_north_south/physics/SETUP.json').read_text())['model_sha256'];assert setup['model_sha256']==expected,'CANONICAL_NS_MODEL_CHANGED'
  import mujoco as mj
  previous=v.adapter;before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};v.adapter=law.Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());assert Path(v.adapter.compute.__func__.__code__.co_filename).resolve()==R/'experiments/v1035_signed_timed_input_source/signed_control.py';native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<2325 and time.time()<end-60,'NATIVE_OR_OWN_REPLAY_RESERVE';inside=True;answer=native(*args);inside=False;return answer
  v.native=counted;v.scan();packet=causal.packet(v,False);xy=np.asarray(v.body()[:2]);request=[task['speed'],task['speed']*math.tan(task['target'])/.6,False];rr=np.vstack([np.tile(request,(125,1)),np.zeros((2200,3))]);plan=finite_plan(setup,packet,None,rr,'FIXED125_RESPONSE_PLUS_COMPLETE2200_STOP');assert plan['passed'],'FIXED_RESPONSE_PREDICTION_REJECTED';dump(out/'PLAN.json',plan);ss=np.asarray(plan['state_path']);maximum=np.zeros(3)
  for i,request in enumerate(rr):
   v.step(*request);b=np.asarray(v.body());angle=b[2]-ss[i+1,2];err=np.array([np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,err);assert np.all(maximum<=[.04,.035,.015]),'ACTUAL_PREDICTOR_LOCAL_TRACKING';assert abs(b[3])<=.13 and abs(b[4])<=.16,'ACTUAL_BODY_CAP'
   if v.count%5==0:v.scan()
  assert np.linalg.norm(v.body()[3:])<=.03;result.update(passed=True,maximum_local_tracking=maximum.tolist(),actual_motion_m=float(np.linalg.norm(np.asarray(v.body()[:2])-xy)),complete_stop_native=2200,target=task['target'],request_speed=.125,actual_control_owner='V1035 signed Adapter via vehicle.step only',initial_model_sha256=setup['model_sha256'])
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  if v is not None:
   result['response_native']=None if inside else v.count
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-10:
    try:
     v.native=native;result['replay_state_initializations']=None;result['own_replay_native']=None;rep=f.replay(v,end,out/'physics');result.update(replay_state_initializations=1,replay=rep,own_replay_native=rep['replay_native']);result['passed']=result['passed']and rep['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('v1077_guarded_result',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
