"""The exact production retained-profile executor, separately software-tested."""
import math,time
import numpy as np
from kernel import virtual,dump,predict
def regenerate(setup,packet,plan):
 # V1050 stores its terminal200 explicitly in actions. Never append a second
 # terminal hold when reconstituting the physical entry's exact profile.
 ss,uu,rr,mm=predict(setup,packet,plan['actions'],tail=False)
 assert ss.shape==np.asarray(plan['state_path']).shape
 assert uu.shape==np.asarray(plan['predicted_actuator_controls']).shape
 assert np.max(abs(ss-np.asarray(plan['state_path'])))<=1e-8
 assert np.max(abs(uu-np.asarray(plan['predicted_actuator_controls'])))<=1e-8
 assert np.array_equal(rr,np.asarray(plan['planned_body_requests']))
 return ss,uu,rr,mm
def execute(v,plan,end,evidence=None,out=None):
 ss=np.asarray(plan['state_path']);rr=np.asarray(plan['planned_body_requests']);posmax=headmax=steermax=0.
 assert len(ss)==len(rr)+1 and plan['retained_suffix_audit']['passed']
 for i,request in enumerate(rr):
  assert time.time()<end-150,'PROFILE_REPLAY_TIME_RESERVE'
  v.step(*request);body=np.asarray(v.body());pos=float(np.linalg.norm(body[:2]-ss[i+1,:2]));d=body[2]-ss[i+1,2];head=abs(math.atan2(math.sin(d),math.cos(d)));steer=abs(virtual(v.steering_sample()[:2])-ss[i+1,6]);posmax=max(posmax,pos);headmax=max(headmax,head);steermax=max(steermax,steer)
  assert pos<=.04 and head<=.035 and steer<=.015,'NATIVE_TRACKING_FAILED'
  assert abs(body[3])<=.13 and abs(body[4])<=.16,'BODY_CAP'
  if evidence is not None and v.count%5==0:evidence.update(v.scan())
  if out is not None and v.count%200==0:dump(out/'PARTIAL.json',dict(phase='FULL_TIMED_PROFILE',native=v.count,suffix_native=i+1,maximum_position_m=posmax,maximum_heading_rad=headmax))
 return dict(passed=True,maximum_position_m=posmax,maximum_heading_rad=headmax,maximum_steering_rad=steermax)
