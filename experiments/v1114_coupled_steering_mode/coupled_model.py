"""One scalar longitudinal coupling only during a rear-zero steering episode."""
import json,math
import numpy as np
from prediction import Predictor as Original,initial as original_initial
from common import C
from coupled_control import Adapter
GAIN=json.loads((C/'COUPLING.json').read_text())['rear_zero_steering_gain']
def initial(packet):
 origin=original_initial(packet);origin['state'][4]=float(packet.get('body_lateral',0.));origin['coupled_episode']=bool(packet.get('coupled_episode',False));return origin
class Predictor(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.adapter.__class__=Adapter;self.coupled_episode=bool(args[1].get('coupled_episode',False))
 def step(self,v,w,stale=False):
  old=self.state.copy();mode=getattr(self.adapter,'parked_target',None)is not None
  if mode:self.coupled_episode=True
  if abs(v)>=.005:self.coupled_episode=False
  s,u=super().step(v,w,stale)
  if not self.coupled_episode:return s,u
  assert np.max(abs(u[2:]))<=1e-10,'COUPLING_ONLY_REAR_ZERO'
  x,y,yaw,speed,lateral,body_w,delta,delta_rate=old;nd,nr=s[6:];nv=s[3]+GAIN*math.sin((delta+nd)/2)*nr;mv=(speed+nv)/2;md=(delta+nd)/2
  da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-delta);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(lateral+nl)/2;a=yaw+da/2
  self.state=np.array([x+.01*(mv*math.cos(a)-ml*math.sin(a)),y+.01*(mv*math.sin(a)+ml*math.cos(a)),yaw+da,nv,nl,nw,nd,nr]);assert np.isfinite(self.state).all();return self.state.copy(),u
