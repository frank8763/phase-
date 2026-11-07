"""Causal proposal-only penalty for stopping where another tail is expensive."""
import numpy as np
from norm_gate import radial_values
HORIZON=6.56
SCALE=.08*HORIZON
EDGE_WEIGHT=6.


def deficit(field,state,poses):
    p=np.asarray(poses,float).reshape(-1,3)
    if state['center']is None:return np.zeros(len(p))
    lower=radial_values(field,p,state,np.full(len(p),HORIZON))
    return np.clip((.155-lower)/SCALE,0.,1.)
