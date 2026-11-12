"""Original .08 branch exact; separately calibrated .125 ARX speed branch."""
import json,math
from pathlib import Path
import numpy as np
from kernel import Predictor as OriginalPredictor,PARAMETERS as ORIGINAL,virtual
P=json.loads((Path(__file__).resolve().parent/'PARAMETERS.json').read_text())
class Predictor(OriginalPredictor):
 def step(self,v,w,stale=False):
  if abs(v-.125)>1e-12 or stale:return super().step(v,w,stale)
  x,y,yaw,speed,lateral,body_w,delta,delta_rate=self.state;command=self.adapter.compute(v,w,speed,body_w,stale);target=virtual(command[:2]);c=self.p['steering_discrete'];nr=c[0]*delta_rate+c[1]*(target-delta);nd=delta+.01*nr;mean=float(command[2:].mean());nv=P['speed_pole']*speed+P['speed_gain']*mean+P['curvature_speed_coefficient']*mean*(math.tan(nd)/.6)**2;mv=(speed+nv)/2;md=(delta+nd)/2;da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-delta);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(lateral+nl)/2;a=yaw+da/2;self.state=np.array([x+.01*(mv*math.cos(a)-ml*math.sin(a)),y+.01*(mv*math.sin(a)+ml*math.cos(a)),yaw+da,nv,nl,nw,nd,nr]);assert np.isfinite(self.state).all();self.steps+=1;return self.state.copy(),command.copy()
