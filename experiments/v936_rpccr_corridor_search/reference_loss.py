"""Causal RP-CCR reference-loss trigger; no dependence on rejected nonzero Twist."""
import math
from dataclasses import dataclass,field

@dataclass
class ReferenceLoss:
 minimum_failures:int=3
 stall_s:float=1.5
 last_success:float|None=None
 failures:list=field(default_factory=list)
 poses:list=field(default_factory=list)
 last_nonzero:float|None=None
 mode:str='NORMAL'
 def route(self,at,passed):
  assert math.isfinite(at)
  if passed:self.last_success=at;self.failures=[]
  else:self.failures.append(at)
 def command(self,at,v,w):
  assert all(math.isfinite(x)for x in[at,v,w])
  if abs(v)>.005 or abs(w)>1e-6:self.last_nonzero=at
 def observe(self,packet,source,now):
  assert packet['native_tick']>=source['source_native_tick'],'FUTURE_RECOVERY_SOURCE'
  assert 0<=now-packet['body_measured_at']<=.2 and 0<=source['source_age_s']<=.2,'STALE_RECOVERY_SOURCE'
  body=packet['body'];assert all(math.isfinite(x)for x in body)
  self.poses.append((now,float(body[0]),float(body[1])))
  self.poses=[p for p in self.poses if p[0]>=now-self.stall_s-.2]
  span=now-self.poses[0][0]if self.poses else 0.
  movement=max((math.hypot(x-self.poses[0][1],y-self.poses[0][2])for t,x,y in self.poses),default=0.)
  no_reference=len(self.failures)>=self.minimum_failures and(self.last_success is None or now-self.last_success>=self.stall_s)
  stopped=abs(body[3])<=.03 and abs(body[4])<=.03
  silence=self.last_nonzero is None or now-self.last_nonzero>=self.stall_s
  trigger=self.mode=='NORMAL'and source.get('support_bounds')is not None and no_reference and stopped and span>=self.stall_s-1e-8 and movement<.02 and silence
  if trigger:self.mode='CANCEL_NORMAL_REFERENCE'
  return dict(triggered=trigger,mode=self.mode,failed_reference_count=len(self.failures),observed_stall_s=span,observed_motion_m=movement,normal_reference_age_s=None if self.last_success is None else now-self.last_success,body_native_tick=packet['native_tick'],source_native_tick=source['source_native_tick'],zero_request_is_not_motion_permission=True)
