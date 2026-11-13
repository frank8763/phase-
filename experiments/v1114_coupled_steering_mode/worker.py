"""One authorized physical component, exact recorded-input replay, no retry."""
import sys,os,json,time,signal,fcntl,traceback,importlib.util,math
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from common import R,O,dump,sha,remaining,source_ok,pin,RESOURCE
sys.path.insert(0,str(C))
from fixture_contract import validate_task,validate_actual
import numpy as np
from logic import Adapter,SteeringModeRefusal,kernel,initial,response_error,response_passed,measured_rest,ready_to_drive
sys.path.insert(0,str(C))
from execution import applied_step,complete_stop_source,execute_complete_stop
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def packet(v):
 now=time.monotonic();enc=v.steering_sample()
 body=list(v.body());lat=float(-v.d.qvel[0]*math.sin(body[2])+v.d.qvel[1]*math.cos(body[2]));return dict(body=body,body_lateral=lat,native_tick=v.count,sim_time=float(v.d.time),body_measured_at=now,sent_at=now,dynamic_discovered=False,steering=dict(position=enc[:2].tolist(),velocity=enc[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)))
def main():
 task=json.loads(Path(sys.argv[1]).read_text());w=json.loads((O/'ROUND_WINDOW.json').read_text())
 assert task in json.loads((C/'TASKS.json').read_text()) and task['dynamic']is False
 fixture=json.loads((C/'STATIC_T0_SOURCE_FIXTURE.json').read_text());validate_task(task,fixture)
 assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']and not(O/'COMPLETION.json').exists()
 assert remaining(w)>800 and source_ok(),'AUTHORITY_OR_SOURCE'
 out=Path(task['output']);assert out.is_relative_to(R/'runs/v858_nav2_verified/v1114')and not out.exists()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out.mkdir(parents=True);start=time.monotonic();end=min(time.time()+750,time.time()+remaining(w)-10)
 result=dict(passed=False,vehicle_initializations=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,analytical_prediction_native=0,whole_route_passed=False,scope='fixed coupled steering component')
 v=None;creating=False;inside_native=False;native_kind='actual';completed_replay=0;journal=[];rejected=[];first=None;coupled_episode=False;anchor=None;envelopes=[]
 def abort(*_):raise TimeoutError('ABSOLUTE_COMPONENT_DEADLINE')
 signal.signal(signal.SIGTERM,abort);signal.signal(signal.SIGALRM,abort);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  factory=load('v1114_cpu_static_factory',C/'physical.py');creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(started_unix=time.time(),integrations_before=0))
  v=factory.create(out/'physics',task);creating=False;result['vehicle_initializations']=1;pin();assert v.count==0 and v.d.time==0. and v.actor is None
  import mujoco as mj
  from cpu_backend import require_cpu_backend
  result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend())
  setup=json.loads((out/'physics/SETUP.json').read_text());validate_actual(task,fixture,setup,sha(out/'physics/scene_model.mjb'))
  old=v.adapter;before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
  v.adapter=Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=float(old.integral)
  assert all(np.array_equal(a,np.asarray(getattr(v.d,k)))for k,a in before.items()),'BINDING_WROTE_STATE'
  actual_initial=packet(v);dump(out/'ACTUAL_INITIAL_PACKET.json',actual_initial)
  with np.load(C/('PLAN_'+task['task_id']+'.npz'))as z:plan={k:z[k].copy()for k in z.files}
  assert np.max(abs(initial(actual_initial)['state']-plan['states'][0]))<=1e-8,'CANONICAL_INITIAL_STATE_CHANGED'
  phases=json.loads((C/('PHASES_'+task['task_id']+'.json')).read_text())
  native=v.native
  def counted(*args):
   nonlocal inside_native,completed_replay
   assert time.time()<end-2 and remaining(w)>2,'NATIVE_DEADLINE'
   inside_native=True;value=native(*args);inside_native=False
   if native_kind=='replay':completed_replay+=1
   return value
  v.native=counted
  def step(vrequest,wrequest,mode,target,phase,nominal_index):
   nonlocal coupled_episode
   applied_step(v,[vrequest,wrequest],mode,target,phase,nominal_index,journal,rejected)
   if mode:coupled_episode=True
   if abs(vrequest)>=.005:coupled_episode=False
   body=v.body();lateral=-v.d.qvel[0]*math.sin(body[2])+v.d.qvel[1]*math.cos(body[2])
   assert abs(body[3])<=.13 and abs(body[4])<=.16 and abs(lateral)<=.03,'ACTUAL_BODY_CAP'
   if mode:assert np.array_equal(v.d.ctrl[v.adapter.commands.ids[2:]],np.zeros(2)),'PARKED_REAR_NOT_ZERO'
   if anchor is not None:
    distance=float(np.linalg.norm(np.asarray(body[:2])-anchor[:2]));angle=abs(math.atan2(math.sin(body[2]-anchor[2]),math.cos(body[2]-anchor[2])))
    assert distance<=.02 and angle<=.1,'COUPLED_FOOTPRINT_ENVELOPE_ANOMALY'
  maximum=np.zeros(3);phase_metrics=[]
  for phase in phases:
   if phase['parked']and not measured_rest(v.body(),v.steering_sample()):first=dict(reason='PARKED_ENTRY_NOT_ACTUALLY_REST',phase=phase['name'],native=v.count);break
   if phase['name']=='restart'and not ready_to_drive(v.body(),v.steering_sample(),phase['target']):first=dict(reason='ACTUAL_STEERING_NOT_READY',phase=phase['name'],native=v.count);break
   if phase['name']in ['restart','final_stop']:anchor=None
   if phase['parked']:
    anchor=np.array(v.body()[:3]);raw=float(kernel.ref._old.Geometry(setup['known'],None).clearances(anchor[None,:])[0][0]);lower=raw-.02-math.hypot(.44,.375)*.1
    assert lower>=kernel.REQUIRED,'COUPLED_COMPLETE_ENVELOPE_NOT_CERTIFIED'
    envelopes.append(dict(start_native=v.count,phase=phase['name'],anchor=anchor.tolist(),translation_limit_m=.02,yaw_limit_rad=.1,raw_anchor_m=raw,whole_envelope_raw_lower_m=lower));dump(out/'MODE_ENVELOPES.json',envelopes)
   start_body=np.array(v.body());pm=np.zeros(3)
   for i in range(phase['begin'],phase['end']):
    assert time.monotonic()-start<600 and time.time()<end-120 and remaining(w)>120,'STOP_AND_REPLAY_RESERVE'
    try:step(*plan['requests'][i,:2],plan['modes'][i],plan['targets'][i],phase['name'],i)
    except SteeringModeRefusal as error:
     first=dict(reason=str(error),phase=phase['name'],native=v.count,unapplied_nominal_index=i);break
    e=response_error(v.body(),kernel.virtual(v.steering_sample()[:2]),plan['states'][i+1]);maximum=np.maximum(maximum,e);pm=np.maximum(pm,e)
    if not response_passed(e):first=dict(reason='NATIVE_MODEL_RESPONSE_ERROR',phase=phase['name'],native=v.count,errors=e.tolist(),limits=[.01,.008,.015],predicted=plan['states'][i+1].tolist(),actual_body=list(v.body()),actual_encoder=v.steering_sample().tolist());break
    if plan['coupled'][i]and abs(v.body()[3]-plan['states'][i+1,3])>.002:first=dict(reason='COUPLED_LONGITUDINAL_PREDICTION_ERROR',phase=phase['name'],native=v.count,actual_speed=v.body()[3],predicted_speed=float(plan['states'][i+1,3]),limit=.002);break
   phase_metrics.append(dict(name=phase['name'],actual_end=v.count,maximum_error=pm.tolist(),actual_yaw_change=float(v.body()[2]-start_body[2])))
   dump(out/'PARTIAL_PROGRESS.json',dict(native=v.count,phase=phase['name'],first_failure=first))
   if first:break
  result.update(first_failure=first,maximum_response_error=maximum.tolist(),phase_metrics=phase_metrics,planned_complete=v.count==8100 and first is None)
  if first:
   dump(out/'FIRST_RESPONSE_FAILURE.json',first);begin=v.count
   origin=packet(v);origin['coupled_episode']=coupled_episode;proof,ss,uu=complete_stop_source(setup,origin);result['analytical_prediction_native']+=2200;dump(out/'FAILURE_STOP_CERTIFICATE.json',dict(packet=origin,proof=proof));np.savez_compressed(out/'FAILURE_STOP_SOURCE.npz',states=ss,controls=uu)
   assert proof['passed'],'ACTUAL_STATE_COMPLETE_STOP_NOT_CERTIFIED'
   execute_complete_stop(step,lambda:time.time()<end-45 and remaining(w)>45)
   result['failure_stop']=dict(begin=begin,end=v.count,native=2200,actual_rest=measured_rest(v.body(),v.steering_sample()))
   assert result['failure_stop']['actual_rest'],'FAILURE_TAIL_NOT_STOPPED'
  else:
   assert measured_rest(v.body(),v.steering_sample()),'TERMINAL_ACTUAL_REST'
   result['passed']=True
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  result['new_actual_native']=None if inside_native and native_kind=='actual'else v.count if v is not None else None if creating else 0
  dump(out/'MODE_JOURNAL.json',journal)
  dump(out/'REJECTED_COMMANDS.json',rejected)
  if v is not None:
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if result.get('evidence_saved')and v.count>0 and not inside_native and len(v.rows)==v.count and time.time()<end-30 and remaining(w)>30:
    try:
     native_kind='replay';result['replay_state_initializations']=1;result['own_replay_native']=None
     result['replay']=factory.replay(v,min(end,time.time()+remaining(w)-2),out/'physics');result['own_replay_native']=completed_replay;result['passed']=bool(result['passed']and result['replay']['passed'])
    except BaseException as e:result.update(passed=False,replay_error=repr(e),own_replay_native=None if inside_native else completed_replay)
  signal.setitimer(signal.ITIMER_REAL,0)
  result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-start)
  dump(out/'RESULT.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['traceback','physical','phase_metrics']}),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
