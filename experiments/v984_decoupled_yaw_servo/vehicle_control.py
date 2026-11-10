"""V958 steering/common drive, with bounded rear-only body-yaw compensation.

No model, geometry, state, time, reference or body-command writes occur here.
The physical response remains unqualified until a separately authorized gate.
"""
import importlib.util
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v984_original_hold_brake',R/'experiments/v958_hold_steering_contract/vehicle_control.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
YAW_GAIN=1.5
MAX_EQUIVALENT_YAW=.16


class Adapter(base.Adapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.last_yaw_proof=None

    def compute(self,v,w,measured_v,measured_w,stale=False):
        previous=self.last.copy()
        nominal=super().compute(v,w,measured_v,measured_w,stale)
        clipped_v=float(np.clip(v,-.15,.30))
        clipped_w=float(np.clip(w,-abs(clipped_v)*self.max_curvature,abs(clipped_v)*self.max_curvature))
        error=clipped_w-float(measured_w)
        self.last_yaw_proof=dict(applied=False,requested=[float(v),float(w)],measured=[float(measured_v),float(measured_w)],
                                 nominal=nominal.tolist(),previous=previous.tolist(),gain=YAW_GAIN)
        # Original hold-steering brake, stale and nonforward handling remain the
        # original function, including integral reset and original actuator slew.
        if stale or clipped_v<.005 or abs(error)<=1e-12:
            return nominal
        rate=np.asarray(self.commands.rate)*self.dt/.08
        lower=np.maximum(self.commands.lower[2:],previous[2:]-rate[2:])
        upper=np.minimum(self.commands.upper[2:],previous[2:]+rate[2:])
        # Do not introduce a wheel-target sign change that the nominal map did
        # not request. Individual wheel braking remains the original behavior.
        for i,value in enumerate(nominal[2:]):
            if value>0:lower[i]=max(lower[i],0.)
            elif value<0:upper[i]=min(upper[i],0.)
            else:lower[i]=upper[i]=0.
        common=float(nominal[2:].mean())
        lo=max(common-upper[0],lower[1]-common)
        hi=min(common-lower[0],upper[1]-common)
        assert lo<=hi+1e-12,'EMPTY_REAR_DIFFERENTIAL_FEASIBLE_SET'
        if lo>hi:lo=hi=(lo+hi)/2
        equivalent=float(np.clip(clipped_w+YAW_GAIN*error,-MAX_EQUIVALENT_YAW,MAX_EQUIVALENT_YAW))
        desired=equivalent*self.track/(2*self.radius)
        differential=float(np.clip(desired,lo,hi))
        command=nominal.copy();command[2:]=[common-differential,common+differential]
        assert self.commands.legal(command),'REAR_YAW_COMMAND_OUTSIDE_ORIGINAL_LIMITS'
        assert np.max(abs(command-previous)-rate)<=1e-10,'REAR_YAW_COMMAND_SLEW_EXCEEDED'
        assert np.max(abs(command[:2]-nominal[:2]))==0.,'FRONT_STEERING_CHANGED'
        assert abs(command[2:].mean()-common)<=1e-12,'LONGITUDINAL_COMMON_COMPONENT_CHANGED'
        self.last=command.copy()
        self.last_yaw_proof.update(applied=True,yaw_error=error,equivalent_yaw_target=equivalent,
            requested_differential=desired,feasible_differential=[lo,hi],selected_differential=differential,
            selected=command.tolist(),projection_limited=not(lo<=desired<=hi),original_body_command_unchanged=True)
        return command


def transfer_restored_state(old,new):
    """Pure controller-memory transfer at a future restored origin, no model call."""
    assert abs(old.dt-new.dt)<=1e-12,'CONTROLLER_DT_CHANGED'
    assert np.array_equal(old.commands.lower,new.commands.lower)and np.array_equal(old.commands.upper,new.commands.upper),'ACTUATOR_LIMIT_CHANGED'
    assert np.array_equal(old.commands.rate,new.commands.rate),'ACTUATOR_RATE_CHANGED'
    assert old.commands.legal(old.last),'INVALID_RESTORED_CONTROL_MEMORY'
    assert np.isfinite(old.integral),'NONFINITE_RESTORED_INTEGRAL'
    new.last=old.last.copy();new.integral=float(old.integral);new.mode=old.mode
    new.last_yaw_proof=None
    assert np.array_equal(old.last,new.last)and old.integral==new.integral
    return dict(controller_memory_only=True,integrations=0,root_or_clock_write=False,
                original_last_control=old.last.tolist(),original_longitudinal_integral=old.integral)
