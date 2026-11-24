"""Pure current-mailbox sequence contract; no imports of numerical code."""
import math
from context import digest

class Session:
 def __init__(self,freeze_sha,config):
  self.freeze_sha=freeze_sha;self.config=config;self.sequence=0;self.last_native=-1;self.poisoned=False
 def accept(self,envelope):
  assert not self.poisoned,'TEB_SESSION_POISONED_NO_RETRY'
  try:
   assert envelope['sequence']==self.sequence+1,'TEB_QUERY_SEQUENCE'
   assert envelope['source_freeze_sha256']==self.freeze_sha,'TEB_QUERY_SOURCE'
   wire=envelope['wire'];assert digest(wire)==envelope['wire_sha256'],'TEB_QUERY_DIGEST'
   assert wire['schema']=='PHASE_TEB_REAR_AXLE_QUERY_V1'and wire['config']==self.config,'TEB_QUERY_CONFIG'
   native=wire['source_native'];stamp=wire['source_sim_time']
   assert type(native)is int and native>=0 and native>self.last_native and native%10==0,'TEB_QUERY_CURRENT_ORDER'
   assert self.sequence>0 or native==0,'TEB_FIRST_CURRENT_ZERO'
   assert math.isfinite(stamp)and abs(stamp-.01*native)<=1e-8,'TEB_QUERY_CURRENT_CLOCK'
   assert not wire['historical_controls_supplied']and not wire['actor_truth_supplied'],'TEB_QUERY_FORBIDDEN_INPUT'
   assert set(wire['query'])=={'x','y','yaw','goal_x','goal_y','goal_yaw','vx','vy','omega'}
   assert all(type(x)in(int,float)and math.isfinite(x)for x in wire['query'].values())
   assert 0<len(wire['obstacles'])<=4096
   for item in wire['obstacles']:
    assert set(item)=={'x','y','vx','vy','dynamic'}and item['dynamic']==0 and item['vx']==item['vy']==0.
    assert all(type(item[k])in(int,float)and math.isfinite(item[k])for k in ['x','y','vx','vy'])
   self.sequence=envelope['sequence'];self.last_native=native;return wire
  except BaseException:
   self.poisoned=True;raise
 def refuse(self):self.poisoned=True
