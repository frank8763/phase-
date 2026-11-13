"""Measured-rest entry and explicitly bounded coupled steering motion."""
import numpy as np
from parked_control import Adapter as Legacy
from kernel import law
import math
STEERING_RATE=.2
MOTION_SPEED_LIMIT=.01
class SteeringModeRefusal(AssertionError):pass
class Adapter(Legacy):
 def compute(self,v,w,measured_v,measured_w,stale=False):
  target=getattr(self,'parked_target',None)
  if target is None:
   u=super().compute(v,w,measured_v,measured_w,stale);self._steering_motion_active=False;return u
  assert v==0. and w==0. and not stale,'STEERING_MOTION_CANNOT_DRIVE'
  if not getattr(self,'_steering_motion_active',False):
   if abs(measured_v)>.003 or abs(measured_w)>.003:raise SteeringModeRefusal('STEERING_ENTRY_NOT_ACTUALLY_REST')
  elif abs(measured_v)>MOTION_SPEED_LIMIT or abs(measured_w)>.16:raise SteeringModeRefusal('STEERING_COUPLED_MOTION_LIMIT')
  assert abs(self.last[2:]).max()<=1e-10,'STEERING_REAR_NOT_ZERO'
  assert np.isfinite(target)and abs(target)<=self.center_limit,'STEERING_TARGET_LIMIT'
  previous=self.last.copy();rate=np.asarray(self.commands.rate)*self.dt/.08
  lower=np.maximum(self.commands.lower,previous-rate);upper=np.minimum(self.commands.upper,previous+rate)
  assert np.all(lower[2:]<=0.)and np.all(upper[2:]>=0.),'ZERO_REAR_NOT_LEGAL'
  L=self.wheelbase;h=self.track/2;base=law.base;pair=np.array([base.inverse_steering(previous[0],1,L,h),base.inverse_steering(previous[1],-1,L,h)])
  assert abs(pair[0]-pair[1])<=1e-8,'PREVIOUS_STEERING_COORDINATION'
  delta=math.atan(L*float(pair.mean()));lo=max(-self.max_curvature,base.inverse_steering(lower[0],1,L,h),base.inverse_steering(lower[1],-1,L,h),math.tan(max(-self.center_limit,delta-STEERING_RATE*self.dt))/L)
  hi=min(self.max_curvature,base.inverse_steering(upper[0],1,L,h),base.inverse_steering(upper[1],-1,L,h),math.tan(min(self.center_limit,delta+STEERING_RATE*self.dt))/L)
  assert lo<=hi+1e-10,'NO_LEGAL_STEERING_MOTION'
  if lo>hi:lo=hi=(lo+hi)/2
  k=float(np.clip(math.tan(target)/L,lo,hi));u=np.r_[base.steering(k,L,h),0.,0.]
  assert self.commands.legal(u)and np.max(abs(u-previous)-rate)<=1e-10,'STEERING_CONTROL_CONTRACT'
  self.last=u.copy();self.integral=0.;self._steering_motion_active=True;self.mode='BOUNDED_COUPLED_STEERING';return u
