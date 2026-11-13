"""Frozen original C++ allocation/dynamics, proposal only; no physics imports."""
import ctypes
from pathlib import Path
import numpy as np
from kernel import PARAMETERS
O=Path(__file__).resolve().parents[2]/'runs/v1107_reference_frame_alignment'
class Preview:
    def __init__(self,setup):
        self.lib=ctypes.CDLL(str(O/'analytical_dynamics.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
        self.lib.expand.argtypes=[a,a,a,a,ctypes.c_int,ctypes.c_int,a,a,a,a,a,a];self.lib.expand.restype=ctypes.c_int
        self.limits=np.ascontiguousarray(setup['limits'],dtype=float);self.rates=np.ascontiguousarray(setup['slew_per_second'],dtype=float)
        p=PARAMETERS;self.parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']],float)
        self.native=0;self.calls=0
    def expand(self,state,memory,targets,speed,steps):
        state=np.ascontiguousarray(state,float);memory=np.ascontiguousarray(memory,float);targets=np.ascontiguousarray(targets,float)
        assert state.shape==(8,) and memory.shape==(5,) and targets.ndim==1 and 0<len(targets)<=22 and 25<=steps<=500
        assert np.isfinite(np.r_[state,memory,targets]).all() and abs(targets).max()<=.42722137342572125+1e-12 and speed in [.08,-.03]
        n=len(targets);speeds=np.full(n,speed);ss=np.empty((n,steps,8));uu=np.empty((n,steps,4));mm=np.empty((n,5))
        code=self.lib.expand(state,memory,targets,speeds,n,steps,self.limits,self.rates,self.parameters,ss,uu,mm)
        assert code==0,('ORIGINAL_ANALYTICAL_CONTRACT',code)
        assert np.isfinite(ss).all() and np.isfinite(uu).all() and np.isfinite(mm).all()
        self.calls+=1;self.native+=n*steps
        return ss,uu,mm
