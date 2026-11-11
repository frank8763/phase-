"""Zero-copy publish-to-command path; parked asynchronous refresh executor."""
import json,math,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from kernel import C,R,dump,virtual,public_setup,load
from handoff import hold_permission
from atomic import allocate,publish
previous=load('v1054_original_job_owner',R/'experiments/v1053_parked_refresh_handoff/execute.py')
ProcessJob=previous.ProcessJob;HOLD_NATIVE=800;MAX_EPOCHS=16;MAX_NEW_NATIVE=40000
# ProcessJob uses kernel.C from this process's canonical module. It launches
# this version's source_job, never a physical entry or another model owner.
def error(v,expected):return previous.error(v,expected)
def execute(v,setup,original,end,evidence,out,packet_fn,job_class=ProcessJob,pace=True):
 origin=v.count;active=original;cursor=0;segments=[];adoptions=[];maximum=dict(position=0.,heading=0.,steering=0.);moved=0;pending=[];critical=[]
 def step(request,expected):
  nonlocal moved
  assert time.time()<end-150 and v.count-origin<MAX_NEW_NATIVE,'EXECUTION_OR_REPLAY_RESERVE';v.step(*request);values=error(v,expected);maximum.update({k:max(maximum[k],values[k])for k in maximum});moved+=int(abs(request[0])>.005)
  if v.count%5==0:evidence.update(v.scan())
 def save_pending():
  nonlocal pending
  for path,view,segment in pending:
   record=view.record();record['goal']=original['goal'];segment['state_path']=record['state_path'];dump(path,record)
  pending=[]
 try:
  for epoch in range(MAX_EPOCHS):
   packet=packet_fn(v,True);source=evidence.source(v);permission=hold_permission(setup,packet,source);holder=dict(kind='CERTIFIED_PARKED_HOLD',start_native=v.count,executed_native=0,state_path=permission['states'],minimum_raw_m=permission['minimum_raw_m'],planning_packet=packet,planning_source=source);segments.append(holder);job=None;folder=out/'refresh'/('epoch%02d'%epoch)
   try:
    job=job_class(folder,dict(setup=public_setup(setup),packet=packet,source=source,goal=original['goal'],actions=active['actions'],elapsed=cursor))
    for i in range(HOLD_NATIVE):
     step([0.,0.,False],np.array(permission['states'][i+1]));holder['executed_native']+=1
     if pace:time.sleep(.01)
    proposal=job.finish()
   finally:
    if job is not None:job.close()
   buffers=allocate(proposal)  # all large conversion BEFORE fresh measurement
   fresh=packet_fn(v,True);latest=evidence.source(v);now=time.monotonic();view=publish(buffers,fresh,latest,now);limit=view.checkpoint;segment=dict(kind='REQUALIFIED_INPUT',start_native=v.count,executed_native=0,state_path=None,adopted_plan=str((folder/'ADOPTED_PLAN.json').relative_to(R)));segments.append(segment);pending.append((folder/'ADOPTED_PLAN.json',view,segment));cursor=0
   elapsed=time.monotonic()-fresh['body_measured_at'];critical.append(elapsed);assert elapsed<=.05,'PUBLICATION_TO_FIRST_CONTROL_EXPIRED'
   for i in range(limit):
    step(view.request(i),view.state(i+1));segment['executed_native']+=1;cursor+=1
    if v.count%200==0:dump(out/'PARTIAL.json',dict(phase='ATOMIC_PARKED_REFRESH_EXECUTION',epoch=epoch,native=v.count,new_native=v.count-origin,epoch_progress=cursor,maximum_local_tracking=maximum,maximum_publish_to_control_s=max(critical)))
   # Serialization only at the next actual stopped boundary, after first and
   # all remaining control ticks. The saved values exactly match the views.
   active=view.record();active['goal']=original['goal'];save_pending();adoptions.append(dict(epoch=epoch,start_native=segment['start_native'],prefix_packet_tick=packet['native_tick'],published_tick=fresh['native_tick'],wait=view.wait,source_native_tick=latest['source_native_tick'],next_checkpoint_native=limit,publish_to_first_control_s=elapsed));dump(out/'ADOPTIONS.json',adoptions)
   if cursor==view.native_steps:return dict(passed=True,epochs=epoch+1,new_native=v.count-origin,moving_native=moved,maximum_local_tracking=maximum,actual_execution_segments=len(segments),maximum_publish_to_control_s=max(critical))
  raise AssertionError('FIXED_EPOCH_LIMIT')
 finally:
  if segments:segments[-1]['executed_native']=v.count-segments[-1]['start_native']
  save_pending();dump(out/'EXECUTION_SEGMENTS.json',segments);dump(out/'ADOPTIONS.json',adoptions)
