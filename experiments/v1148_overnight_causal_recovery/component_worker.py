"""Canonical reconstruction32515; one real8+2200 refreshed-control component."""
from night_tools import *
import math,gzip,signal,fcntl,traceback,types
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import Adapter,ref,REQUIRED
from source import Engine,initial,remaining_rows
sys.path.insert(0,str(R/'experiments/v1146_causal_certificate_refresh'))
from fast_cycle import certify
from refresh import causal_packets,try_commit,digest
sys.path.insert(0,str(R/'experiments/v1144_saved_entry_relay'))
from scene_contract import verify

PARENT=R/'runs/v858_nav2_verified/v1144/observation_main'
HISTORY=32515

def packet(v,episode):
 now=time.monotonic();b=list(v.body());e=v.steering_sample()
 return dict(body=b,body_lateral=float(-v.d.qvel[0]*math.sin(b[2])+v.d.qvel[1]*math.cos(b[2])),native_tick=v.count,sim_time=float(v.d.time),body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=e[:2].tolist(),velocity=e[2:].tolist(),native_tick=v.count,measured_at=now),controller_memory=dict(last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral)),coupled_episode=bool(episode),steering_motion_active=bool(getattr(v.adapter,'_steering_motion_active',False)))

def historical_mode(index,journal):
 if index<20160:return None
 row=journal[index-20160];assert row['native']==index and row['component_index']==index-20160
 return float(row['target'])if row['mode']else None

def main():
 task=json.loads(Path(sys.argv[1]).read_text());assert task in json.loads((C/'TASKS.json').read_text());out=Path(task['output'])
 assert out.is_relative_to(R/'runs/v858_nav2_verified/v1148')and not out.exists()
 assert json.loads((O/'APPROVAL.json').read_text())['models_authorized']and source_ok()and remaining()>500
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 out.mkdir(parents=True);end=min(time.time()+7200,time.time()+remaining()-300)
 def halt(*_):raise TimeoutError('SHORT_COMPONENT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 v=None;engine=None;creating=False;inside=False;kind='actual';replayed=0;history=0;episode=False;journal=[];proofs={};error=None;failure=None;maximum=np.zeros(3)
 result=dict(passed=False,models=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,scope='one real8-step refresh handoff plus complete2200 stop; not route acceptance')
 try:
  sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
  factory=load('short_original_cpu_factory',R/'experiments/v1114_coupled_steering_mode/physical.py')
  creating=True;dump(out/'INITIALIZATION_ATTEMPT.json',dict(at=time.time(),integrations_before=0));v=factory.create(out/'physics',task);creating=False;result['models']=1;pin()
  assert v.count==0 and v.d.time==0. and v.actor is not None
  import mujoco as mj
  from cpu_backend import require_cpu_backend
  result['resource_policy']=dict(RESOURCE,renderer=require_cpu_backend())
  setup=json.loads((out/'physics/SETUP.json').read_text());oldsetup=json.loads((PARENT/'physics/SETUP.json').read_text())
  result['scene_identity']=verify(setup,oldsetup,task)
  assert sha(out/'physics/scene_model.mjb')==sha(PARENT/'physics/scene_model.mjb')
  assert np.array_equal(np.load(out/'physics/INITIAL_STATE.npz')['state'],np.load(PARENT/'physics/INITIAL_STATE.npz')['state'])
  old=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=old.encoders);v.adapter.virtual_rate=.6;v.adapter.last=old.last.copy();v.adapter.integral=float(old.integral)
  native=v.native
  def counted(*args):
   nonlocal inside,replayed
   assert time.time()<end-2 and remaining()>30,'NATIVE_DEADLINE'
   inside=True;value=native(*args);inside=False
   if kind=='replay':replayed+=1
   return value
  v.native=counted
  historical=np.load(PARENT/'physics/NATIVE_TRACE.npz');commands=json.loads((PARENT/'physics/BODY_COMMANDS.json').read_text());oldjournal=json.loads((PARENT/'MODE_JOURNAL.json').read_text())
  scan_index={}
  for scan in json.loads(gzip.open(PARENT/'physics/SENSORS.json.gz','rt').read()):
   if scan['native_tick']<=HISTORY:scan_index.setdefault(scan['native_tick'],[]).append(scan)
  def history_scan():
   for expected in scan_index.get(v.count,[]):
    actual=v.scan();assert all(actual[k]==expected[k]for k in ['native_tick','time','xy','yaw','ranges']),'HISTORICAL_SENSOR_CHANGED'
  history_scan()
  for i in range(HISTORY):
   assert time.time()<end-130 and remaining()>200,'RECONSTRUCTION_RESERVE'
   v.adapter.parked_target=historical_mode(i,oldjournal)
   if i>=20160:
    row=oldjournal[i-20160];assert np.max(abs(v.adapter.last-row['last_ctrl']))<=1e-10 and abs(v.adapter.integral-row['integral'])<=1e-10,'HISTORICAL_CONTROLLER_MEMORY'
   _,vr,wr,_,_,stale=commands[i];v.step(vr,wr,bool(stale));history=v.count
   for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    current=np.asarray(getattr(v.d,key));expected=historical[key][i]
    if current.size:assert np.max(abs(current-expected))<=1e-8,'HISTORICAL_STATE_CHANGED '+key
   history_scan()
   if v.count%1000==0:dump(out/'PARTIAL.json',dict(stage='canonical_history_reconstruction',native=v.count))
  p=packet(v,False);saved=json.loads((PARENT/'STOP_CERTIFICATES.json').read_text())[-1]
  assert np.max(abs(np.asarray(initial(p)['state'])-np.asarray(initial(saved['packet'])['state'])))<=1e-8
  assert np.max(abs(np.asarray(p['controller_memory']['last_ctrl'])-saved['packet']['controller_memory']['last_ctrl']))<=1e-8
  assert abs(p['controller_memory']['integral']-saved['packet']['controller_memory']['integral'])<=1e-8
  dump(out/'ACTUAL_REFRESH_PACKET.json',p)
  checkpoint=np.zeros(mj.mj_stateSize(v.m,v.spec));mj.mj_getState(v.m,v.d,checkpoint,v.spec);np.savez_compressed(out/'CHECKPOINT_INTEGRATION.npz',state=checkpoint,controller_last=v.adapter.last,integral=np.array([v.adapter.integral]),native=np.array([v.count]));dump(out/'CHECKPOINT_RECORD.json',dict(spec=int(v.spec),model_sha256=sha(out/'physics/scene_model.mjb'),state_sha256=hashlib.sha256(checkpoint.tobytes()).hexdigest(),native=v.count,sim_time=float(v.d.time),packet=p,original_prefix_reconstructed=True,not_a_new_route_sample=True,no_state_restore_performed=True))
  clean,duplicates=causal_packets(v.sensor_rows,p)
  causal=load('short_original_causal',R/'experiments/v1024_full_route_execution/causal.py');norm=load('short_original_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
  evidence=causal.Evidence(setup['known']);evidence.periodic=norm.PeriodicSupport()
  for scan in clean:evidence.update(scan)
  source=evidence.source(types.SimpleNamespace(d=types.SimpleNamespace(time=p['sim_time'])));dump(out/'ACTUAL_CAUSAL_SOURCE.json',source)
  oldx=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text())
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.spatial import ConvexHull
  nested=max(float((np.asarray(new)@ConvexHull(np.asarray(prior)).equations[:,:3].T+ConvexHull(np.asarray(prior)).equations[:,3]).max())for new,prior in zip(source['periodic']['vertices'],oldx['source']['periodic']['vertices']))
  assert nested<=2e-8,'NONNESTED_OBSERVATION_DOMAIN'
  rows=json.loads((R/'runs/v1144_saved_entry_relay/software/ROWS.json').read_text())['rows'];rest=remaining_rows(rows,12355);block=[];left=8
  for target,speed,count,mode in rest:
   take=min(left,int(count));block.append((target,speed,take,mode));left-=take
   if not left:break
  assert not left and all(not row[3]for row in block)
  schedules=dict(current=[(0.,0.,2200,0)],prospective=block+[(0.,0.,2200,0)])
  engine=Engine(setup);predictions={};x=dict(setup=setup,packet=p,source=source)
  for name,rows in schedules.items():
   ss,uu=engine.simulate(initial(p),rows);predictions[name]=(ss,uu)
   proofs[name]=certify(dict(x,goal=ss[-1,:2].tolist(),safe_terminal_pose=ss[-1,:3].tolist()),ss,uu,rows)
  previous=dict(packet_sha256=digest(p),proof=saved['current'])
  candidate=dict(packet_sha256=digest(p),nested_domain=True,duals_verified=True,source_native_tick=source['source_native_tick'],source_age_s=source['source_age_s'],support_kind='original analytic coefficient full-cycle envelope; no LP duals needed')
  bundle,transaction=try_commit(previous,p,lambda _:candidate,lambda a,b:proofs,time.monotonic,time.monotonic()+1.)
  assert transaction['committed'],'REFRESH_TRANSACTION_REFUSED'
  dump(out/'REFRESH_CERTIFICATES.json',dict(packet=p,proofs=proofs,transaction=transaction,nested_hull_residual=nested,actual_packets=len(clean),duplicates=duplicates))
  ss,uu=predictions['prospective'];np.savez_compressed(out/'PREDICTED_COMPONENT.npz',states=ss,controls=uu)
  schedule=schedules['prospective'];index=0
  for target,speed,count,mode in schedule:
   for _ in range(count):
    before=packet(v,episode);journal.append(dict(native=v.count,component_index=index,target=target,speed=speed,mode=False,last_ctrl=before['controller_memory']['last_ctrl'],integral=before['controller_memory']['integral']))
    v.adapter.parked_target=None;v.step(speed,0. if not speed else speed*math.tan(target)/.6,False)
    b=np.asarray(v.body());enc=v.steering_sample();expected=ss[index+1];virtual=__import__('kernel').virtual(enc[:2])
    errors=np.array([np.linalg.norm(b[:2]-expected[:2]),abs(math.atan2(math.sin(b[2]-expected[2]),math.cos(b[2]-expected[2]))),abs(virtual-expected[6])]);maximum=np.maximum(maximum,errors)
    assert np.all(errors<=[.04,.035,.015]),'ACTUAL_REFERENCE_RESPONSE_FAILED'
    lateral=-v.d.qvel[0]*math.sin(b[2])+v.d.qvel[1]*math.cos(b[2]);assert abs(b[3])<=.13 and abs(b[4])<=.16 and abs(lateral)<=.03,'ACTUAL_BODY_CAP'
    if v.count%5==0:v.scan()
    index+=1
  final=packet(v,False);target=ss[-1,:3];position_error=float(np.linalg.norm(np.asarray(final['body'][:2])-target[:2]));yaw_error=abs(math.atan2(math.sin(final['body'][2]-target[2]),math.cos(final['body'][2]-target[2])))
  assert position_error<=.025 and yaw_error<=.1 and abs(np.asarray(final['body'][3:])).max()<=.003 and abs(v.steering_sample()[2:]).max()<=.015,'ACTUAL_COMPONENT_TERMINAL'
  actual_pose=np.array(final['body'][:3])[None,:];a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(actual_pose);assert min(a[0],b[0])>=REQUIRED,'ACTUAL_CYCLE_HOLD'
  result.update(passed=True,component_native=index,maximum_response_error=maximum,terminal_position_error_m=position_error,terminal_yaw_error_rad=yaw_error,actual_full_cycle_raw_m=float(min(a[0],b[0])),fresh_actual_sensor_count=len(clean),actual_prefix_progress_m=float(np.linalg.norm(np.asarray(v.rows[HISTORY+7]['qpos'][:2])-np.asarray(p['body'][:2]))),original_goal_passed=False)
  dump(out/'ACTUAL_FINAL_PACKET.json',final)
 except BaseException as e:
  error=dict(error=repr(e),traceback=traceback.format_exc());result['passed']=False;dump(out/'ERROR.json',error)
 finally:
  result.update(error=error,historical_reconstruction_native=history,new_actual_native=None if inside and kind=='actual'else v.count if v else None if creating else 0,models=None if creating else result['models'],analytical_cpp_native=engine.native if engine else 0,analytical_inflight_unknown=bool(engine and getattr(engine,'in_call',False)))
  result['new_component_native']=None if result['new_actual_native']is None else max(0,result['new_actual_native']-HISTORY)
  dump(out/'MODE_JOURNAL.json',journal)
  if v is not None:
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if result.get('evidence_saved')and v.count and not inside and time.time()<end-25 and remaining()>60:
    try:
     kind='replay';result['replay_state_initializations']=1;result['own_replay_native']=None;result['replay']=factory.replay(v,end,out/'physics');result['own_replay_native']=replayed;result['passed']=bool(result['passed']and result['replay']['passed'])
    except BaseException as e:result.update(passed=False,replay_error=repr(e),own_replay_native=None if inside else replayed)
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,source_unchanged=source_ok(),closed_unix=time.time());dump(out/'RESULT.json',result);print(encode(result))
 return 0 if result['passed']else 1

if __name__=='__main__':sys.exit(main())
