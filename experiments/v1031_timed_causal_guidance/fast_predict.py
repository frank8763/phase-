"""Bounded no-model analytical expansion. Never used for final admission."""
import ctypes,hashlib,subprocess
from pathlib import Path
import numpy as np
from whole_input import PARAMETERS
C=Path(__file__).resolve().parent;R=C.parents[1]

def library():
    source=C/'fast_predict.cpp';digest=hashlib.sha256(source.read_bytes()).hexdigest();cache=R/'runs/v1031_timed_causal_guidance';cache.mkdir(exist_ok=True)
    target=cache/('analytical_'+digest[:16]+'.so')
    if not target.exists():subprocess.run(['g++','-std=c++17','-O2','-fPIC','-shared',str(source),'-o',str(target)],check=True,timeout=30)
    obj=ctypes.CDLL(str(target));arr=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    obj.expand.argtypes=[arr,arr,arr,arr,ctypes.c_int,ctypes.c_int,arr,arr,arr,arr,arr,arr];obj.expand.restype=ctypes.c_int
    return obj

class Expander:
    def __init__(self,setup):
        self.lib=library();self.limits=np.ascontiguousarray(setup['limits'],dtype=float);self.rates=np.ascontiguousarray(setup['slew_per_second'],dtype=float)
        p=PARAMETERS;self.p=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete']])
    def expand(self,state,memory,targets,steps=334,speeds=None):
        state=np.ascontiguousarray(state,float);memory=np.ascontiguousarray(memory,float);targets=np.ascontiguousarray(targets,float)
        assert state.shape==(8,)and memory.shape==(5,)and targets.ndim==1 and 0<len(targets)<=5 and 0<steps<=334
        assert np.isfinite(np.r_[state,memory,targets]).all() and abs(targets).max()<=.42722137342572125+1e-12
        speeds=np.full(len(targets),.03)if speeds is None else np.ascontiguousarray(speeds,float)
        assert speeds.shape==targets.shape and np.isin(speeds,[0.,.03,.08]).all()
        n=len(targets);states=np.empty((n,steps,8));ctrl=np.empty((n,steps,4));mem=np.empty((n,5))
        result=self.lib.expand(state,memory,targets,speeds,n,steps,self.limits,self.rates,self.p,states,ctrl,mem)
        assert result==0,('ANALYTICAL_EXPANSION_CONTRACT',result)
        assert np.isfinite(states).all()and np.isfinite(ctrl).all()and np.isfinite(mem).all()
        return states,ctrl,mem
