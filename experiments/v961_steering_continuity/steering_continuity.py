"""Pure command shaping before safety admission. No model/obstacle truth inputs."""
import copy
import math
import numpy as np

K=.758770385
VIRTUAL_RATE=.60
WHEELBASE=.60
TRACK=.54


def measured(packet,now,max_age=.05):
    encoder=packet.get('steering')
    if encoder is None:raise ValueError('MEASURED_STEERING_REQUIRED')
    q=np.asarray(encoder['position'],float);v=np.asarray(encoder['velocity'],float)
    if q.shape!=(2,)or v.shape!=(2,)or not np.isfinite([*q,*v,encoder['measured_at'],now]).all():raise ValueError('INVALID_STEERING_ENCODERS')
    if encoder['native_tick']!=packet['native_tick']:raise ValueError('INCOHERENT_STEERING_ENCODERS')
    if abs(encoder['measured_at']-packet['body_measured_at'])>1e-9:raise ValueError('INCOHERENT_STEERING_TIMESTAMP')
    if not 0<=now-encoder['measured_at']<=max_age:raise ValueError('STALE_STEERING_ENCODERS')
    if abs(q).max()>.520001:raise ValueError('STEERING_OUTSIDE_ORIGINAL_LIMIT')
    t=np.tan(q);curvature=np.array([t[0]/(WHEELBASE+TRACK/2*t[0]),t[1]/(WHEELBASE-TRACK/2*t[1])])
    return q,v,curvature


class SteeringContinuity:
    def __init__(self):self.last=None

    def preview(self,packet,v,w,now):
        if not np.isfinite([v,w,now]).all()or v<0 or v>.1+1e-10 or abs(w)>abs(v)*K+1e-9:raise ValueError('UNQUALIFIED_FORWARD_REQUEST')
        q,velocity,curvature=measured(packet,now)
        base=dict(raw=[float(v),float(w)],at=float(now),native_tick=packet['native_tick'],
            position=q.tolist(),velocity=velocity.tolist(),prior=copy.deepcopy(self.last),rate=VIRTUAL_RATE)
        if abs(v)<.005:return dict(base,selected=[0.,0.],delta=None,mode='STOP_NO_MOTION_OVERRIDE')
        restart=self.last is None or now-self.last['at']>.2
        if self.last is not None and now<self.last['at']:raise ValueError('NONMONOTONIC_STEERING_COMMAND_TIME')
        if restart:
            if max(abs(packet['body'][3]),abs(packet['body'][4]))>.03 or abs(velocity).max()>.03:
                return dict(base,selected=[0.,0.],delta=None,mode='WAIT_MEASURED_BODY_AND_STEERING_STABLE')
            if abs(curvature[0]-curvature[1])>.02:raise ValueError('INCONSISTENT_STOPPED_ACKERMANN_STEERING')
            initial=float(np.mean(curvature));assert abs(initial)<=K+2e-6
            delta=math.atan(WHEELBASE*float(np.clip(initial,-K,K)))
            mode='ANCHORED_TO_MEASURED_STOPPED_STEERING'
        else:
            dt=min(.05,now-self.last['at']);assert dt>=0
            target=math.atan(WHEELBASE*w/v)
            delta=float(np.clip(target,self.last['delta']-VIRTUAL_RATE*dt,self.last['delta']+VIRTUAL_RATE*dt))
            mode='RATE_LIMITED_FORWARD_CONTINUATION'
        angular=float(v*math.tan(delta)/WHEELBASE)
        assert abs(angular)<=v*K+1e-9
        return dict(base,selected=[float(v),angular],delta=delta,mode=mode)

    def commit(self,shape):
        # Only an actually dispatched, newly admitted proof may commit this state.
        self.last=None if shape['delta']is None else dict(at=shape['at'],delta=shape['delta'])


def stopped_ready(packet,now):
    _,velocity,_=measured(packet,now,max_age=.2)
    return bool(max(abs(packet['body'][3]),abs(packet['body'][4]))<=.03 and abs(velocity).max()<=.03)
