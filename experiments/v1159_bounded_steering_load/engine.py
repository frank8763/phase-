"""Independent C++ candidate propagation; full state/control/memory outputs."""
from pathlib import Path
import ctypes
import math
import numpy as np
from bindings import PARAMETERS,GAIN

C=Path(__file__).resolve().parent;R=C.parents[1]


class Engine:
    def __init__(self,setup,coefficients):
        self.setup=setup;self.coefficients=list(coefficients);self.native=0;self.in_call=False
        self.lib=ctypes.CDLL(str(R/'runs/v1159_bounded_steering_load/profile.so'))
        arr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');ints=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
        self.lib.profile.argtypes=[arr,arr,arr,arr,ints,ints,ctypes.c_int,arr,arr,arr,arr,arr,arr]
        self.lib.profile.restype=ctypes.c_int;self.lib.profile_work.argtypes=[];self.lib.profile_work.restype=ctypes.c_int

    def simulate(self,origin,rows):
        assert rows and all(len(r)==4 and int(r[2])==r[2] and 0<r[2]<=12000 and r[3]in[0,1]for r in rows)
        n=sum(int(r[2])for r in rows);assert n<=40000
        state=np.asarray(origin['state'],float).copy();memory=np.r_[origin['last_ctrl'],origin['integral']]
        assert state.shape==(8,)and memory.shape==(5,)and np.isfinite(state).all()and np.isfinite(memory).all()
        assert type(origin['steering_load_episode'])is bool
        p=PARAMETERS;params=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient'],GAIN,float(origin.get('coupled_episode',False)),float(origin.get('steering_motion_active',False)),*self.coefficients,float(origin['steering_load_episode'])])
        tt=np.array([r[0]for r in rows]);vv=np.array([r[1]for r in rows]);nn=np.array([r[2]for r in rows],np.int32);mm=np.array([r[3]for r in rows],np.int32)
        ss=np.empty((n,8));uu=np.empty((n,4));mem=np.empty((n,5));limits=np.array(self.setup['limits'],float);rates=np.array(self.setup['slew_per_second'],float)
        self.in_call=True;code=self.lib.profile(state,memory,tt,vv,nn,mm,len(rows),limits,rates,params,ss,uu,mem);self.in_call=False
        work=int(self.lib.profile_work());self.native+=work
        assert code==work==n,('CPP_PROFILE_FAILED',code,work,n)
        return np.vstack([state,ss]),uu,np.vstack([memory,mem])


def row(v,w,mode=False,target=0.):
    return (float(target)if mode else math.atan(.6*w/v)if v else 0.,float(v),1,int(mode))
