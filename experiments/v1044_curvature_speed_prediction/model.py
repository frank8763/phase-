"""One curvature-speed term for qualified-domain proposal; original allocator."""
import importlib.util,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1044_original_predictor',R/'experiments/v1003_causal_recovery_execution/predictor.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
virtual=base.virtual;virtual_rate=base.virtual_rate
class Predictor(base.Predictor):
 def __init__(self,setup,initial,parameters):
  assert np.isfinite(parameters["curvature_speed_coefficient"]) and -.02<parameters["curvature_speed_coefficient"]<0.,"INVALID_CURVATURE_SPEED_COEFFICIENT"
  assert parameters["curvature_speed_domain_m_s"]==.08,"INVALID_CURVATURE_SPEED_DOMAIN"
  super().__init__(setup,initial,parameters)
 def step(self,v,w,stale=False):
  if abs(v-.08)>1e-12 or stale:return super().step(v,w,stale)
  x,y,yaw,speed,lateral,body_w,delta,delta_rate=self.state;command=self.adapter.compute(v,w,speed,body_w,stale);target=virtual(command[:2]);c=self.p['steering_discrete'];nr=c[0]*delta_rate+c[1]*(target-delta);nd=delta+.01*nr;s=self.p['speed_discrete'];nv=s[0]*speed+s[1]*float(command[2:].mean())
  if abs(v-.08)<=1e-12 and not stale:nv+=self.p['curvature_speed_coefficient']*float(command[2:].mean())*(math.tan(nd)/.6)**2
  mv=(speed+nv)/2;md=(delta+nd)/2;da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-delta);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(lateral+nl)/2;a=yaw+da/2
  self.state=np.array([x+.01*(mv*math.cos(a)-ml*math.sin(a)),y+.01*(mv*math.sin(a)+ml*math.cos(a)),yaw+da,nv,nl,nw,nd,nr]);assert np.isfinite(self.state).all();self.steps+=1;return self.state.copy(),command.copy()
