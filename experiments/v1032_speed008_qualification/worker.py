"""Actual model creation/integration only through run_phase, fixed three tasks."""
import fcntl,hashlib,importlib.util,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1032_speed008_qualification'
sys.path[:0]=[str(C),str(R/'experiments/v1027_timed_speed_source'),str(R/'experiments/v1024_full_route_execution')]
from whole_input import Predictor,PARAMETERS,initial
from geometry_model import ref,REQUIRED
from causal import packet
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
execute=load('v1032_exact_executor',C/'execute.py').execute
def authorize(task,receipt):
 a=json.loads((O/'APPROVAL.json').read_text());w=json.loads((O/'ROUND_WINDOW.json').read_text());f=json.loads((C/'SOURCE_FREEZE.json').read_text())
 assert a['models_authorized'] is True and not (O/'COMPLETION.json').exists(),'WINDOW_CLOSED'
 assert receipt==dict(task_id=task['task_id'],window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json')),'WRONG_AUTHORIZATION'
 assert task in json.loads((C/'TASKS.json').read_text()) and task['dynamic'] is False,'UNREGISTERED_TASK'
 assert all(sha(R/p)==v for p,v in f['files'].items()),'FROZEN_SOURCE_CHANGED'
 assert Path(task['output']).resolve().is_relative_to(R/'runs/v858_nav2_verified/v1032') and not Path(task['output']).exists(),'OUTPUT_NOT_NEW'
 assert time.time()<w['absolute_deadline_unix']-360,'INSUFFICIENT_MODEL_AND_REPLAY_RESERVE'
 return min(w['absolute_deadline_unix']-30,time.time()+300)
def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());end=authorize(task,receipt)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 out=Path(task['output']);out.mkdir(parents=True);v=None;creating=False;in_step=False;result=dict(passed=False,model_initializations=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0)
 def abort(*_):raise InterruptedError('ROOT_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,abort);signal.signal(signal.SIGTERM,abort);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  factory=load('v1032_original_factory',R/'experiments/v1020_terminal_two_route_development/physical.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;result['model_initializations']=1
  assert v.count==0 and v.d.time==0. and v.actor is None,'FRESH_STATIC_T0_REQUIRED'
  import mujoco as mj
  law=load('v1032_original_allocator',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py');before={k:np.asarray(getattr(v.d,k)).copy() for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};old=v.adapter
  adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);adapter.virtual_rate=.6;adapter.last=old.last.copy();adapter.integral=float(old.integral);v.adapter=adapter
  assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items()),'ADAPTER_WROTE_PHYSICAL_STATE'
  setup=json.loads((out/'physics/SETUP.json').read_text());p=packet(v,False);frozen=json.loads((C/('PLAN_'+task['task_id']+'.json')).read_text());predictor=Predictor(setup,initial(p),PARAMETERS)
  states=[predictor.state.copy()];controls=[]
  for request in frozen['planned_body_requests']:s,u=predictor.step(*request);states.append(s);controls.append(u)
  states=np.asarray(states);controls=np.asarray(controls)
  assert np.max(abs(states-np.asarray(frozen['state_path'])))<=1e-8,'FRESH_PREDICTION_DIFFERS'
  a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);assert a.min()>=REQUIRED,'SOURCE_STATIC_GEOMETRY'
  plan=dict(frozen,state_path=states.tolist(),predicted_actuator_controls=controls.tolist(),minimum_static_raw_m=float(a.min()));dump(out/'ACTUAL_INITIAL_PACKET.json',p);dump(out/'REGENERATED_PROFILE.json',plan)
  native=v.native
  def counted(*args):
   nonlocal in_step
   in_step=True;answer=native(*args);in_step=False;return answer
  v.native=counted;result['response']=execute(v,plan,end);result.update(passed=True,status='FIXED_RESPONSE_AND_COMPLETE_STOP')
 except BaseException as e:result.update(passed=False,status='FAILED',error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['model_initializations']=None
  result['navigation_native']=None if in_step or (v is None and creating) else v.count if v is not None else 0
  if v is not None:
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not in_step and result.get('evidence_saved') and time.time()<end-30:
    try:
     result['own_replay_native']=None;replay=factory.replay(v,end,out/'physics');result['replay']=replay;result['own_replay_native']=replay['replay_native'];result['passed']=result['passed'] and replay['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time());dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['physical','traceback']}),flush=True)
 return 0 if result['passed'] else 1
if __name__=='__main__':sys.exit(main())
