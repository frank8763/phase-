"""Exact historical prefix then newly calibrated complete-goal continuation.

This is a saved-state component; historical motion is not a new main sample.
No state restore/root write; every physical transition goes through vehicle.step.
"""
import sys,signal,math,fcntl,traceback,gzip
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths();sys.path.insert(0,str(C));from resource_policy import apply
RESOURCE=apply()
import numpy as np
from kernel import law,virtual
from retime_complete import propose
causal=load('v1078_actual_causal_packet',R/'experiments/v1024_full_route_execution/causal.py')
HIST=15290;INPUT=R/'records/nav2_v1076_20261112/ACTUAL_CAUSAL_ENTRY_INPUT.json';ARCH=R/'runs/v1077_speed125_response/restored_NS'
def contracts(task):
 assert task in json.loads((C/'TASKS.json').read_text())and task['historical_prefix_native']==HIST;assert Path(task['output'])==RAW/task['task_id'];assert json.loads((R/'runs/v1077_speed125_response/COMPLETION.json').read_text())['response_5_passed'];assert json.loads((R/'runs/v1077_speed125_response/RESTORED_NS.json').read_text())['passed'];return Path(task['output'])
def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task=json.loads(Path(sys.argv[1]).read_text());out=contracts(task);w=json.loads((O/'ROUND_WINDOW.json').read_text());a=json.loads((O/'APPROVAL.json').read_text());assert a['models_authorized']and task['task_id']in a['allowed_task_ids'];assert time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);f=factory();v=None;creating=False;inside=False;native=None;end=min(time.time()+900,w['absolute_deadline_unix']-30);result=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',historical_replay_native=0,recovery_native=0,own_replay_native=0,private_mujoco_native=0,replay_state_initializations=0,training_updates=0,new_main_samples=0,scope='Saved original NS15290 continuation, not a new navigation main',resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('SAVED_COMPONENT_OR_ROOT_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  old=np.load(ARCH/'NATIVE_TRACE.npz');cmd=np.array(json.loads((ARCH/'BODY_COMMANDS.json').read_text()));setup_old=json.loads((ARCH/'SETUP.json').read_text());x=json.loads(INPUT.read_text())
  with gzip.open(ARCH/'CONTACTS.json.gz','rt')as inp:old_contacts=json.load(inp)
  with gzip.open(ARCH/'SENSORS.json.gz','rt')as inp:old_sensors=json.load(inp)
  sensor_map={s['native_tick']:s for s in old_sensors};creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']==setup_old['model_sha256'];assert np.array_equal(v.initial,np.load(ARCH/'INITIAL_STATE.npz')['state']),'HISTORICAL_INITIAL_STATE_CHANGED'
  import mujoco as mj
  previous=v.adapter;before={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};v.adapter=law.Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral;assert all(np.array_equal(x,np.asarray(getattr(v.d,k)))for k,x in before.items());native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<22290 and time.time()<end-90,'SAVED_COMPONENT_NATIVE_OR_REPLAY_RESERVE';inside=True;q=native(*args);inside=False;return q
  v.native=counted;maximum_history=0.;range_error=0.;contact_mismatch=0
  def scan_check():
   nonlocal range_error
   s=v.scan();expected=sensor_map[v.count];range_error=max(range_error,float(abs(np.asarray(s['ranges'])-expected['ranges']).max()));assert range_error<=1e-6,'HISTORICAL_CAUSAL_RANGE_CHANGED';return s
  scan_check()
  for i in range(HIST):
   v.step(*cmd[i,[1,2,5]])
   for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
    values=np.asarray(getattr(v.d,key));maximum_history=max(maximum_history,float(abs(values-old[key][i]).max())if values.size else 0.)
   assert maximum_history<=1e-8,'HISTORICAL_ALL_STATE_CTRL_REPLAY_CHANGED';aa=v.contacts[-1];bb=old_contacts[i+1];same=len(aa)==len(bb)and all(list(a[:3])==list(b[:3])and abs(a[3]-b[3])<=1e-8 for a,b in zip(aa,bb));contact_mismatch+=not same;assert same,'HISTORICAL_CONTACT_CHANGED'
   if v.count%5==0:scan_check()
   if v.count%1000==0:dump(out/'PARTIAL.json',dict(stage='historical_replay',native=v.count))
  packet=causal.packet(v,True);actual_root=np.r_[packet['body'],packet['steering']['position'],packet['steering']['velocity'],packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']];expected=np.r_[x['packet']['body'],x['packet']['steering']['position'],x['packet']['steering']['velocity'],x['packet']['controller_memory']['last_ctrl'],x['packet']['controller_memory']['integral']];assert abs(actual_root-expected).max()<=1e-8 and abs(packet['sim_time']-x['packet']['sim_time'])<=1e-8,'SAVED_CAUSAL_ROOT_CHANGED';root=np.asarray(v.body()[:2]);dump(out/'HISTORICAL_REPLAY_PROOF.json',dict(passed=True,native=HIST,maximum_state_ctrl_mocap_error=maximum_history,range_error=range_error,contact_mismatched_ticks=contact_mismatch,actual_packet=packet,source_input_sha256=sha(INPUT),no_external_state_restore=True))
  baseline=np.load(R/'records/nav2_v1076_20261112/PATH_PHASE_DIAGNOSIS.npz');proposal=propose(setup,packet,x['source'],x['goal'],baseline['requests']);assert proposal['passed'],'ACTUAL_ROOT_COMPLETE_GOAL_SOURCE_REJECTED';rr=proposal.pop('requests');ss=proposal.pop('states');uu=proposal.pop('controls');assert len(rr)<7000;np.savez_compressed(out/'COMPLETE_GOAL_PLAN.npz',states=ss,controls=uu,requests=rr);dump(out/'COMPLETE_GOAL_PROOF.json',proposal);dump(out/'ACTUAL_CAUSAL_INPUT.json',dict(packet=packet,source=x['source'],goal=x['goal'],setup=setup));maximum=np.zeros(3)
  for i,request in enumerate(rr):
   v.step(*request);b=np.asarray(v.body());angle=b[2]-ss[i+1,2];err=np.array([np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,err);assert np.all(maximum<=[.04,.035,.015]),'COMPLETE_GOAL_ACTUAL_TRACKING';assert abs(b[3])<=.13 and abs(b[4])<=.16,'ACTUAL_BODY_CAP'
   if v.count%5==0:v.scan()
   if v.count%500==0:dump(out/'PARTIAL.json',dict(stage='new_recovery',native=v.count,recovery_native=v.count-HIST,maximum_local_tracking=maximum.tolist()))
  distance=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']));progress=float(np.linalg.norm(np.asarray(v.body()[:2])-root));assert distance<=.45 and progress>=1. and np.linalg.norm(v.body()[3:])<=.03,'ACTUAL_GOAL_OR_PROGRESS_OR_STOP';result.update(passed=True,actual_goal_distance=distance,actual_continuation_net_m=progress,maximum_local_tracking=maximum.tolist(),new_complete_goal_native=len(rr),historical_replay_proof=maximum_history,range_replay_error=range_error,actual_control_owner='V1035 signed Adapter via vehicle.step only',original_main_stays_failed=True)
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  if v is not None:
   result['historical_replay_native']=None if inside else min(v.count,HIST);result['recovery_native']=None if inside else max(0,v.count-HIST)
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-15:
    try:v.native=native;result['own_replay_native']=None;result['replay_state_initializations']=None;rep=f.replay(v,end,out/'physics');result.update(replay_state_initializations=1,own_replay_native=rep['replay_native'],replay=rep);result['passed']=result['passed']and rep['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('v1078_original_result_recorder',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
