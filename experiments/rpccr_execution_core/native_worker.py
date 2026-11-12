"""Single reusable saved-continuation worker; physical import stays inside main."""
import sys,json,time,signal,fcntl,traceback,math,hashlib
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
RESOURCE=apply();sys.path.insert(0,str(CORE));import numpy as np
from physical_ops import dump,factory,bind,restore
from plans import complete,REC
from kernel import load,law,virtual
from braking_reserve import Adapter
causal=load('execution_core_causal_packet',R/'experiments/v1024_full_route_execution/causal.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def entry(taskfile):
 task=json.loads(Path(taskfile).read_text());O=Path(task['run_root']);cfg=json.loads((O/'CONFIG.json').read_text());assert task in json.loads(Path(cfg['task_table']).read_text());out=Path(task['output']);assert out.parent==R/'runs/v858_nav2_verified'/cfg['version'];return task,O,cfg,out

def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=entry(sys.argv[1]);w=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text());assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'];assert all(sha(R/p)==h for p,h in json.loads(Path(cfg['source_freeze']).read_text())['files'].items());assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>120;lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False);end=min(w['absolute_deadline_unix']-30,time.time()+900);history=18074;v=None;native=None;inside=False;creating=False;f=factory(O);result=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',historical_replay_native=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,new_main_samples=0,resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('ABSOLUTE_OR_TASK_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;import mujoco as mj
  setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';bind(v,law.Adapter,mj);native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<history+3555 and time.time()<end-90,'COUNT_OR_REPLAY_RESERVE';inside=True;x=native(*args);inside=False;return x
  v.native=counted;restore(v,history,out);packet=causal.packet(v,True);inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());expected=inp['packet'];a=np.r_[packet['body'],packet['steering']['position'],packet['steering']['velocity'],packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']];b=np.r_[expected['body'],expected['steering']['position'],expected['steering']['velocity'],expected['controller_memory']['last_ctrl'],expected['controller_memory']['integral']];assert abs(a-b).max()<=1e-8 and abs(packet['sim_time']-expected['sim_time'])<=1e-8;source=inp['source'];assert source['source_native_tick']==15290;bind(v,Adapter,mj);proof,ss,uu,rr=complete(setup,packet,source);assert proof['passed'],'COMPLETE_SOURCE_REJECTED';dump(out/'PLAN_PROOF.json',proof);np.savez_compressed(out/'PLAN.npz',states=ss,controls=uu,requests=rr);dump(out/'ACTUAL_INPUT.json',dict(packet=packet,setup=setup,source=source));origin=np.asarray(v.body()[:2]);maximum=np.zeros(3);reserve=[];vmax=0.
  for i,req in enumerate(rr):
   v.step(*req);body=np.asarray(v.body());angle=body[2]-ss[i+1,2];e=np.array([np.linalg.norm(body[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,e);vmax=max(vmax,abs(body[3]));reserve.append(v.adapter.last_braking_reserve);assert np.all(maximum<=[.04,.035,.015]),'ACTUAL_TRACKING';assert abs(body[3])<=.13 and abs(body[4])<=.16,'ACTUAL_BODY_CAP'
   if v.count%5==0:v.scan()
   if (i+1)%250==0:dump(out/'PARTIAL.json',dict(stage='new_actual',native=v.count,new_native=i+1,maximum_tracking=maximum.tolist(),maximum_speed=vmax))
  distance=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']));progress=float(np.linalg.norm(np.asarray(v.body()[:2])-origin));assert np.linalg.norm(v.body()[3:])<=.03 and distance<=.45 and progress>=1.,'ACTUAL_GOAL_PROGRESS_COMPLETE_STOP';result.update(passed=True,actual_goal_distance_m=distance,actual_motion_m=progress,maximum_local_tracking=maximum.tolist(),maximum_actual_longitudinal_speed=vmax,complete_stop_native=2200)
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  if creating:result['vehicle_initializations']=None
  if v is not None:
   result['historical_replay_native']=None if inside else min(v.count,history);result['new_actual_native']=None if inside else max(0,v.count-history)
   try:
    result['physical']=v.finish();result['evidence_saved']=True
    if'reserve'in locals():dump(out/'BRAKING_RESERVE.json',reserve)
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-15:
    try:v.native=native;result['own_replay_native']=None;result['replay_state_initializations']=None;q=f.replay(v,end,out/'physics');result.update(own_replay_native=q['replay_native'],replay_state_initializations=1,replay=q);result['passed']=result['passed']and q['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('core_result_sink',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
