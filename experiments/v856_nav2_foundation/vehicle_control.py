"""Body-Twist to native Ackermann servos, no obstacle or target truth input.

Fixed engineering design: measured body velocity PI wheel feedforward, Ackermann
curvature clipping, measured yaw P feedback, and original per-second actuator slew.
No learned network changes and no vehicle root-position assistance.
"""
import math
import numpy as np
class Adapter:
    def __init__(self,model,mj,dt=.01):
        from actuator_commands import CommandMap
        self.commands=CommandMap(model,mj);self.dt=dt;self.last=np.zeros(4);self.integral=0.
        self.wheelbase=.60;self.track=.54;self.radius=.12;self.center_limit=.42722137342572125
        self.max_curvature=math.tan(self.center_limit)/self.wheelbase
    def compute(self,v,w,measured_v,measured_w,stale=False):
        assert np.isfinite([v,w,measured_v,measured_w]).all()
        v=float(np.clip(v,-.15,.30));w=float(np.clip(w,-abs(v)*self.max_curvature,abs(v)*self.max_curvature))
        if stale or abs(v)<.005:
            self.integral=0.;target=self.last.copy();target[2:]=0.
        else:
            error=v-measured_v;self.integral=float(np.clip(self.integral+error*self.dt,-.4,.4))
            mean=float(np.clip(v/self.radius+8.*error+4.*self.integral,-6.,6.))
            desired_w=float(np.clip(w+1.5*(w-measured_w),-abs(v)*self.max_curvature,abs(v)*self.max_curvature))
            delta=math.atan(self.wheelbase*desired_w/v)
            if abs(delta)<1e-10:left=right=0.
            else:
                radius=self.wheelbase/math.tan(abs(delta));inside=math.atan(self.wheelbase/(radius-self.track/2));outside=math.atan(self.wheelbase/(radius+self.track/2))
                left,right=(inside,outside)if delta>0 else(-outside,-inside)
            diff=desired_w*self.track/(2*self.radius)
            target=np.array([left,right,mean-diff,mean+diff])
        target=np.clip(target,self.commands.lower,self.commands.upper);rate=self.commands.rate*self.dt/.08
        command=np.clip(target,self.last-rate,self.last+rate)
        assert self.commands.legal(command) and np.max(abs(command-self.last)-rate)<1e-10
        self.last=command.copy();return command
