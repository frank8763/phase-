"""One actuator-legal amplitude/rate map for prediction, reserve and execution."""
import numpy as np

class CommandMap:
    def __init__(self,model,mj):
        names=['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']
        self.ids=[mj.mj_name2id(model,mj.mjtObj.mjOBJ_ACTUATOR,n)for n in names]
        assert min(self.ids)>=0 and np.all(model.actuator_ctrllimited[self.ids]),'ACTUATOR_LIMITS_REQUIRED'
        self.lower=model.actuator_ctrlrange[self.ids,0].copy();self.upper=model.actuator_ctrlrange[self.ids,1].copy()
        assert np.all(self.lower<self.upper)
        self.rate=np.array([.10,.10,.70,.70])
    def legal(self,command):
        a=np.asarray(command,float);return a.shape==(4,)and np.isfinite(a).all()and np.all(a>=self.lower-1e-12)and np.all(a<=self.upper+1e-12)
    def step(self,target,last):
        last=np.asarray(last,float);target=np.asarray(target,float)
        assert self.legal(last),'NONCANONICAL_PREVIOUS_COMMAND'
        assert target.shape==(4,)and np.isfinite(target).all(),'INVALID_TARGET_COMMAND'
        return np.clip(np.clip(target,self.lower,self.upper),last-self.rate,last+self.rate)
    def assert_first(self,command,last):
        assert self.legal(command),'COMMAND_OUTSIDE_ACTUATOR_RANGE'
        assert np.max(abs(np.asarray(command)-self.step(command,last)))<=1e-12,'COMMAND_EXCEEDS_ACTUATOR_SLEW'
    def sequence(self,target,last,horizon,brake_after=None):
        rows=[];command=np.asarray(last,float).copy()
        for tick in range(0,horizon,8):
            active=np.asarray(target,float).copy()
            if brake_after is not None and tick>=brake_after:active[2:]=0.
            command=self.step(active,command)
            rows.extend([command.copy()for _ in range(min(8,horizon-tick))])
        return np.asarray(rows)
