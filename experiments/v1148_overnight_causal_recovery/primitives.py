"""The existing qualified C++ normal-mode kernel, including end controller memory.

Guidance expansion only. Complete selected sources are independently propagated
by the qualified mode-aware engine AND Python before any acceptance.
"""
from night_tools import *
import ctypes
import numpy as np
sys.path.insert(0,str(R/'experiments/v1121_coupled_route_night'))
from bindings import PARAMETERS,REQUIRED,ref
from source import Engine,initial,python_replay
CAP=.42722137342572125

class Expander:
 def __init__(self,setup):
  self.lib=ctypes.CDLL(str(R/'runs/v1118_coupled_live_qualification/profile.so'));a=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');self.lib.expand.argtypes=[a,a,a,a,ctypes.c_int,ctypes.c_int,a,a,a,a,a,a];self.lib.expand.restype=ctypes.c_int
  p=PARAMETERS;self.p=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']]);self.limits=np.ascontiguousarray(setup['limits'],float);self.rates=np.ascontiguousarray(setup['slew_per_second'],float);self.native=0;self.partial_unknown=False
 def expand(self,state,memory,targets,speed,ticks):
  state=np.ascontiguousarray(state,float);memory=np.ascontiguousarray(memory,float);targets=np.ascontiguousarray(targets,float)
  assert state.shape==(8,)and memory.shape==(5,)and targets.ndim==1 and 0<len(targets)<=7
  assert np.isfinite(np.r_[state,memory,targets]).all()and abs(targets).max()<=CAP+1e-12
  assert speed in [0.,.08,.12]and type(ticks)is int and 1<=ticks<=2200
  speeds=np.full(len(targets),speed);ss=np.empty((len(targets),ticks,8));uu=np.empty((len(targets),ticks,4));mem=np.empty((len(targets),5));self.partial_unknown=True
  code=self.lib.expand(state,memory,targets,speeds,len(targets),ticks,self.limits,self.rates,self.p,ss,uu,mem)
  assert code==0,('ANALYTICAL_PRIMITIVE_CONTRACT',code)
  self.native+=len(targets)*ticks;self.partial_unknown=False;assert np.isfinite(ss).all()and np.isfinite(uu).all()and np.isfinite(mem).all()
  return ss,uu,mem

def state_key(state,memory,tick,start_clock):
 # Approximate merging is search guidance, never an acceptance proof.
 phase=(start_clock+.01*tick)%(2*np.pi/.32)
 scales=np.array([.06,.06,.08,.02,.01,.02,.08,.08])
 return tuple(np.rint(np.r_[np.asarray(state)/scales,np.asarray(memory)/[.08,.08,.3,.3,.1],phase/.4]).astype(int))
