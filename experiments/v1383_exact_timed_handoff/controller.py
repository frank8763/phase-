"""Original timed intent; phase starts at measured original gear release."""
import math
class Capture:
    def __init__(self,task):self.task=task;self.release_tick=None;self.phase='GEAR_WAIT'
    def select(self,body,tick,encoders,last_ctrl):
        if self.release_tick is None:return -.005,.0025,dict(phase='GEAR_WAIT',parked_target=None,release_tick=None)
        t=.05+(tick-self.release_tick)*.01;cruise=(self.task['reference_length_m']-.15)/.1
        speed=.1*t if t<=1 else .1 if t<=1+cruise else max(0.,.1-.05*(t-1-cruise))
        if speed<.005-1e-12:
            self.phase='RESPONSE_COMPLETE';return 0.,0.,dict(phase=self.phase,parked_target=None,release_tick=self.release_tick,profile_phase_s=t)
        speed=max(.005,speed);self.phase='DRIVE' if t<=1+cruise else 'BRAKE'
        return -speed,.5*speed,dict(phase=self.phase,parked_target=None,release_tick=self.release_tick,profile_phase_s=t)
    def observe_gear(self,tick,proof):
        if proof['released']:
            assert self.release_tick is None and proof['requested_gear']==-1 and proof['braking_native']>=200
            self.release_tick=tick
def errors(body,segment):
    r=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]];goal=segment['poses'][-1]
    return math.dist(r[:2],goal[:2]),abs(math.atan2(math.sin(r[2]-goal[2]),math.cos(r[2]-goal[2])))
