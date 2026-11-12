"""Bounded measured-pose execution, recertifying complete future before each block."""
import sys,json,time,signal,fcntl,traceback,math,copy
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
RESOURCE=apply();sys.path.insert(0,str(CORE));import numpy as np
from physical_ops import dump,factory,bind,restore
from plans import REC
from kernel import load,law,virtual
from braking_reserve import Adapter
import path_tracking
from path_tracking import complete_from_measurement,select_reference,MAX_ACTIVE,STOP_NATIVE,BLOCK,reference
from native_worker import entry,sha
causal=load('tracking_core_causal_packet',R/'experiments/v1024_full_route_execution/causal.py')

def main():
 assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=entry(sys.argv[1]);w=json.loads((O/'ROUND_WINDOW.json').read_text());approval=json.loads((O/'APPROVAL.json').read_text())
 assert approval['models_authorized']and task['task_id']in approval['allowed_task_ids'];assert all(sha(R/p)==h for p,h in json.loads(Path(cfg['source_freeze']).read_text())['files'].items())
 assert min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())>120
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out.mkdir(parents=True,exist_ok=False)
 end=min(w['absolute_deadline_unix']-30,time.time()+900);history=18074;v=None;native=None;inside=False;creating=False;f=factory(O)
 result=dict(passed=False,vehicle_initializations=0,internal_factory_model_constructions='unknown',historical_replay_native=0,new_actual_native=0,own_replay_native=0,replay_state_initializations=0,private_mujoco_native=0,training_updates=0,new_main_samples=0,analytical_prediction_native=0,resource_policy=RESOURCE)
 def halt(*_):raise TimeoutError('ABSOLUTE_OR_TASK_DEADLINE')
 signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
 try:
  creating=True;v=f.create_vehicle(out/'physics',task);creating=False;result['vehicle_initializations']=1;import mujoco as mj
  setup=json.loads((out/'physics/SETUP.json').read_text());assert setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';bind(v,law.Adapter,mj);native=v.native
  def counted(*args):
   nonlocal inside
   assert v.count<history+MAX_ACTIVE+STOP_NATIVE and time.time()<end-90,'COUNT_OR_REPLAY_RESERVE'
   inside=True;x=native(*args);inside=False;return x
  v.native=counted;restore(v,history,out);packet=causal.packet(v,True);inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());expected=inp['packet']
  a=np.r_[packet['body'],packet['steering']['position'],packet['steering']['velocity'],packet['controller_memory']['last_ctrl'],packet['controller_memory']['integral']];b=np.r_[expected['body'],expected['steering']['position'],expected['steering']['velocity'],expected['controller_memory']['last_ctrl'],expected['controller_memory']['integral']]
  assert abs(a-b).max()<=1e-8 and abs(packet['sim_time']-expected['sim_time'])<=1e-8
  source=inp['source'];assert source['source_native_tick']==15290;bind(v,Adapter,mj)
  offset,candidates=select_reference(setup,packet,source);result['analytical_prediction_native']+=sum(x.get('active_native',0)+STOP_NATIVE for x in candidates if'active_native'in x)
  dump(out/'REFERENCE_SELECTION.json',dict(offset_m=offset,candidates=candidates));dump(out/'ACTUAL_INPUT.json',dict(packet=packet,setup=setup,source=source))
  path,arc=reference(offset);cross_max=0.;origin=np.asarray(v.body()[:2]);maximum=np.zeros(3);vmax=0.;progress=0;moving=0;blocks=[];stop_latched=False;certdir=out/'certificates';certdir.mkdir();prediction_wall=0.
  while not stop_latched:
   assert moving<MAX_ACTIVE,'ACTIVE_BUDGET';packet=causal.packet(v,True);packet['speed_episode']=bool(getattr(v.adapter,'_speed_episode',False));source_age=float(packet['sim_time']-source['periodic']['last'])
   start=time.monotonic();proof,ss,uu,rr,indices=complete_from_measurement(setup,packet,source,progress,MAX_ACTIVE-moving,offset);prediction_wall+=time.monotonic()-start;result['analytical_prediction_native']+=len(rr)
   number=len(blocks);prefix=min(BLOCK,proof['active_native'])if proof['active_native']else STOP_NATIVE;stop_latched=proof['active_native']==0
   meta=dict(number=number,start_native=v.count,packet=packet,source_native_tick=source['source_native_tick'],source_age_s=source_age,progress=progress,remaining_active=MAX_ACTIVE-moving,offset_m=offset,executed_native=0,planned_prefix=prefix,proof=proof)
   dump(certdir/(str(number)+'.json'),meta);np.savez_compressed(certdir/(str(number)+'.npz'),states=ss,controls=uu,requests=rr,progress=indices)
   assert proof['passed'],'COMPLETE_MEASURED_FUTURE_REJECTED'
   blocks.append(meta);dump(out/'BLOCKS.json',blocks)
   for i,req in enumerate(rr[:prefix]):
    v.step(*req);meta['executed_native']+=1;body=np.asarray(v.body());angle=body[2]-ss[i+1,2]
    e=np.array([np.linalg.norm(body[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,e);vmax=max(vmax,abs(body[3]))
    cross=float(np.linalg.norm(path[:,:2]-body[:2],axis=1).min());cross_max=max(cross_max,cross);assert cross<=.04,'ACTUAL_PATH_CROSS_TRACK';assert np.all(e<=[.04,.035,.015]),'ACTUAL_BLOCK_TRACKING';assert abs(body[3])<=.13 and abs(body[4])<=.16,'ACTUAL_BODY_CAP'
    if v.count%5==0:v.scan()
   progress=int(indices[prefix-1]);moving+=0 if stop_latched else prefix;dump(certdir/(str(number)+'.json'),meta);dump(out/'BLOCKS.json',blocks)
   dump(out/'PARTIAL.json',dict(stage='closed_loop_actual',native=v.count,new_native=v.count-history,moving_native=moving,certificates=len(blocks),maximum_tracking=maximum.tolist(),prediction_wall_s=prediction_wall))
  distance=float(np.linalg.norm(np.asarray(v.body()[:2])-task['goal_xy']));motion=float(np.linalg.norm(np.asarray(v.body()[:2])-origin))
  assert np.linalg.norm(v.body()[3:])<=.03 and distance<=.45 and motion>=1.,'ACTUAL_GOAL_PROGRESS_COMPLETE_STOP'
  result.update(passed=True,actual_goal_distance_m=distance,actual_motion_m=motion,maximum_local_tracking=maximum.tolist(),maximum_actual_longitudinal_speed=vmax,complete_stop_native=STOP_NATIVE,moving_native=moving,certificates=len(blocks),prediction_wall_s=prediction_wall,maximum_path_cross_track_m=cross_max)
 except BaseException as e:result.update(passed=False,error=repr(e),traceback=traceback.format_exc())
 finally:
  result['analytical_prediction_native']=path_tracking.PREDICTION_NATIVE
  if creating:result['vehicle_initializations']=None
  if v is not None:
   result['historical_replay_native']=None if inside else min(v.count,history);result['new_actual_native']=None if inside else max(0,v.count-history)
   try:result['physical']=v.finish();result['evidence_saved']=True
   except BaseException as e:result.update(passed=False,evidence_saved=False,save_error=repr(e))
   if not inside and result.get('evidence_saved')and v.count and time.time()<end-15:
    try:v.native=native;result['own_replay_native']=None;result['replay_state_initializations']=None;q=f.replay(v,end,out/'physics');result.update(own_replay_native=q['replay_native'],replay_state_initializations=1,replay=q);result['passed']=result['passed']and q['passed']
    except BaseException as e:result.update(passed=False,replay_error=repr(e))
  signal.setitimer(signal.ITIMER_REAL,0);result['closed']=True;load('tracking_result_sink',R/'experiments/v1067_causal_replan_brake_reserve/entry_record.py').save(out,result)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
