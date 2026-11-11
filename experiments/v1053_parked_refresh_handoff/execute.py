"""Single actuator owner, fixed hold clock, atomic parked-plan replacement."""
import json,math,os,subprocess,sys,time
from pathlib import Path
import numpy as np
from kernel import C,R,dump,virtual,public_setup
from handoff import hold_permission,publish
HOLD_NATIVE=800;MAX_EPOCHS=16;MAX_NEW_NATIVE=40000
class ProcessJob:
 def __init__(self,folder,payload):
  folder.mkdir(parents=True,exist_ok=False);dump(folder/'INPUT.json',payload);self.folder=folder;self.log=(folder/'console').open('x');self.child=subprocess.Popen([sys.executable,'-B',str(C/'source_job.py'),str(folder)],cwd=R,stdout=self.log,stderr=subprocess.STDOUT)
 def finish(self):
  assert self.child.poll()is not None,'SOURCE_MISSED_FIXED_HOLD_DEADLINE'
  result=json.loads((self.folder/'RESULT.json').read_text());assert self.child.returncode==0 and result['passed'],'SOURCE_PRODUCER_FAILED';return result
 def close(self):
  if self.child.poll()is None:
   self.child.terminate()
   try:self.child.wait(2)
   except subprocess.TimeoutExpired:self.child.kill();self.child.wait(2)
  self.log.close()
def error(v,expected):
 body=np.asarray(v.body());d=body[2]-expected[2];values=dict(position=float(np.linalg.norm(body[:2]-expected[:2])),heading=abs(math.atan2(math.sin(d),math.cos(d))),steering=abs(virtual(v.steering_sample()[:2])-expected[6]));assert values['position']<=.04 and values['heading']<=.035 and values['steering']<=.015,'LOCAL_NATIVE_TRACKING_FAILED';assert abs(body[3])<=.13 and abs(body[4])<=.16,'BODY_CAP';return values
def execute(v,setup,original,end,evidence,out,packet_fn,job_class=ProcessJob,pace=True):
 origin=v.count;active=original;cursor=0;segments=[];adoptions=[];maximum=dict(position=0.,heading=0.,steering=0.);moved=0;pending=[]
 def step(request,expected):
  nonlocal moved
  assert time.time()<end-150 and v.count-origin<MAX_NEW_NATIVE,'EXECUTION_OR_REPLAY_RESERVE';v.step(*request);values=error(v,expected);maximum.update({k:max(maximum[k],values[k])for k in maximum});moved+=int(abs(request[0])>.005)
  if v.count%5==0:evidence.update(v.scan())
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
   fresh=packet_fn(v,True);latest=evidence.source(v);now=time.monotonic();adopted=publish(proposal,fresh,latest,now);adopted['planning_packet']=proposal['packet'];adopted['planning_source']=proposal['source'];adopted['publication_source']=latest;adopted['goal']=original['goal'];pending.append((folder/'ADOPTED_PLAN.json',adopted));adoptions.append(dict(epoch=epoch,start_native=v.count,prefix_packet_tick=packet['native_tick'],published_tick=fresh['native_tick'],wait=adopted['phase_wait_ticks'],source_native_tick=latest['source_native_tick'],next_checkpoint_native=adopted['next_checkpoint_native']));active=adopted;cursor=0;request=np.array(active['planned_body_requests']);states=np.array(active['state_path']);limit=active['next_checkpoint_native'];segment=dict(kind='REQUALIFIED_INPUT',start_native=v.count,executed_native=0,state_path=active['state_path'],adopted_plan=str((folder/'ADOPTED_PLAN.json').relative_to(R)));segments.append(segment)
   assert time.monotonic()-fresh['body_measured_at']<=.05,'PUBLICATION_TO_FIRST_CONTROL_EXPIRED'
   for i in range(limit):
    step(request[i],states[i+1]);segment['executed_native']+=1;cursor+=1
    if v.count%200==0:dump(out/'PARTIAL.json',dict(phase='PARKED_REFRESH_EXECUTION',epoch=epoch,native=v.count,new_native=v.count-origin,epoch_progress=cursor,maximum_local_tracking=maximum))
   for path,row in pending:dump(path,row)
   pending=[];dump(out/'ADOPTIONS.json',adoptions)
   if cursor==len(request):return dict(passed=True,epochs=epoch+1,new_native=v.count-origin,moving_native=moved,maximum_local_tracking=maximum,actual_execution_segments=len(segments))
  raise AssertionError('FIXED_EPOCH_LIMIT')
 finally:
  if segments:segments[-1]['executed_native']=v.count-segments[-1]['start_native']
  for path,row in pending:dump(path,row)
  dump(out/'EXECUTION_SEGMENTS.json',segments);dump(out/'ADOPTIONS.json',adoptions)
