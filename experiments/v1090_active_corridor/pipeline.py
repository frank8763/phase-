"""At most two fully stopped, sensed recovery corridors before goal pursuit."""
import sys,json,time,math,types
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(C));import corridor
import live_reference as live
from physical_ops import bind,dump
from braking_reserve import Adapter
from kernel import virtual
original=types.ModuleType('unchanged_goal_pipeline');original.__file__=str(CORE/'fresh_pipeline.py');exec(compile((CORE/'fresh_pipeline.py').read_text(),original.__file__,'exec'),original.__dict__)
configure=original.configure
def eligible(error):return str(error)=='LIVE_COMPLETE_STATIC_REFERENCE_REQUIRED'or str(error).startswith("('NO_LIVE_COMPLETE_DYNAMIC_REFERENCE'")
def execute(v,setup,goal_seed,end,evidence,out,packet_fn,output):
 import mujoco as mj
 started=time.monotonic();events=[];segments=__import__('owner')._active_corridor_result['_direct_segments']
 for renewal in range(3):
  bind(v,Adapter,mj);p=packet_fn(v,True);p['speed_episode']=False;source=evidence.source(v)
  try:proposal=live.produce(setup,p,source,output,goal_seed['goal'])
  except AssertionError as e:
   if not eligible(e):raise
   dump(out/('GOAL_PROPOSAL_REJECTION_%02d.json'%renewal),dict(native=v.count,error=str(e),finite_recovery_not_goal_success=True))
   assert renewal<2,'REGISTERED_TWO_RECOVERY_CORRIDORS_EXHAUSTED'
   q=corridor.construct(setup,p,source,output,goal_seed['goal']);stage=dict(stage=renewal,packet=p,source=source,goal=goal_seed['goal'],selected_proof=q['proof'],candidates=q['candidates'],requests=q['requests'].tolist(),origin_native=v.count,original_goal_proposal_rejection=str(e));events.append(stage);dump(out/'ACTIVE_CORRIDOR_STAGES.json',events);cursor=0;origin=np.array(v.body()[:2]);maximum=np.zeros(3)
   while cursor<len(q['requests']):
    assert time.time()<end-120,'ACTIVE_CORRIDOR_REPLAY_RESERVE';at=packet_fn(v,True);at['speed_episode']=False;remaining=q['requests'][cursor:];proof,ss,uu=corridor.proof(setup,at,source,remaining);assert proof['passed'],'ACTIVE_CORRIDOR_RECEDING_CERTIFICATE_REJECTED'
    # Commit a complete zero stop, otherwise original fixed input for <=125 natives.
    count=len(remaining)if np.array_equal(remaining,np.zeros_like(remaining))else min(125,len(remaining)-2200)
    assert count>0
    saved=dict(passed=True,scope='FULL_CYCLE_FINITE_ACTIVE_CORRIDOR',packet=at,source=source,stage=renewal,first_in_stage=cursor==0,planned_body_requests=remaining.tolist(),state_path=ss.tolist(),predicted_actuator_controls=uu.tolist(),proof=proof)
    path=out/('ACTIVE_CORRIDOR_%02d_%05d.json'%(renewal,cursor));dump(path,saved);row=dict(path=str(path.relative_to(R)),origin_native=v.count,executed_native=0,label='ACTIVE_CORRIDOR',source_kind='FINITE_RECOVERY_NOT_ARRIVAL');segments.append(row)
    try:
     for i,r in enumerate(remaining[:count]):
      v.step(*r);body=np.asarray(v.body());angle=body[2]-ss[i+1,2];error=np.array([np.linalg.norm(body[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(angle),math.cos(angle))),abs(virtual(v.steering_sample()[:2])-ss[i+1,6])]);maximum=np.maximum(maximum,error);assert np.all(error<=[.04,.035,.015]),'ACTIVE_CORRIDOR_LOCAL_TRACKING';assert abs(body[3])<=.13 and abs(body[4])<=.16,'ACTIVE_CORRIDOR_BODY_CAP'
      if v.count%5==0:evidence.update(v.scan())
    finally:
     row['executed_native']=v.count-row['origin_native'];dump(out/'DIRECT_SEGMENTS.json',segments)
    cursor+=count;dump(out/'PARTIAL.json',dict(phase='FINITE_ACTIVE_CORRIDOR',stage=renewal,native=v.count,executed_corridor_native=cursor,total_corridor_native=len(q['requests']),maximum_local_tracking=maximum.tolist()))
   assert np.linalg.norm(v.body()[3:])<=.03,'ACTIVE_CORRIDOR_ACTUAL_STOP_REQUIRED';motion=float(np.linalg.norm(np.asarray(v.body()[:2])-origin));assert motion>=.05,'ACTIVE_CORRIDOR_ACTUAL_MOTION_REQUIRED';stage.update(actual_motion_m=motion,end_native=v.count,maximum_local_tracking=maximum.tolist());dump(out/'ACTIVE_CORRIDOR_STAGES.json',events)
   continue
  # No re-computation or changed clock between acceptance and original execution.
  old=live.produce;live.produce=lambda *args,**kwargs:proposal
  try:answer=original.execute(v,setup,goal_seed,end,evidence,out,packet_fn,output)
  finally:live.produce=old
  answer.update(active_corridor_stages=len(events),active_corridor_native=sum(e.get('end_native',e['origin_native'])-e['origin_native']for e in events),total_recovery_wall_s=time.monotonic()-started);return answer
 raise AssertionError('NO_COMPLETE_GOAL_AFTER_REGISTERED_CORRIDORS')
