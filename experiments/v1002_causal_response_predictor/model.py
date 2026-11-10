"""Causal low-order predictor using the same frozen joint-target allocator.

No model factory/physics APIs. This is analytical prediction, not MuJoCo replay.
"""
import copy,importlib.util,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
def load(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fixture=load('v1002_explicit_metadata',R/'experiments/v993_steering_transient_diagnosis/fixture.py')
law=load('v1002_exact_v993_law',R/'experiments/v993_steering_transient_diagnosis/vehicle_control.py')
def virtual(q):
    z=np.tan(np.asarray(q,float));k=(z[0]/(.6+.27*z[0])+z[1]/(.6-.27*z[1]))/2
    return float(math.atan(.6*k))
def virtual_rate(q,qd):
    q=np.asarray(q,float);qd=np.asarray(qd,float);z=np.tan(q)
    k=(z[0]/(.6+.27*z[0])+z[1]/(.6-.27*z[1]))/2
    rates=.6*(1+z*z)*qd/(np.array([.6+.27*z[0],.6-.27*z[1]])**2)
    return float(.6*rates.mean()/(1+(.6*k)**2))

class Predictor:
    def __init__(self,setup,initial,parameters):
        self.p=copy.deepcopy(parameters);self.dt=.01
        self.state=np.asarray(initial['state'],float).copy()
        assert self.state.shape==(8,)and np.isfinite(self.state).all(),'INVALID_INITIAL_PREDICTOR_STATE'
        self.adapter=fixture.make(law.Adapter,setup);self.adapter.last=np.asarray(initial['last_ctrl'],float).copy();self.adapter.integral=float(initial['integral'])
        assert self.adapter.commands.legal(self.adapter.last)
        self.adapter.virtual_rate=float(initial.get('virtual_rate',.6));self.steps=0
    def step(self,v,w,stale=False):
        x,y,yaw,speed,lateral,body_w,delta,delta_rate=self.state
        command=self.adapter.compute(v,w,speed,body_w,stale)
        target=virtual(command[:2]);c=self.p['steering_discrete'];next_rate=c[0]*delta_rate+c[1]*(target-delta)
        next_delta=delta+self.dt*next_rate
        s=self.p['speed_discrete'];next_speed=s[0]*speed+s[1]*float(command[2:].mean())
        mid_speed=(speed+next_speed)/2;mid_delta=(delta+next_delta)/2;curvature=math.tan(mid_delta)/.6
        dyaw=self.p['gain_a']*mid_speed*curvature*self.dt+self.p['steering_rate_b']*(next_delta-delta)
        next_w=self.p['gain_a']*next_speed*math.tan(next_delta)/.6+self.p['steering_rate_b']*next_rate
        lc=self.p['lateral_discrete'];next_lateral=lc[0]*next_speed*math.tan(next_delta)/.6+lc[1]*next_rate
        mid_lateral=(lateral+next_lateral)/2;a=yaw+dyaw/2
        next_x=x+self.dt*(mid_speed*math.cos(a)-mid_lateral*math.sin(a));next_y=y+self.dt*(mid_speed*math.sin(a)+mid_lateral*math.cos(a))
        state=np.array([next_x,next_y,yaw+dyaw,next_speed,next_lateral,next_w,next_delta,next_rate])
        assert np.isfinite(state).all(),'NONFINITE_PREDICTION'
        self.state=state;self.steps+=1
        return state.copy(),command.copy()
