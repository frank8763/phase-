"""Joint Ackermann target allocation; algebraic candidate, not plant qualification.

One virtual curvature generates both steering targets and rear velocity targets.
Intersect original actuator slew/limits before selecting curvature/common speed.
No state, reference, model, time or body-command write occurs here.
"""
import importlib.util
import math
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v990_original_controller_interface',R/'experiments/v958_hold_steering_contract/vehicle_control.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
YAW_GAIN=0.
VIRTUAL_RATE=.6
MAX_EQUIVALENT_YAW=.16
MAX_COMMON=6.


def inverse_steering(angle, side, wheelbase, half_track):
    t=math.tan(float(angle))
    den=wheelbase+side*half_track*t
    assert den>0.,'INVALID_STEERING_INVERSE'
    return t/den


def steering(curvature,wheelbase,half_track):
    return np.array([math.atan(wheelbase*curvature/(1-half_track*curvature)),
                     math.atan(wheelbase*curvature/(1+half_track*curvature))])


class Adapter(base.Adapter):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.last_allocation_proof=None

    def compute(self,v,w,measured_v,measured_w,stale=False):
        assert np.isfinite([v,w,measured_v,measured_w]).all(),'NONFINITE_BODY_COMMAND'
        assert np.isfinite(self.last).all() and np.isfinite(self.integral),'NONFINITE_CONTROLLER_MEMORY'
        assert 0.<self.dt<=.02,'INVALID_CONTROLLER_PERIOD'
        previous=self.last.copy();old_integral=self.integral
        assert self.commands.legal(previous),'PREVIOUS_CONTROL_OUTSIDE_LIMITS'
        v=float(np.clip(v,-.15,.30))
        w=float(np.clip(w,-abs(v)*self.max_curvature,abs(v)*self.max_curvature))
        braking=bool(stale or abs(v)<.005)
        assert braking or v>0.,'V990_FORWARD_COMPONENT_ONLY'
        rate=np.asarray(self.commands.rate,float)*self.dt/.08
        lower=np.maximum(np.asarray(self.commands.lower,float),previous-rate)
        upper=np.minimum(np.asarray(self.commands.upper,float),previous+rate)
        h=self.track/2;L=self.wheelbase
        previous_k=np.array([inverse_steering(previous[0],1,L,h),inverse_steering(previous[1],-1,L,h)])
        assert abs(previous_k[0]-previous_k[1])<=1e-8,'PREVIOUS_FRONT_TARGETS_NOT_COORDINATED'
        pk=float(previous_k.mean())
        assert abs(pk)<=self.max_curvature+1e-9,'PREVIOUS_CURVATURE_OUTSIDE_CONTRACT'
        assert np.min(previous[2:])>=-1e-10,'PREVIOUS_REAR_REVERSE'
        pm=float(previous[2:].mean())
        prior_rear=pm*np.array([1-h*pk,1+h*pk])
        assert np.max(abs(prior_rear-previous[2:]))<=1e-8,'PREVIOUS_REAR_TARGETS_NOT_COORDINATED'
        lower[2:]=np.maximum(lower[2:],0.)
        assert np.all(lower<=upper+1e-12),'EMPTY_ACTUATOR_BOX'
        klo=max(-self.max_curvature,inverse_steering(lower[0],1,L,h),inverse_steering(lower[1],-1,L,h))
        khi=min(self.max_curvature,inverse_steering(upper[0],1,L,h),inverse_steering(upper[1],-1,L,h))
        delta=math.atan(L*pk)
        klo=max(klo,math.tan(max(-self.center_limit,delta-getattr(self,'virtual_rate',VIRTUAL_RATE)*self.dt))/L)
        khi=min(khi,math.tan(min(self.center_limit,delta+getattr(self,'virtual_rate',VIRTUAL_RATE)*self.dt))/L)
        # x=m*(1-h*k), y=m*(1+h*k). Pairwise lower/upper
        # inequalities give the exact feasible k interval for positive factors.
        l0,l1=map(float,lower[2:]);u0,u1=map(float,upper[2:])
        if l0+u1>0:khi=min(khi,(u1-l0)/(h*(l0+u1)))
        if l1+u0>0:klo=max(klo,(l1-u0)/(h*(l1+u0)))
        khi=min(khi,(1-l0/MAX_COMMON)/h)
        klo=max(klo,(l1/MAX_COMMON-1)/h)
        assert klo<=khi+1e-10,'NO_JOINT_CURVATURE_COMMON_SPEED'
        if klo>khi:klo=khi=(klo+khi)/2
        if braking:
            wanted_k=pk;wanted_common=0.;next_integral=0.
            desired_yaw=0.;mode='BRAKING_COORDINATED_STEERING_HOLD'
        else:
            error=v-float(measured_v)
            next_integral=float(np.clip(old_integral+error*self.dt,-.4,.4))
            wanted_common=float(np.clip(v/self.radius+8*error+4*next_integral,0.,MAX_COMMON))
            desired_yaw=float(np.clip(w+YAW_GAIN*(w-float(measured_w)),-MAX_EQUIVALENT_YAW,MAX_EQUIVALENT_YAW))
            wanted_k=float(np.clip(desired_yaw/v,-self.max_curvature,self.max_curvature))
            mode='FORWARD_COORDINATED_ALLOCATION'
        k=float(np.clip(wanted_k,klo,khi))
        if braking:assert abs(k-pk)<=1e-9,'BRAKE_CANNOT_PRESERVE_STEERING'
        factors=np.array([1-h*k,1+h*k]);assert np.min(factors)>0
        mlo=max(0.,float(np.max(lower[2:]/factors)))
        mhi=min(MAX_COMMON,float(np.min(upper[2:]/factors)))
        assert mlo<=mhi+1e-10,'EMPTY_COMMON_SPEED_INTERVAL'
        if mlo>mhi:mlo=mhi=(mlo+mhi)/2
        mean=float(np.clip(wanted_common,mlo,mhi))
        front=previous[:2].copy()if braking else steering(k,L,h)
        command=np.r_[front,mean*factors]
        assert self.commands.legal(command),'JOINT_COMMAND_OUTSIDE_LIMITS'
        assert np.max(abs(command-previous)-rate)<=1e-10,'JOINT_COMMAND_SLEW_EXCEEDED'
        # No individual wheel clipping after this joint solution.
        self.integral=next_integral;self.last=command.copy();self.mode=mode
        self.last_allocation_proof=dict(mode=mode,requested=[float(v),float(w)],measured=[float(measured_v),float(measured_w)],
            stale=bool(stale),previous=previous.tolist(),previous_integral=float(old_integral),next_integral=next_integral,
            lower=lower.tolist(),upper=upper.tolist(),curvature_interval=[klo,khi],wanted_curvature=wanted_k,
            selected_curvature=k,common_interval=[mlo,mhi],wanted_common=wanted_common,selected_common=mean,
            equivalent_yaw_target=desired_yaw,curvature_limited=abs(k-wanted_k)>1e-10,
            common_limited=abs(mean-wanted_common)>1e-10,selected=command.tolist(),
            original_body_command_unchanged=True,physical_tracking_qualified=False)
        return command


def transfer_restored_state(old,new):
    """Exact stopped controller-memory transfer; no physical model call."""
    assert old.dt==new.dt and abs(old.dt-.01)<1e-12,'CONTROLLER_PERIOD_CHANGED'
    for name in ['lower','upper','rate']:
        assert np.array_equal(getattr(old.commands,name),getattr(new.commands,name)),'ACTUATOR_CONTRACT_CHANGED'
    assert old.commands.legal(old.last) and np.isfinite(old.integral),'INVALID_CONTROLLER_MEMORY'
    assert np.max(abs(old.last[2:]))<=1e-10,'SWITCH_REQUIRES_STOPPED_REAR_TARGETS'
    k0=inverse_steering(old.last[0],1,old.wheelbase,old.track/2)
    k1=inverse_steering(old.last[1],-1,old.wheelbase,old.track/2)
    assert abs(k0-k1)<=1e-8 and abs(k0)<=new.max_curvature+1e-9,'RESTORED_FRONT_TARGETS_NOT_COORDINATED'
    new.last=old.last.copy();new.integral=float(old.integral);new.mode=old.mode;new.last_allocation_proof=None
    return dict(controller_memory_only=True,integrations=0,root_or_clock_write=False,
                original_last_control=old.last.tolist(),original_longitudinal_integral=old.integral,
                stopped_origin_curvature=(k0+k1)/2)
