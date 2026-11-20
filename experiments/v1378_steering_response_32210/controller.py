"""Same existing bounded coupled-steering mode; single saved input qualification."""
import math
def rear(body):return [body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
class Capture:
    def __init__(self,task):self.task=task;self.phase='PREPARE_REVERSE';self.ready_since=None
    def select(self,body,tick,encoders,last_ctrl):
        k=self.task['forward_curvature'];target=math.atan(.6*k);pair=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]
        angle=max(abs(a-b) for a,b in zip(encoders[:2],pair));ready=angle<=.025 and max(abs(a-b) for a,b in zip(last_ctrl[:2],pair))<=.025 and max(abs(x) for x in encoders[2:])<=.03 and max(abs(x) for x in body[3:])<=.003 and max(abs(x) for x in last_ctrl[2:])<=1e-10
        if ready:
            if self.ready_since is None:self.ready_since=tick
            elif tick-self.ready_since>=self.task['ready_hold_native']:self.phase='RESPONSE_COMPLETE'
        else:self.ready_since=None
        return 0.,0.,dict(phase=self.phase,forward_steering_error_rad=angle,ready=ready,ready_since=self.ready_since,
            parked_target=target if self.phase=='PREPARE_REVERSE' else None)
def errors(body,segment):
    a=rear(body);b=segment['poses'][0];return math.dist(a[:2],b[:2]),abs(math.atan2(math.sin(a[2]-b[2]),math.cos(a[2]-b[2])))
