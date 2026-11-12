"""Preview the next at-most-five requests and their complete 2200-stop tail.

This is an additional static admission gate. A failed preview requests a
separately certified current-state stop; it never grants an unsafe command.
"""
import math
import numpy as np
from kernel import initial,Expander,PARAMETERS,REQUIRED
from planner import library

class Reserve:
 def __init__(self,setup,use_wide_reserve=True):
  self.setup=setup;self.use_wide_reserve=use_wide_reserve;self.armed=False;self.lib=library();self.engine=Expander(setup);self.rect=np.ascontiguousarray(setup['known']['known_rectangles'],float);self.circles=np.ascontiguousarray(setup['known']['known_circles'],float);self.limits=np.ascontiguousarray(setup['limits'],float);self.rates=np.ascontiguousarray(setup['slew_per_second'],float);p=PARAMETERS;self.parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']],float)
 def stop(self,state,memory):
  return self.lib.stop_lower(np.ascontiguousarray(state,float),np.ascontiguousarray(memory,float),self.limits,self.rates,self.parameters,self.rect,len(self.rect),self.circles,len(self.circles),2200)
 def check(self,packet,requests):
  requests=np.asarray(requests,float);assert requests.ndim==2 and requests.shape[1]==3 and 0<len(requests)<=5 and not requests[:,2].any(),'BRAKE_PREVIEW_REQUEST_CONTRACT'
  origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];current=self.stop(state,memory);minimum=current
  for v,w,stale in requests:
   target=0. if v==0 else math.atan(.6*w/v);states,controls,mem=self.engine.expand(state,memory,np.array([target]),1,np.array([v]));state=states[0,-1];memory=mem[0];minimum=min(minimum,self.lib.static_pose(*state[:3],self.rect,len(self.rect),self.circles,len(self.circles)))
  future=self.stop(state,memory);minimum=min(minimum,future)
  if self.use_wide_reserve and current>=REQUIRED+.02:self.armed=True
  extra=.02 if self.armed else min(.001,max(0.,current-REQUIRED)/2)
  return dict(passed=bool(current>=REQUIRED and minimum>=REQUIRED+extra),current_stop_passed=bool(current>=REQUIRED),current_stop_minimum_raw_m=float(current),preview_stop_minimum_raw_m=float(minimum),required_raw_m=REQUIRED,additional_preview_reserve_m=float(extra),wider_reserve_latched=self.armed,preview_native=len(requests),complete_stop_native=2200,models=0,integrations=0)
