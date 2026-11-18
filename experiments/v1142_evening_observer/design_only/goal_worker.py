"""One physical historical reconstruction and fixed certified observation refuge."""
import sys,os,time,math,signal,fcntl,gzip,traceback
from evening_tools import *
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'));from bindings import Adapter,initial
from source import Engine,remaining_rows
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry,REQUIRED

def front(rows,n):
 out=[]
 for t,v,k,m in rows:
  take=min(n,int(k))
  if take:out.append((t,v,take,m));n-=take
  if not n:break
 assert n==0;return out

def packet(v,episode):
 now=time.monotonic();enc=v.steering_sample();b=v.body();return {'body':list(b),'body_lateral':float(-v.d.qvel[0]*math.sin(b[2])+v.d.qvel[1]*math.cos(b[2])),'native_tick':v.count,'sim_time':float(v.d.time),'body_measured_at':now,'sent_at':now,'dynamic_discovered':True,'steering':{'position':enc[:2].tolist(),'velocity':enc[2:].tolist(),'native_tick':v.count,'measured_at':now},'controller_memory':{'last_ctrl':v.adapter.last.tolist(),'integral':float(v.adapter.integral)},'coupled_episode':bool(episode),'steering_motion_active':bool(getattr(v.adapter,'_steering_motion_active',False))}

def main():
 task=json.loads(Path(sys.argv[1]).read_text());assert task in json.loads((C/'TASKS.json').read_text());assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']and source_ok()and remaining()>1000;out=Path(task['output']);assert out.is_relative_to(R/'runs/v858_nav2_verified/v1142')and not out.exists();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True);end=min(time.time()+950,time.time()+remaining()-10);signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('OBSERVER_DEADLINE')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('OBSERVER_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()));v=None;engine=None;creating=False;inside=False;kind='actual';replay_count=0;episode=False;journal=[];certificates=[];error=None;failure=None;history_count=0;maximum=np.zeros(3);anchor_mode=None
 result={'passed':False,'vehicle_initializations':0,'new_actual_native':0,'own_replay_native':0,'replay_state_initializations':0,'private_mujoco_native':0,'training_updates':0,'historical_reconstruction_native':0,'new_observer_component_native':0,'scope':'fixed observation-to-original-goal component with historical reconstruction'}
 try:
  factory=load('afternoon_observer_factory',C/'physical.py');creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',{'started_unix':time.time(),'integrations_before':0});v=factory.create(out/'physics',task);creating=False;result['vehicle_initializations']=1;pin();assert v.count==0 and v.d.time==0. and v.actor is not None
  import mujoco as mj
  from cpu_backend import require_cpu_backend
  result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend());oldroot=R/'runs/v858_nav2_verified/v1142/observation_main';oldph=oldroot/'physics';setup=json.loads((out/'physics/SETUP.json').read_text());oldsetup=json.loads((oldph/'SETUP.json').read_text());assert setup['model_sha256']==oldsetup['model_sha256']==sha(out/'physics/scene_model.mjb'),'CANONICAL_MODEL_CHANGED';__import__('scene_contract').verify(setup,oldsetup,task);contract=load('afternoon_route_contract',R/'experiments/v1089_route_scene_contract/contract.py');contract.verify_live(v,task);assert np.array_equal(np.load(oldph/'INITIAL_STATE.npz')['state'],np.load(out/'physics/INITIAL_STATE.npz')['state']),'INITIAL_STATE_CHANGED'
  old_adapter=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=old_adapter.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old_adapter.last.copy();v.adapter.integral=float(old_adapter.integral);dump(out/'ACTUAL_INITIAL_PACKET.json',packet(v,False));native=v.native
  def counted(*args):
   nonlocal inside,replay_count
   assert time.time()<end-2 and remaining()>2;inside=True;value=native(*args);inside=False
   if kind=='replay':replay_count+=1
   return value
  v.native=counted
  history_modes={r['native']:r for r in json.loads((oldroot/'MODE_JOURNAL.json').read_text())};hist={k:v.copy()for k,v in np.load(oldph/'NATIVE_TRACE.npz').items()};cmd=json.loads((oldph/'BODY_COMMANDS.json').read_text());scanrows=json.loads(gzip.open(oldph/'SENSORS.json.gz','rt').read());scans={}
  for row in scanrows:
   if row['native_tick']<=34860:scans.setdefault(row['native_tick'],[]).append(row)
  def oldscan():
   for expected in scans.get(v.count,[]):
    actual=v.scan();assert all(actual[k]==expected[k]for k in ['native_tick','time','xy','yaw','ranges']),'HISTORICAL_SENSOR_CHANGED'
  oldscan()
  for i in range(34860):
   assert time.time()<end-400 and remaining()>400,'HISTORY_REPLAY_RESERVE';_,vr,wr,mv,mw,stale=cmd[i];v.adapter.parked_target=history_modes[i]['target']if i in history_modes and history_modes[i]['mode']else None;v.step(vr,wr,bool(stale));history_count=v.count
   for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    if hist[key][i].size:assert float(abs(np.asarray(getattr(v.d,key))-hist[key][i]).max())<=1e-8,'HISTORICAL_STATE_CHANGED '+key
   oldscan()
   if v.count%500==0:dump(out/'PARTIAL.json',{'stage':'historical_reconstruction','native':v.count})
  x=json.loads((O/'post_observation/FRESH_INPUT.json').read_text());p=packet(v,False);assert float(abs(initial(p)['state']-initial(x['packet'])['state']).max())<=1e-8 and float(abs(v.adapter.last-x['packet']['controller_memory']['last_ctrl']).max())<=1e-8,'SAVED_ENTRY_CHANGED';dump(out/'ACTUAL_SAVED_ENTRY.json',p)
  data={k:v.copy()for k,v in np.load(O/'selected_goal/SOURCE.npz').items()};rows=json.loads((O/'selected_goal/ROWS.json').read_text())['rows'];table=np.load(O/'post_observation/JOINT_TABLE.npz');g=Geometry(x,{k:table[k]for k in ['bounds','centers']});engine=Engine(setup);offset=0;total=len(data['controls']);cut=len(data['controls'])-2200;mode_previous=False
  def execute_one(target,speed,mode,phase,index):
   nonlocal episode,anchor_mode,mode_previous,maximum
   b=np.asarray(v.body());before=packet(v,episode)
   if mode and not mode_previous:
    assert abs(b[3])<=.003 and abs(b[4])<=.003 and abs(v.steering_sample()[2:]).max()<=.015,'MODE_ENTRY_NOT_REST';anchor_mode=b[:3].copy();lower=float(g.cycle(anchor_mode[None,:])[0])-.02-np.hypot(.44,.375)*.1;assert lower>=REQUIRED,'ACTUAL_MODE_ENVELOPE_REFUSED'
   if abs(speed)>=.005:anchor_mode=None
   row={'native':v.count,'component_index':index,'mode':bool(mode),'target':target,'speed':speed,'last_ctrl':v.adapter.last.tolist(),'integral':float(v.adapter.integral),'episode':episode,'active':bool(getattr(v.adapter,'_steering_motion_active',False)),'phase':phase};v.adapter.parked_target=target if mode else None;before_native=v.count
   try:v.step(speed,0. if mode or speed==0 else speed*math.tan(target)/.6,False)
   except BaseException:
    if v.count>before_native:journal.append(row)
    raise
   journal.append(row)
   if mode:episode=True
   if abs(speed)>=.005:episode=False
   mode_previous=bool(mode);body=np.asarray(v.body());enc=v.steering_sample();lateral=-v.d.qvel[0]*math.sin(body[2])+v.d.qvel[1]*math.cos(body[2]);assert abs(body[3])<=.13 and abs(body[4])<=.16 and abs(lateral)<=.03,'ACTUAL_BODY_CAP'
   if anchor_mode is not None:
    assert np.linalg.norm(body[:2]-anchor_mode[:2])<=.02 and abs(math.atan2(math.sin(body[2]-anchor_mode[2]),math.cos(body[2]-anchor_mode[2])))<=.1,'ACTUAL_MODE_ENVELOPE_CHANGED'
   if mode:assert np.array_equal(v.d.ctrl[v.adapter.commands.ids[2:]],np.zeros(2))and abs(body[3])<=.01,'MODE_REAR_OR_SPEED'
   if index is not None:
    expected=data['states'][index+1];e=np.array([np.linalg.norm(body[:2]-expected[:2]),abs(math.atan2(math.sin(body[2]-expected[2]),math.cos(body[2]-expected[2]))),abs(math.atan(.6*(math.tan(enc[0])/(.6+.27*math.tan(enc[0]))+math.tan(enc[1])/(.6-.27*math.tan(enc[1])))/2)-expected[6])]);maximum=np.maximum(maximum,e);assert np.all(e<=[.04,.035,.015]),'ACTUAL_REFERENCE_RESPONSE_FAILED'
   if v.count%5==0:v.scan()
  def stopproof(p,schedule):
   ss,uu=engine.simulate(initial(p),schedule);proof,_=g.final(dict(x,packet=p,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,schedule);return proof
  while offset<total:
   assert time.time()<end-180 and remaining()>180,'STOP_REPLAY_RESERVE';rest=remaining_rows(rows,offset);first=rest[0];n=int(first[2])if first[3]or offset>=cut else min(8,int(first[2]));block=front(rest,n);p=packet(v,episode);current=stopproof(p,[(0.,0.,2200,0)]);assert current['passed'],'CURRENT_STOP_CERTIFICATE_FAILED';prospective=stopproof(p,[*block,(0.,0.,2200,0)]);certificates.append({'packet':p,'offset':offset,'count':n,'actual_native':v.count,'current':current,'prospective':prospective})
   if not prospective['passed']:failure={'reason':'NEXT_BLOCK_REFUSED','offset':offset};break
   for target,speed,ticks,mode in block:
    for _ in range(int(ticks)):
     execute_one(float(target),float(speed),bool(mode),'observation_prefix'if offset<cut else'final_stop',offset);offset+=1
   dump(out/'PARTIAL.json',{'stage':'observation_refuge','native':v.count,'offset':offset,'maximum_reference_error':maximum})
  if failure is not None:
   for _ in range(2200):execute_one(0.,0.,False,'failure_stop',None)
  else:
   final=packet(v,episode);anchor=np.asarray(data['states'][-1,:3]);body=np.asarray(v.body());distance=float(np.linalg.norm(body[:2]-anchor[:2]));yaw=abs(math.atan2(math.sin(body[2]-anchor[2]),math.cos(body[2]-anchor[2])));assert distance<=.025 and yaw<=.1 and abs(body[3:]).max()<=.003 and abs(v.steering_sample()[2:]).max()<=.015,'ACTUAL_REFUGE_TERMINAL';assert float(g.cycle(body[None,:3])[0])>=REQUIRED,'ACTUAL_REFUGE_CYCLE_HOLD';dump(out/'ACTUAL_FINAL_PACKET.json',final);result.update(passed=True,registered_component_terminal_pose=anchor.tolist(),actual_component_goal_error_m=distance,actual_component_goal_yaw_rad=yaw,maximum_reference_error=maximum,component_complete=True,original_goal_reached=bool(np.linalg.norm(body[:2]-[4.,-2.])<=.45),actual_new_observations=len([r for r in v.sensor_rows if r['native_tick']>34860]))
 except BaseException as e:
  error={'error':repr(e),'traceback':traceback.format_exc()};result['passed']=False
  # A certified stop is attempted only for a functional/model-response refusal;
  # never add steps after a native safety fault or unknown native integration.
  if v is not None and engine is not None and not inside and v.count>=34860 and time.time()<end-150 and any(label in repr(e)for label in ['ACTUAL_REFERENCE_RESPONSE_FAILED','CURRENT_STOP_CERTIFICATE_FAILED','ACTUAL_REFUGE_TERMINAL','ACTUAL_REFUGE_CYCLE_HOLD','MODE_ENTRY_NOT_REST','ACTUAL_MODE_ENVELOPE_REFUSED']):
   try:
    sp=stopproof(packet(v,episode),[(0.,0.,2200,0)]);dump(out/'FAILURE_STOP_PROOF.json',sp)
    if sp['passed']:
     begin=v.count
     for _ in range(2200):execute_one(0.,0.,False,'failure_stop',None)
     result['failure_stop']={'begin':begin,'end':v.count,'complete2200':v.count-begin==2200}
   except BaseException as se:result['failure_stop_error']=repr(se)
 finally:
  result.update(error=error,functional_failure=failure,historical_reconstruction_native=history_count,new_actual_native=None if inside and kind=='actual'else v.count if v else None if creating else 0,vehicle_initializations=None if creating else result['vehicle_initializations'],analytical_prediction_native=engine.native if engine else 0,analytical_partial_work_unknown=bool(engine and getattr(engine,'in_call',False)),source_unchanged=source_ok());result['new_observer_component_native']=None if result['new_actual_native']is None else max(0,result['new_actual_native']-history_count);dump(out/'MODE_JOURNAL.json',journal);dump(out/'STOP_CERTIFICATES.json',certificates)
  if v is not None:
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if result.get('evidence_saved')and v.count and not inside and time.time()<end-30 and remaining()>30:
    try:kind='replay';result['replay_state_initializations']=1;result['own_replay_native']=None;result['replay']=factory.replay(v,min(end,time.time()+remaining()-2),out/'physics');result['own_replay_native']=replay_count;result['passed']=bool(result['passed']and result['replay']['passed'])
    except BaseException as e:result.update(passed=False,replay_error=repr(e),own_replay_native=None if inside else replay_count)
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time(),not_three_route_or24_acceptance=True);dump(out/'RESULT.json',result);print(encode({k:v for k,v in result.items()if k not in ['physical','error']}))
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
