"""Scalar independent reconstruction of the declared steering command state."""
import math
import numpy as np


def reconstruct(last,packet,request,now):
    v,w=request;s=packet['steering'];q=s['position'];velocity=s['velocity'];tick=packet['native_tick']
    assert s['native_tick']==tick and abs(s['measured_at']-packet['body_measured_at'])<=1e-9 and 0<=now-s['measured_at']<=.05
    assert 0<=v<=.1+1e-10 and abs(w)<=v*.758770385+1e-9
    if v<.005:return [0.,0.],None,'STOP_NO_MOTION_OVERRIDE'
    if last is None or now-last['at']>.2:
        if max(abs(packet['body'][3]),abs(packet['body'][4]))>.03 or max(map(abs,velocity))>.03:
            return [0.,0.],None,'WAIT_MEASURED_BODY_AND_STEERING_STABLE'
        left=math.tan(q[0])/(.6+.27*math.tan(q[0]));right=math.tan(q[1])/(.6-.27*math.tan(q[1]))
        assert abs(left-right)<=.02 and abs((left+right)/2)<=.758770385+2e-6
        delta=math.atan(.6*max(-.758770385,min(.758770385,(left+right)/2)))
        mode='ANCHORED_TO_MEASURED_STOPPED_STEERING'
    else:
        assert now>=last['at'];step=.6*min(.05,now-last['at']);target=math.atan(.6*w/v)
        delta=max(last['delta']-step,min(last['delta']+step,target));mode='RATE_LIMITED_FORWARD_CONTINUATION'
    return [v,v*math.tan(delta)/.6],delta,mode


def check(shape,packet,last):
    assert shape['prior']==last
    selected,delta,mode=reconstruct(last,packet,shape['raw'],shape['at'])
    assert mode==shape['mode']and np.max(abs(np.array(selected)-shape['selected']))<=1e-12
    assert(delta is None and shape['delta']is None)or(delta is not None and abs(delta-shape['delta'])<=1e-12)
    return None if delta is None else dict(at=shape['at'],delta=delta)
