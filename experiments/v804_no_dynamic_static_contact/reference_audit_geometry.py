"""Independent proposal-field reconstruction from public map and causal bounds only."""
from types import SimpleNamespace
import numpy as np
def reference_field(protocol,state):
 bounds=np.asarray(protocol['footprint_bounds'],float);rect=list(protocol['known_rectangles']);circ=list(protocol['known_circles'])
 if state['center']is not None:
  rect.append(state['current_outer_rectangle'])
  t=np.linspace(0.,6.56,17)[:,None];pl=np.asarray(state['position_lower']);pu=np.asarray(state['position_upper']);vl=np.asarray(state['velocity_lower']);vu=np.asarray(state['velocity_upper'])
  lo=np.maximum(pl+t*vl-.02*t*t,pl-.12*t);hi=np.minimum(pu+t*vu+.02*t*t,pu+.12*t);pad=.12*(6.56/16)/2+1e-5;lower=lo.min(axis=0)-pad;upper=hi.max(axis=0)+pad
  rect.append([*((lower+upper)/2),*((upper-lower)/2+.10)])
 return SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(rect).reshape(-1,4),circles=np.asarray(circ).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
