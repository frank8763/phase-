"""Signed joint Ackermann allocation, with zero-rear and measured-rest handoff.

Forward branch is delegated byte-for-byte to V993. Reverse mirrors the rear
common-speed allocation; steering and all actuator/rate bounds are unchanged.
This is an analytical candidate until independent physical qualification.
"""
import importlib.util,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1035_original_v993_allocator',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
class Adapter(base.Adapter):
 def compute(self,v,w,measured_v,measured_w,stale=False):
  assert np.isfinite([v,w,measured_v,measured_w]).all()and np.isfinite(self.last).all()and np.isfinite(self.integral),'NONFINITE_COMMAND_OR_MEMORY'
  v=float(np.clip(v,-.15,.30));w=float(np.clip(w,-abs(v)*self.max_curvature,abs(v)*self.max_curvature));braking=bool(stale or abs(v)<.005);previous=self.last.copy();mean=float(previous[2:].mean())
  if (not braking and v>0)or(braking and mean>=-1e-10):
   assert mean>=-1e-10,'FORWARD_BEFORE_COMPLETE_REVERSE_STOP'
   if not braking and mean<=1e-10:assert measured_v>=-.003,'FORWARD_GEAR_REQUIRES_ACTUAL_REST'
   return super().compute(v,w,measured_v,measured_w,stale)
  assert self.commands.legal(previous)and np.max(previous[2:])<=1e-10,'REVERSE_BEFORE_COMPLETE_FORWARD_STOP'
  if not braking and abs(previous[2:]).max()<=1e-10:assert abs(measured_v)<=.003,'REVERSE_GEAR_REQUIRES_ACTUAL_REST'
  rate=np.asarray(self.commands.rate,float)*self.dt/.08;lower=np.maximum(np.asarray(self.commands.lower,float),previous-rate);upper=np.minimum(np.asarray(self.commands.upper,float),previous+rate);h=self.track/2;L=self.wheelbase
  pk_pair=np.array([base.inverse_steering(previous[0],1,L,h),base.inverse_steering(previous[1],-1,L,h)]);pk=float(pk_pair.mean());assert abs(pk_pair[0]-pk_pair[1])<=1e-8 and abs(pk)<=self.max_curvature+1e-9,'PREVIOUS_FRONT_COORDINATION'
  assert np.max(abs(mean*np.array([1-h*pk,1+h*pk])-previous[2:]))<=1e-8,'PREVIOUS_REAR_COORDINATION'
  # Solve in positive magnitudes, then apply the negative gear sign once.
  l=np.maximum(-upper[2:],0.);u=-lower[2:];assert np.all(l<=u+1e-12),'EMPTY_REVERSE_MAGNITUDE_BOX'
  klo=max(-self.max_curvature,base.inverse_steering(lower[0],1,L,h),base.inverse_steering(lower[1],-1,L,h));khi=min(self.max_curvature,base.inverse_steering(upper[0],1,L,h),base.inverse_steering(upper[1],-1,L,h));delta=math.atan(L*pk);vr=getattr(self,'virtual_rate',.6)
  klo=max(klo,math.tan(max(-self.center_limit,delta-vr*self.dt))/L);khi=min(khi,math.tan(min(self.center_limit,delta+vr*self.dt))/L)
  l0,l1=map(float,l);u0,u1=map(float,u)
  if l0+u1>0:khi=min(khi,(u1-l0)/(h*(l0+u1)))
  if l1+u0>0:klo=max(klo,(l1-u0)/(h*(l1+u0)))
  khi=min(khi,(1-l0/base.MAX_COMMON)/h);klo=max(klo,(l1/base.MAX_COMMON-1)/h);assert klo<=khi+1e-10,'NO_REVERSE_JOINT_ALLOCATION'
  if klo>khi:klo=khi=(klo+khi)/2
  if braking:wanted=pk;integral=0.;common=0.
  else:
   error=abs(v)+float(measured_v);integral=float(np.clip(self.integral+error*self.dt,-.4,.4));common=float(np.clip(abs(v)/self.radius+8*error+4*integral,0.,base.MAX_COMMON));desired=float(np.clip(w,-base.MAX_EQUIVALENT_YAW,base.MAX_EQUIVALENT_YAW));wanted=float(np.clip(desired/v,-self.max_curvature,self.max_curvature))
  k=float(np.clip(wanted,klo,khi));factors=np.array([1-h*k,1+h*k]);lo=max(0.,float(np.max(l/factors)));hi=min(base.MAX_COMMON,float(np.min(u/factors)));assert lo<=hi+1e-10,'EMPTY_REVERSE_COMMON_INTERVAL'
  if lo>hi:lo=hi=(lo+hi)/2
  m=float(np.clip(common,lo,hi));front=previous[:2].copy()if braking else base.steering(k,L,h);command=np.r_[front,-m*factors]
  assert self.commands.legal(command)and np.max(abs(command-previous)-rate)<=1e-10,'REVERSE_CONTROL_CONTRACT'
  if braking:assert abs(k-pk)<=1e-9,'REVERSE_BRAKE_STEERING_CHANGED'
  self.last=command.copy();self.integral=integral;self.mode='REVERSE_COORDINATED_BRAKE'if braking else'REVERSE_COORDINATED_ALLOCATION';self.last_allocation_proof=dict(analytical_only=True,physical_response_qualified=False,gear=-1,braking=braking,curvature=k,common=-m,selected=command.tolist())
  return command
