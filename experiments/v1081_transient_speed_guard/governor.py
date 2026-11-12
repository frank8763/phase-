"""One-step speed projection from measured body/front encoders; original limits."""
import math,json,importlib.util
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1081_original_signed_owner',R/'experiments/v1035_signed_timed_input_source/signed_control.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
s=importlib.util.spec_from_file_location('v1081_original_virtual_math',R/'experiments/v1003_causal_recovery_execution/predictor.py');kin=importlib.util.module_from_spec(s);s.loader.exec_module(kin)
P=json.loads((C/'PARAMETERS.json').read_text());STEER=json.loads((R/'experiments/v1079_dual_steering_qualification/PARAMETERS.json').read_text())['front_wheels'];SPEED=json.loads((R/'experiments/v1078_saved_ns_retimed/PARAMETERS.json').read_text())
def speed_terms(speed,front,rates,command):
 nf=np.array(front,float);nr=np.array(rates,float)
 for k,p in enumerate(STEER):nr[k]=p['rate_pole']*nr[k]+p['target_gain']*(command[k]-nf[k])
 nf+=.01*nr;delta=kin.virtual(front);rate=kin.virtual_rate(front,rates);features=np.array([delta*rate,rate*rate,speed*(math.tan(delta)/.6)**2]);extra=float(features@np.asarray(P['transient_coefficients']));gain=SPEED['speed_gain']+SPEED['curvature_speed_coefficient']*(math.tan(kin.virtual(nf))/.6)**2;assert gain>0,'NONPOSITIVE_SPEED_GAIN';offset=SPEED['speed_pole']*speed+extra;return offset,gain,nf,nr
class Adapter(base.Adapter):
 def compute(self,v,w,measured_v,measured_w,stale=False):
  previous=self.last.copy();old_integral=self.integral;u=super().compute(v,w,measured_v,measured_w,stale)
  if abs(v-.125)>1e-12 or stale:return u
  assert callable(self.encoders),'MEASURED_FRONT_REQUIRED';enc=np.asarray(self.encoders(),float);assert enc.shape==(4,)and np.isfinite(enc).all(),'BAD_FRONT_SAMPLE';offset,gain,_,_=speed_terms(measured_v,enc[:2],enc[2:],u);target=(P['projected_speed_cap']-offset-P['empirical_one_step_error_reserve'])/gain;rate=np.asarray(self.commands.rate,float)*self.dt/.08;lower=np.maximum(np.asarray(self.commands.lower,float),previous-rate);upper=np.minimum(np.asarray(self.commands.upper,float),previous+rate);k=(base.base.inverse_steering(u[0],1,self.wheelbase,self.track/2)+base.base.inverse_steering(u[1],-1,self.wheelbase,self.track/2))/2;factors=np.array([1-self.track/2*k,1+self.track/2*k]);lo=max(0.,float(np.max(lower[2:]/factors)));hi=min(float(u[2:].mean()),float(np.min(upper[2:]/factors)),max(0.,target));feasible=lo<=hi+1e-10
  assert feasible,'NO_SLEW_LEGAL_SPEED_PROJECTION';m=float(np.clip(u[2:].mean(),lo,hi));u[2:]=m*factors;limited=m<float(self.last[2:].mean())-1e-12
  if limited:self.integral=min(old_integral,self.integral)
  assert self.commands.legal(u)and np.max(abs(u-previous)-rate)<=1e-10,'PROJECTED_CONTROL_CONTRACT';assert offset+gain*m+P['empirical_one_step_error_reserve']<=P['projected_speed_cap']+1e-10,'PROJECTED_SPEED_BOUND';self.last=u.copy();self.last_speed_projection=dict(offset=offset,gain=gain,common=m,limited=limited,reserve=P['empirical_one_step_error_reserve']);return u
