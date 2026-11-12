"""Transactional wheel allocation with empirical complete-braking speed preview.

No physical/state writes. Braking preview uses original actuator slew and the
qualified zero-input ARX response; its error reserve remains empirical.
"""
import copy,math,importlib.util,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
signed=load('reserve_original_signed',R/'experiments/v1035_signed_timed_input_source/signed_control.py')
old=load('reserve_old_one_step_math',R/'experiments/v1081_transient_speed_guard/governor.py')
from kernel import PARAMETERS
HARD_SPEED=.13
ERROR_RESERVE=.002
PREVIEW=128
POLE,GAIN=map(float,PARAMETERS['speed_discrete'])
POW=POLE**np.arange(PREVIEW+1)
assert 0<POLE<1 and ERROR_RESERVE/(1-POLE)<.03

def braking_upper(speed,offset,gain,mean,factors,rear_rate):
 """Current candidate once, then fastest legal coordinated steering-hold stop."""
 decrement=float(np.min(rear_rate/factors));assert decrement>0
 first=offset+gain*mean+ERROR_RESERVE
 future_mean=np.maximum(0.,mean-decrement*np.arange(1,PREVIEW+1))
 future=POW[1:]*first+GAIN*np.convolve(future_mean,POW[:-1])[:PREVIEW]+ERROR_RESERVE*(1-POW[1:])/(1-POLE)
 assert future_mean[-1]==0.,'PREVIEW_DOES_NOT_REACH_ZERO_REAR'
 peak=max(float(speed),first,float(future.max()),ERROR_RESERVE/(1-POLE))
 return peak,first,float(future[-1])

class Adapter(signed.Adapter):
 def _candidate(self,v,w,mv,mw,stale,enc,guarded):
  shadow=copy.copy(self);shadow.last=self.last.copy()
  command=signed.Adapter.compute(shadow,v,w,mv,mw,stale)
  if not guarded:return shadow,command,None
  previous=self.last;rate=np.asarray(self.commands.rate,float)*self.dt/.08
  lower=np.maximum(np.asarray(self.commands.lower,float),previous-rate)
  upper=np.minimum(np.asarray(self.commands.upper,float),previous+rate)
  curvature=(signed.base.inverse_steering(command[0],1,self.wheelbase,self.track/2)+signed.base.inverse_steering(command[1],-1,self.wheelbase,self.track/2))/2
  factors=np.array([1-self.track/2*curvature,1+self.track/2*curvature])
  lo=max(0.,float(np.max(lower[2:]/factors)))
  hi=min(float(command[2:].mean()),float(np.min(upper[2:]/factors)))
  assert lo<=hi+1e-10,'EMPTY_BASE_COMMON_INTERVAL'
  if abs(v-.125)<=1e-12 and not stale:offset,gain,_,_=old.speed_terms(mv,enc[:2],enc[2:],command)
  else:offset=POLE*mv;gain=GAIN
  def envelope(m):return braking_upper(mv,offset,gain,m,factors,rate[2:])
  low_peak=envelope(lo)[0]
  if low_peak>HARD_SPEED+1e-12:return None,None,dict(feasible=False,minimum_peak=low_peak,common_lower=lo,common_upper=hi)
  nominal=hi
  if envelope(hi)[0]>HARD_SPEED:
   for _ in range(22):
    mid=(lo+hi)/2
    if envelope(mid)[0]<=HARD_SPEED:lo=mid
    else:hi=mid
   mean=lo
  else:mean=hi
  command[2:]=mean*factors;limited=mean<nominal-1e-12
  if limited:shadow.integral=min(self.integral,shadow.integral)
  assert self.commands.legal(command)and np.max(abs(command-previous)-rate)<=1e-10,'SLEW_OR_AMPLITUDE_CHANGED'
  peak,first,end=envelope(mean);assert peak<=HARD_SPEED+1e-10
  shadow.last=command.copy();proof=dict(feasible=True,limited=limited,maximum_braking_speed_upper=peak,next_speed_upper=first,end_speed_upper=end,common=mean,nominal_common=nominal,preview_native=PREVIEW,error_reserve=ERROR_RESERVE,hard_speed=HARD_SPEED,empirical_not_universal=True)
  return shadow,command,proof
 def compute(self,v,w,measured_v,measured_w,stale=False):
  guarded=bool(getattr(self,'_speed_episode',False)or abs(v-.125)<=1e-12)
  if guarded:
   assert callable(self.encoders),'MEASURED_ENCODERS_REQUIRED'
   enc=np.asarray(self.encoders(),float).copy();assert enc.shape==(4,)and np.isfinite(enc).all(),'BAD_ENCODER_SAMPLE'
  else:enc=None
  shadow,u,proof=self._candidate(v,w,measured_v,measured_w,stale,enc,guarded)
  mode='NOMINAL'
  if shadow is None:
   shadow,u,backup=self._candidate(0.,0.,measured_v,measured_w,False,enc,guarded);mode='CERTIFIED_SPEED_BRAKE'
   if shadow is None:raise AssertionError('NO_SPEED_SAFE_SLEW_LEGAL_COMMAND')
   proof.update(backup_selected=True,backup=backup);proof['maximum_braking_speed_upper']=backup['maximum_braking_speed_upper']
  # Commit only an accepted result. Rejected proposals leave all memory intact.
  self.last=u.copy();self.integral=shadow.integral;self.mode=shadow.mode
  self.last_allocation_proof=copy.deepcopy(shadow.last_allocation_proof)
  self.last_braking_reserve=proof;self.reserve_mode=mode;self._speed_episode=guarded
  return u.copy()
