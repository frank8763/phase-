"""One smooth bounded steering-load term; original fast response coefficients."""
from pathlib import Path
from functools import lru_cache
import json
import math
import numpy as np
from runtime import Predictor as Original
from bindings import PARAMETERS as BASE
from kernel import virtual

C=Path(__file__).resolve().parent
SIGMA=.015


def rate_law(delta,rate,speed,target,a,b,k):
    return a*rate+b*(target-delta-k*max(speed,0.)**2*math.tanh(delta/SIGMA))


def validate(p):
    a,b,k=map(float,p['coefficients'])
    assert np.isfinite([a,b,k]).all(),'NONFINITE_PARAMETERS'
    assert [a,b]==BASE['steering_discrete'],'TRANSIENT_PARAMETERS_CHANGED'
    assert 1e-6<k<2.-1e-6 and p['smooth_width_rad']==SIGMA,'LOAD_BOUND_OR_SCALE'
    largest=b*(1+k*.13**2/SIGMA)
    assert 0<a<1 and b>0 and largest<200*(1+a),'SCHUR_SLOPE_CONDITION'
    endpoint=[float(abs(np.linalg.eigvals([[1-.01*x,.01*a],[-x,a]])).max())for x in [b,largest]]
    return a,b,k,max(*endpoint,math.sqrt(a))


@lru_cache(maxsize=1)
def parameters():
    p=json.loads((C/'PARAMETERS.json').read_text());validate(p);return p


class Predictor(Original):
    def __init__(self,setup,origin):
        super().__init__(setup,origin)
        self.a,self.b,self.k,_=validate(parameters())
        assert type(origin.get('steering_load_episode'))is bool,'EXPLICIT_LOAD_EPISODE'
        self.steering_load_episode=origin['steering_load_episode']

    def step(self,v,w,stale=False):
        old=self.state.copy();parked=getattr(self.adapter,'parked_target',None)is not None
        if parked or v<=-.005:self.steering_load_episode=False
        elif v>=.005:self.steering_load_episode=True
        assert abs(v-.125)>1e-12,'HIGH_SPEED_NOT_QUALIFIED'
        s,u=super().step(v,w,stale)
        if not self.steering_load_episode:return s,u
        assert not self.coupled_episode and not parked,'LOAD_MODE_CONFLICT'
        x,y,yaw,speed,lateral,body_w,delta,rate=old;target=virtual(u[:2])
        nr=rate_law(delta,rate,speed,target,self.a,self.b,self.k);nd=delta+.01*nr
        pole,gain=self.p['speed_discrete'];nv=pole*speed+gain*float(u[2:].mean())
        if abs(v-.08)<=1e-12 and not stale:nv+=self.p['curvature_speed_coefficient']*float(u[2:].mean())*(math.tan(nd)/.6)**2
        mv=(speed+nv)/2;md=(delta+nd)/2;dyaw=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-delta)
        nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr
        ml=(lateral+nl)/2;angle=yaw+dyaw/2
        self.state=np.array([x+.01*(mv*math.cos(angle)-ml*math.sin(angle)),y+.01*(mv*math.sin(angle)+ml*math.cos(angle)),yaw+dyaw,nv,nl,nw,nd,nr])
        assert np.isfinite(self.state).all();return self.state.copy(),u
