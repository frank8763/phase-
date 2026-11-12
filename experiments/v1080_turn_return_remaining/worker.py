"""Frozen two moving-return tests, conditional previously unexecuted3555 only."""
import sys,signal,fcntl,traceback,gzip,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths();from resource_policy import apply
RESOURCE=apply()
from science import *
causal=load('v1080_original_measured_packet',R/'experiments/v1024_full_route_execution/causal.py')
def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task=json.loads(Path(sys.argv[1]).read_text());out=contracts(task);w=json.loads((O/'ROUND_WINDOW.json').read_text());a=json.loads((O/'APPROVAL.json').read_text());assert a['models_authorized']and task['task_id']in a['allowed_task_ids'];assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);history=18074 if task['kind']=='remaining'else 0;rr=requests(task);limit=history+len(rr);end=min(w['absolute_deadline_unix']-30,time.time()+(900 if history else 300));reserve=90 if history else 60;v=None;native=None;creating=False;inside=False;f=factory();result=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',historical_replay_native=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,new_main_samples=0,resource_policy=RESOURCE,kind=task['kind'])
 def halt(*_):raise TimeoutError('CHILD_OR_ABSOLUTE_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';assert v.count==0 and v.d.time==0.;import mujoco as mj
  previous=v.adapter;before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};v.adapter=law.Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());assert Path(v.adapter.compute.__func__.__code__.co_filename).resolve()==R/'experiments/v1035_signed_timed_input_source/signed_control.py';native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<limit and time.time()<end-reserve,'NATIVE_OR_REPLAY_RESERVE';inside=True;q=native(*args);inside=False;return q
  v.native=counted
  if history:
   old=np.load(ARCH/'physics/NATIVE_TRACE.npz');cmd=np.asarray(json.loads((ARCH/'physics/BODY_COMMANDS.json').read_text()));assert len(old['qpos'])==history;assert np.array_equal(v.initial,np.load(ARCH/'physics/INITIAL_STATE.npz')['state'])
   with gzip.open(ARCH/'physics/CONTACTS.json.gz','rt')as inp:contacts=json.load(inp)
   with gzip.open(ARCH/'physics/SENSORS.json.gz','rt')as inp:sensors={s['native_tick']:s for s in json.load(inp)}
   maximum=0.;range_error=0.;contact_errors=0
   def check_scan():
    nonlocal range_error
    s=v.scan();range_error=max(range_error,float(abs(np.asarray(s['ranges'])-sensors[v.count]['ranges']).max()));assert range_error<=1e-6,'HISTORICAL_RANGE_MISMATCH'
   check_scan()
   for i in range(history):
    v.step(*cmd[i,[1,2,5]])
    for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
     q=np.asarray(getattr(v.d,k));maximum=max(maximum,float(abs(q-old[k][i]).max())if q.size else 0.)
    assert maximum<=1e-8,'HISTORICAL_STATE_CONTROL_MISMATCH';aa=v.contacts[-1];bb=contacts[i+1];same=len(aa)==len(bb)and all(list(x[:3])==list(y[:3])and abs(x[3]-y[3])<=1e-8 for x,y in zip(aa,bb));contact_errors+=not same;assert same,'HISTORICAL_CONTACT_MISMATCH'
    if v.count%5==0:check_scan()
    if v.count%1000==0:dump(out/'PARTIAL.json',dict(stage='historical_replay',native=v.count))
   dump(out/'HISTORICAL_REPLAY_PROOF.json',dict(passed=True,native=history,maximum_state_ctrl_mocap_error=maximum,range_error=range_error,contact_mismatched_ticks=contact_errors,no_external_state_restore=True))
  else:v.scan()
  packet=causal.packet(v,bool(history));source=None
  if history:
   inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());expected=inp['packet'];actual=np.r_[packet['body'],packet['steering']['position'],packet['steering']['velocity'],packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']];target=np.r_[expected['body'],expected['steering']['position'],expected['steering']['velocity'],expected['controller_memory']['last_ctrl'],expected['controller_memory']['integral']];assert abs(actual-target).max()<=1e-8 and abs(packet['sim_time']-expected['sim_time'])<=1e-8,'ACTUAL_REMAINDER_ROOT_CHANGED';source=inp['source'];assert source['source_native_tick']==15290 and packet['native_tick']==18074
  proposal=plan(setup,packet,source,rr,task);assert proposal['passed'],'ACTUAL_ROOT_COMPLETE_PLAN_REJECTED';ss=proposal.pop('states');uu=proposal.pop('controls');ff=proposal.pop('front_states');proposal.pop('requests');np.savez_compressed(out/'PLAN.npz',states=ss,controls=uu,requests=rr,front_states=ff);dump(out/'PLAN_PROOF.json',proposal);dump(out/'ACTUAL_INPUT.json',dict(packet=packet,source=source,setup=setup,task=task));origin=np.asarray(v.body()[:2]);maximum=np.zeros(3)
  for i,req in enumerate(rr):
   v.step(*req);b=np.asarray(v.body());d=b[2]-ss[i+1,2];err=np.array([np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(d),math.cos(d))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,err);assert np.all(maximum<=[.04,.035,.015]),'ACTUAL_LOCAL_TRACKING';assert abs(b[3])<=.13 and abs(b[4])<=.16,'ACTUAL_BODY_CAP'
   if task['kind']=='turn_return'and i+1==405:
    enc=v.steering_sample()[:2];speed=v.body()[3];cmd_positions=np.asarray(v.rows[-1]['qpos'])[:2]-np.asarray(v.rows[279]['qpos'])[:2];assert abs(enc).max()<=.02 and speed>=.10 and np.linalg.norm(cmd_positions)>=.10,'MOVING_RETURN_FUNCTIONAL_GATE';result['moving_return']=dict(front_angles=enc.tolist(),forward_speed=speed,forward_progress_after_turn=float(np.linalg.norm(cmd_positions)))
   if v.count%5==0:v.scan()
   if v.count%500==0:dump(out/'PARTIAL.json',dict(stage='new_actual',native=v.count,new_native=v.count-history,maximum_local_tracking=maximum.tolist()))
  assert np.linalg.norm(v.body()[3:])<=.03,'ACTUAL_STOP_REQUIRED';progress=float(np.linalg.norm(np.asarray(v.body()[:2])-origin));distance=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']))
  if history:assert distance<=.45 and progress>=1.,'ACTUAL_GOAL_AND_ONE_METRE_REQUIRED'
  else:assert progress>=.30,'ACTUAL_RESPONSE_MOTION_REQUIRED'
  result.update(passed=True,actual_motion_m=progress,actual_goal_distance_m=distance,maximum_local_tracking=maximum.tolist(),complete_stop_native=2200,actual_control_owner='Original V1035 signed Adapter via vehicle.step only')
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  if v is not None:
   result['historical_replay_native']=None if inside else min(v.count,history);result['new_actual_native']=None if inside else max(0,v.count-history)
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-15:
    try:v.native=native;result['own_replay_native']=None;result['replay_state_initializations']=None;q=f.replay(v,end,out/'physics');result.update(own_replay_native=q['replay_native'],replay_state_initializations=1,replay=q);result['passed']=result['passed']and q['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('v1080_original_result_sink',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
