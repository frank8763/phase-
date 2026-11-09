"""Kinematic moving map, measured brake, latched alignment with traction yaw damping.

Requires the existing independently commanded rear traction joints. This is an
engineering component candidate, not a qualified reachability/safety guarantee.
"""
import importlib.util
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v955_original_adapter',ROOT/'experiments/v856_nav2_foundation/vehicle_control.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
STOP_SPEED=.005
STOP_YAW=.005
STABLE_TICKS=10
ALIGN_RATE=.60
ALIGN_BODY_YAW=.03
ALIGN_BODY_SPEED=.03
YAW_DAMPING=4.
MAX_REAR_CORRECTION=.40


class Adapter(old.Adapter):
    def __init__(self,model,mj,dt=.01,encoders=None):
        super().__init__(model,mj,dt)
        self.encoders=encoders;self.mode='DRIVING';self.stable_ticks=0

    def encoder_ready(self):
        if self.encoders is None:raise ValueError('MEASURED_STEERING_REQUIRED')
        position,velocity=(np.asarray(a,float)for a in self.encoders())
        if position.shape!=(2,)or velocity.shape!=(2,)or not np.isfinite([*position,*velocity]).all():
            raise ValueError('INVALID_STEERING_ENCODERS')
        return bool(abs(position).max()<=.01 and abs(velocity).max()<=.03)

    def compute(self,v,w,measured_v,measured_w,stale=False):
        if not np.isfinite([v,w,measured_v,measured_w]).all():raise ValueError('NONFINITE_BODY_COMMAND')
        v=float(np.clip(v,-.15,.30));w=float(np.clip(w,-abs(v)*self.max_curvature,abs(v)*self.max_curvature))
        stopping=stale or abs(v)<.005
        if not stopping:
            if self.mode in {'ALIGNING','READY'} and not self.encoder_ready():
                raise ValueError('MOTION_BEFORE_MEASURED_STEERING_ALIGNMENT')
            self.mode='DRIVING';self.stable_ticks=0
            error=v-measured_v;self.integral=float(np.clip(self.integral+error*self.dt,-.4,.4))
            mean=float(np.clip(v/self.radius+8.*error+4.*self.integral,-6.,6.))
            delta=math.atan(self.wheelbase*w/v)
            if abs(delta)<1e-10:left=right=0.
            else:
                radius=self.wheelbase/math.tan(abs(delta))
                inside=math.atan(self.wheelbase/(radius-self.track/2));outside=math.atan(self.wheelbase/(radius+self.track/2))
                left,right=(inside,outside)if delta>0 else(-outside,-inside)
            diff=w*self.track/(2*self.radius)
            target=np.array([left,right,mean-diff,mean+diff])
        else:
            self.integral=0.
            stopped=abs(measured_v)<=STOP_SPEED and abs(measured_w)<=STOP_YAW
            self.stable_ticks=min(STABLE_TICKS,self.stable_ticks+1)if stopped else 0
            if self.mode not in {'ALIGNING','READY'}:
                self.mode='ALIGNING'if self.stable_ticks>=STABLE_TICKS else'BRAKING'
            target=self.last.copy();target[2:]=0.
            if self.mode in {'ALIGNING','READY'}:
                if abs(measured_v)>ALIGN_BODY_SPEED or abs(measured_w)>ALIGN_BODY_YAW:
                    raise ValueError('ALIGNMENT_BODY_ENVELOPE_EXCEEDED')
                # Latch alignment across small induced motion. The original .03
                # body settling gate remains enforced; no .005 re-lock loop.
                target[:2]=np.clip(np.zeros(2),self.last[:2]-ALIGN_RATE*self.dt,self.last[:2]+ALIGN_RATE*self.dt)
                correction=float(np.clip(-YAW_DAMPING*measured_w*self.track/(2*self.radius),-MAX_REAR_CORRECTION,MAX_REAR_CORRECTION))
                target[2:]=[-correction,correction]  # zero mean traction; no retreat request
                if self.stable_ticks>=STABLE_TICKS and self.encoder_ready() and abs(self.last[:2]).max()<1e-12:
                    self.mode='READY';target[:2]=0.;target[2:]=0.
        target=np.clip(target,self.commands.lower,self.commands.upper)
        rate=self.commands.rate*self.dt/.08
        command=np.clip(target,self.last-rate,self.last+rate)
        assert self.commands.legal(command)and np.max(abs(command-self.last)-rate)<1e-10
        self.last=command.copy();return command
