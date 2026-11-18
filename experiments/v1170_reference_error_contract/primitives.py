"""Bijective kinematic coordinates; no predictor execution or learned bounds."""
import numpy as np
DT=.01
def wrap(a):return np.arctan2(np.sin(a),np.cos(a))

def encode(s,t):
    s=np.asarray(s,float);t=np.asarray(t,float);assert s.shape==t.shape and s.shape[1]==8
    dyaw=wrap(t[:,2]-s[:,2]);angle=s[:,2]+dyaw/2;dp=t[:,:2]-s[:,:2]
    body=np.column_stack([np.cos(angle)*dp[:,0]+np.sin(angle)*dp[:,1],-np.sin(angle)*dp[:,0]+np.cos(angle)*dp[:,1]])
    out=np.empty_like(s);out[:,:2]=body-DT*(s[:,3:5]+t[:,3:5])/2
    out[:,2]=dyaw-DT*(s[:,5]+t[:,5])/2
    out[:,3:6]=t[:,3:6];out[:,6]=t[:,6]-s[:,6]-DT*t[:,7];out[:,7]=t[:,7]
    assert np.isfinite(out).all();return out

def decode(s,c):
    s=np.asarray(s,float);c=np.asarray(c,float);assert s.shape==c.shape and s.shape[1]==8
    out=np.empty_like(s);out[:,3:6]=c[:,3:6];out[:,7]=c[:,7];out[:,6]=s[:,6]+DT*c[:,7]+c[:,6]
    dyaw=DT*(s[:,5]+c[:,5])/2+c[:,2];angle=s[:,2]+dyaw/2;out[:,2]=s[:,2]+dyaw
    body=DT*(s[:,3:5]+c[:,3:5])/2+c[:,:2]
    out[:,0]=s[:,0]+np.cos(angle)*body[:,0]-np.sin(angle)*body[:,1]
    out[:,1]=s[:,1]+np.sin(angle)*body[:,0]+np.cos(angle)*body[:,1]
    return out

def maximum_error(a,b):
    d=np.abs(a-b);d[:,2]=abs(wrap(a[:,2]-b[:,2]));return float(d.max())

FEATURES=['longitudinal_v','lateral_v','body_w','virtual_delta','virtual_rate',
          'previous_front_left','previous_front_right','previous_rear_left','previous_rear_right','integral','request_v','request_w']
PHASES=['BASE_BRAKE','LOADED_BRAKE','COUPLED_BRAKE','PARKED_STEER','FORWARD','REVERSE']
def features(s,memory,request):return np.column_stack([s[:,3:8],memory,request])
