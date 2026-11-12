"""Dual-front measured-coordinate predictor; actuator owner remains unchanged."""
import json,math,importlib.util
from pathlib import Path
import numpy as np
from kernel import Predictor as Legacy,PARAMETERS,initial as old_initial,virtual
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1079_old_virtual_math',R/'experiments/v1003_causal_recovery_execution/predictor.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
STEER=json.loads((C/'PARAMETERS.json').read_text())['front_wheels'];SPEED=json.loads((R/'experiments/v1078_saved_ns_retimed/PARAMETERS.json').read_text())
def initial(packet):
 x=old_initial(packet);x['front_position']=packet['steering']['position'];x['front_velocity']=packet['steering']['velocity'];return x
class Predictor(Legacy):
 def __init__(self,setup,origin,parameters=PARAMETERS):
  super().__init__(setup,origin,parameters);self.front=np.asarray(origin.get('front_position',[0.,0.]),float).copy();self.front_rate=np.asarray(origin.get('front_velocity',[0.,0.]),float).copy();self.high_speed_episode=False
 def step(self,v,w,stale=False):
  if not self.high_speed_episode and abs(v-.125)>1e-12:return super().step(v,w,stale)
  self.high_speed_episode=True;x,y,yaw,speed,lateral,body_w,delta,delta_rate=self.state;command=self.adapter.compute(v,w,speed,body_w,stale)
  for k,p in enumerate(STEER):self.front_rate[k]=p['rate_pole']*self.front_rate[k]+p['target_gain']*(command[k]-self.front[k])
  self.front+=.01*self.front_rate;nd=virtual(self.front);nr=m.virtual_rate(self.front,self.front_rate);mean=float(command[2:].mean());pole,gain=self.p['speed_discrete'];coef=0.
  if abs(v-.125)<=1e-12 and not stale:pole=SPEED['speed_pole'];gain=SPEED['speed_gain'];coef=SPEED['curvature_speed_coefficient']
  elif abs(v-.08)<=1e-12 and not stale:coef=self.p['curvature_speed_coefficient']
  nv=pole*speed+gain*mean+coef*mean*(math.tan(nd)/.6)**2;mv=(speed+nv)/2;md=(delta+nd)/2;da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-delta);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(lateral+nl)/2;a=yaw+da/2;self.state=np.array([x+.01*(mv*math.cos(a)-ml*math.sin(a)),y+.01*(mv*math.sin(a)+ml*math.cos(a)),yaw+da,nv,nl,nw,nd,nr]);assert np.isfinite(self.state).all()and np.isfinite(self.front).all();self.steps+=1;return self.state.copy(),command.copy()
