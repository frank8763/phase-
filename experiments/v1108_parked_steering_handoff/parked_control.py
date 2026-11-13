"""Explicit single-owner, rear-zero steering mode. Software proposal only."""
import math
import numpy as np
from braking_reserve import Adapter as Original
from kernel import law
class Adapter(Original):
    def compute(self,v,w,measured_v,measured_w,stale=False):
        target=getattr(self,'parked_target',None)
        if target is None:return super().compute(v,w,measured_v,measured_w,stale)
        assert v==0. and w==0. and not stale,'STEERING_ONLY_CANNOT_DRIVE'
        assert abs(measured_v)<=.003 and abs(measured_w)<=.16,'STEERING_ONLY_BODY_NOT_STOPPED'
        assert abs(self.last[2:]).max()<=1e-10,'STEERING_ONLY_REAR_NOT_ZERO'
        assert np.isfinite(target) and abs(target)<=self.center_limit,'STEERING_ONLY_TARGET_LIMIT'
        previous=self.last.copy();rate=np.asarray(self.commands.rate)*self.dt/.08
        lower=np.maximum(self.commands.lower,previous-rate);upper=np.minimum(self.commands.upper,previous+rate)
        assert np.all(lower[2:]<=0.) and np.all(upper[2:]>=0.),'ZERO_REAR_NOT_LEGAL'
        L=self.wheelbase;h=self.track/2;base=law.base
        pair=np.array([base.inverse_steering(previous[0],1,L,h),base.inverse_steering(previous[1],-1,L,h)])
        assert abs(pair[0]-pair[1])<=1e-8,'PREVIOUS_STEERING_COORDINATION'
        delta=math.atan(L*float(pair.mean()));vr=getattr(self,'virtual_rate',.6)
        lo=max(-self.max_curvature,base.inverse_steering(lower[0],1,L,h),base.inverse_steering(lower[1],-1,L,h),math.tan(max(-self.center_limit,delta-vr*self.dt))/L)
        hi=min(self.max_curvature,base.inverse_steering(upper[0],1,L,h),base.inverse_steering(upper[1],-1,L,h),math.tan(min(self.center_limit,delta+vr*self.dt))/L)
        assert lo<=hi+1e-10,'NO_LEGAL_PARKED_STEERING'
        if lo>hi:lo=hi=(lo+hi)/2
        k=float(np.clip(math.tan(target)/L,lo,hi));u=np.r_[base.steering(k,L,h),0.,0.]
        assert self.commands.legal(u) and np.max(abs(u-previous)-rate)<=1e-10,'PARKED_CONTROL_CONTRACT'
        self.last=u.copy();self.integral=0.;self.mode='PARKED_STEERING_ONLY'
        return u
