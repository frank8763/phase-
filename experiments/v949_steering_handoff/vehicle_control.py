"""Ackermann feedforward; neutral zero-drive stop; original servo bounds/slew."""
import importlib.util
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('frozen_v856_adapter',ROOT/'experiments/v856_nav2_foundation/vehicle_control.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)


class Adapter(old.Adapter):
    def compute(self,v,w,measured_v,measured_w,stale=False):
        assert np.isfinite([v,w,measured_v,measured_w]).all()
        v=float(np.clip(v,-.15,.30))
        w=float(np.clip(w,-abs(v)*self.max_curvature,abs(v)*self.max_curvature))
        if stale or abs(v)<.005:
            self.integral=0.
            target=np.zeros(4)
        else:
            error=v-measured_v
            self.integral=float(np.clip(self.integral+error*self.dt,-.4,.4))
            mean=float(np.clip(v/self.radius+8.*error+4.*self.integral,-6.,6.))
            # RPP closes pose error outside this adapter. No unqualified inner
            # yaw gain that drives the two steering servos between hard limits.
            delta=math.atan(self.wheelbase*w/v)
            if abs(delta)<1e-10:left=right=0.
            else:
                radius=self.wheelbase/math.tan(abs(delta))
                inside=math.atan(self.wheelbase/(radius-self.track/2))
                outside=math.atan(self.wheelbase/(radius+self.track/2))
                left,right=(inside,outside)if delta>0 else(-outside,-inside)
            diff=w*self.track/(2*self.radius)
            target=np.array([left,right,mean-diff,mean+diff])
        target=np.clip(target,self.commands.lower,self.commands.upper)
        rate=self.commands.rate*self.dt/.08
        command=np.clip(target,self.last-rate,self.last+rate)
        assert self.commands.legal(command) and np.max(abs(command-self.last)-rate)<1e-10
        self.last=command.copy()
        return command
