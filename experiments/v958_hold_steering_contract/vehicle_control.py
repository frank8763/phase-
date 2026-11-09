"""Proposed separation: moving kinematics plus steering-hold braking. No authority."""
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v958_kinematic_map',ROOT/'experiments/v949_steering_handoff/vehicle_control.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


class Adapter(base.Adapter):
    def __init__(self,model,mj,dt=.01,encoders=None):
        super().__init__(model,mj,dt);self.mode='DRIVING';self.encoders=encoders
    def compute(self,v,w,measured_v,measured_w,stale=False):
        if not np.isfinite([v,w,measured_v,measured_w]).all():raise ValueError('NONFINITE_BODY_COMMAND')
        if not(stale or abs(float(np.clip(v,-.15,.30)))<.005):
            self.mode='DRIVING';return super().compute(v,w,measured_v,measured_w,stale)
        self.mode='BRAKING_HOLD';self.integral=0.
        target=self.last.copy();target[2:]=0.;rate=self.commands.rate*self.dt/.08
        command=np.clip(target,self.last-rate,self.last+rate)
        assert self.commands.legal(command)and np.max(abs(command-self.last)-rate)<1e-10
        self.last=command.copy();return command
