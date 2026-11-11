"""One historical exact replay + fixed causal observation approach, run_phase only."""
import fcntl,hashlib,importlib.util,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1039_causal_approach';H=R/'runs/v858_nav2_verified/v1024/dynamic_we'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
causal=load('v1039_original_causal_sensor',R/'experiments/v1024_full_route_execution/causal.py');fast=load('v1039_exact_original_periodic',R/'experiments/v1029_declared_course_source/fast_periodic.py');owner_module=load('v1039_exact_original_native_owner',R/'experiments/v1030_declared_course_dynamic/owner.py');component=load('v1039_exact_component_plan',C/'component_plan.py')
class Evidence(causal.Evidence):
 def __init__(self,known):super().__init__(known);self.periodic=fast.PeriodicSupport()

def authorized(task,receipt):
 a=json.loads((O/'APPROVAL.json').read_text());w=json.loads((O/'ROUND_WINDOW.json').read_text());f=json.loads((C/'SOURCE_FREEZE.json').read_text());assert a['models_authorized']is True and not(O/'COMPLETION.json').exists(),'CLOSED_WINDOW'
 assert receipt==dict(window_sha256=sha(O/'ROUND_WINDOW.json'),source_sha256=sha(C/'SOURCE_FREEZE.json')),'AUTHORITY_BINDING'
 assert task==json.loads((C/'TASK.json').read_text())and task['historical_native']==16740 and task['new_component_native']==6900,'TASK_CHANGED'
 assert all(sha(R/p)==h for p,h in f['files'].items()),'SOURCE_CHANGED'
 assert Path(task['output']).resolve().is_relative_to(R/'runs/v858_nav2_verified/v1039')and not Path(task['output']).exists(),'OUTPUT_NOT_NEW'
 assert time.time()<w['absolute_deadline_unix']-1200,'ROOT_RESERVE'
 return min(w['absolute_deadline_unix']-30,time.time()+900)

def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());end=authorized(task,receipt);lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 out=Path(task['output']);out.mkdir(parents=True);v=None;creating=False;in_native=False;evidence=None;owner=None;result=dict(passed=False,model_initializations=0,historical_replay_native=0,new_component_native=0,navigation_native=0,own_replay_native=0,private_mujoco_native=0,original_goal_arrival_claim=False)
 def abort(*_):raise InterruptedError('ABSOLUTE_OR_EXTERNAL_STOP')
 signal.signal(signal.SIGALRM,abort);signal.signal(signal.SIGTERM,abort);signal.setitimer(signal.ITIMER_REAL,end-time.time())
 try:
  factory=load('v1039_unchanged_physical',R/'experiments/v1020_terminal_two_route_development/physical.py');creating=True;v=factory.create_vehicle(out/'physics',task);creating=False;result['model_initializations']=1
  import mujoco as mj
  old_setup=json.loads((H/'physics/SETUP.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']==old_setup['model_sha256'],'HISTORICAL_MODEL_SHA_CHANGED'
  law=load('v1039_unchanged_v993_law',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py');before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};old=v.adapter;adapter=law.Adapter(v.m,mj,v.dt,encoders=old.encoders);adapter.virtual_rate=.6;adapter.last=old.last.copy();adapter.integral=float(old.integral);v.adapter=adapter
  assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items()),'ADAPTER_WROTE_MODEL_STATE'
  native=v.native
  def counted(*args):
   nonlocal in_native
   in_native=True;answer=native(*args);in_native=False;return answer
  v.native=counted;actual=np.load(H/'physics/NATIVE_TRACE.npz');commands=json.loads((H/'physics/BODY_COMMANDS.json').read_text());assert len(commands)==task['historical_native'];evidence=Evidence(setup['known']);evidence.update(v.scan());maximum=0.
  for i,command in enumerate(commands):
   assert time.time()<end-180,'HISTORICAL_REPLAY_TIME_RESERVE';v.step(command[1],command[2],command[5])
   for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    now=np.asarray(getattr(v.d,key));maximum=max(maximum,float(abs(now-actual[key][i]).max())if now.size else 0.)
   assert maximum<=1e-8,'HISTORICAL_NATIVE_REPLAY_CHANGED'
   if v.count%5==0:evidence.update(v.scan())
   if v.count%500==0:dump(out/'PARTIAL.json',dict(phase='HISTORICAL_REPLAY',native=v.count,maximum_historical_error=maximum))
  baseline=json.loads((H/'DYNAMIC_COMPLETE_PLAN.json').read_text());source=evidence.source(v);assert source['periodic']['vertices']==baseline['source']['periodic']['vertices'],'HISTORICAL_CAUSAL_SOURCE_CHANGED';p=causal.packet(v,True);dump(out/'APPROACH_INITIAL.json',dict(packet=p,source=source));result['historical_replay_maximum_error']=maximum
  requests=np.asarray(json.loads((C/'REQUESTS.json').read_text()));plan=component.plan(p,source,setup,requests);dump(out/'APPROACH_PLAN.json',plan);assert plan['passed'],'FRESH_APPROACH_NOT_CERTIFIED'
  def observe():return evidence.update(v.scan())
  def progress(vehicle,owner):dump(out/'PARTIAL.json',dict(phase='NEW_COMPONENT',native=vehicle.count,new_component_native=vehicle.count-16740,body=list(vehicle.body()),maximum_position_m=owner.maximum_position,maximum_heading_rad=owner.maximum_heading))
  owner=owner_module.Owner(v,end,observe,progress);execution=owner.execute(plan);dump(out/'APPROACH_EXECUTION.json',execution);assert execution['completed']and v.count==23640,'FULL_APPROACH_AND_OBSERVATION_NOT_COMPLETE'
  displacement=float(np.linalg.norm(np.asarray(v.body()[:2])-np.asarray(p['body'][:2])));assert displacement>=1. and abs(np.asarray(v.body()[3:])).max()<=.03,'ACTUAL_APPROACH_OR_STOP_FAILED'
  dump(out/'FINAL_CAUSAL_SOURCE.json',dict(packet=causal.packet(v,True),source=evidence.source(v),setup={k:setup[k]for k in ['known','limits','slew_per_second']},goal=task['goal_xy']))
  result.update(passed=True,status='CERTIFIED_APPROACH_AND_NEW_CAUSAL_OBSERVATIONS',actual_displacement_m=displacement)
 except BaseException as e:result.update(passed=False,status='FAILED',error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['model_initializations']=None
  count=None if in_native or(creating and v is None)else v.count if v is not None else 0;result['completed_native']=count;result['historical_replay_native']=None if count is None else min(16740,count);result['new_component_native']=None if count is None else max(0,count-16740)
  if v is not None:
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if evidence is not None:dump(out/'CAUSAL_EVIDENCE.json',dict(first=evidence.first,rows=evidence.snapshots,periodic_constraints=evidence.periodic.constraints))
   if not in_native and result.get('evidence_saved')and time.time()<end-30:
    try:
     result['own_replay_native']=None;proof=factory.replay(v,end,out/'physics');result['replay']=proof;result['own_replay_native']=proof['replay_native'];result['passed']=result['passed']and proof['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time());dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['physical','traceback']}),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
