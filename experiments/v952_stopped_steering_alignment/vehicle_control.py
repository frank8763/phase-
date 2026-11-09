"""Original moving/braking map; steering alignment only after measured body stop."""
import importlib.util
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v952_frozen_original_adapter',ROOT/'experiments/v856_nav2_foundation/vehicle_control.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
STOP_SPEED=.005
STOP_YAW=.005
STABLE_TICKS=10
STEERING_POSITION=.01
STEERING_RATE=.03


class Adapter(old.Adapter):
    def __init__(self,model,mj,dt=.01,encoders=None):
        super().__init__(model,mj,dt)
        self.encoders=encoders
        self.mode='DRIVING'
        self.stable_ticks=0

    def encoder_ready(self):
        if self.encoders is None:raise ValueError('MEASURED_STEERING_REQUIRED')
        position,velocity=self.encoders()
        position=np.asarray(position,float);velocity=np.asarray(velocity,float)
        if position.shape!=(2,)or velocity.shape!=(2,)or not np.isfinite([*position,*velocity]).all():
            raise ValueError('INVALID_STEERING_ENCODERS')
        return bool(abs(position).max()<=STEERING_POSITION and abs(velocity).max()<=STEERING_RATE)

    def compute(self,v,w,measured_v,measured_w,stale=False):
        if not np.isfinite([v,w,measured_v,measured_w]).all():raise ValueError('NONFINITE_BODY_COMMAND')
        stopping=bool(stale or abs(float(np.clip(v,-.15,.30)))<.005)
        if not stopping:
            if self.mode=='ALIGNING'and not self.encoder_ready():
                raise ValueError('FORWARD_BEFORE_MEASURED_STEERING_ALIGNMENT')
            self.mode='DRIVING';self.stable_ticks=0
            return super().compute(v,w,measured_v,measured_w,stale)

        stopped=abs(measured_v)<=STOP_SPEED and abs(measured_w)<=STOP_YAW
        self.stable_ticks=min(STABLE_TICKS,self.stable_ticks+1)if stopped else 0
        if not stopped:self.mode='BRAKING'
        elif self.stable_ticks>=STABLE_TICKS:self.mode='ALIGNING'
        elif self.mode!='ALIGNING':self.mode='BRAKING'
        previous=self.last.copy()
        command=super().compute(v,w,measured_v,measured_w,stale)
        if self.mode=='ALIGNING':
            rate=self.commands.rate*self.dt/.08
            command[:2]=np.clip(np.zeros(2),previous[:2]-rate[:2],previous[:2]+rate[:2])
            assert self.commands.legal(command)and np.max(abs(command-previous)-rate)<1e-10
            self.last=command.copy()
        return command
