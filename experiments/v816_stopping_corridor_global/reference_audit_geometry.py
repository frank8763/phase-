"""Independent proposal-field reconstruction from public map and causal bounds only."""
from types import SimpleNamespace
import numpy as np
def reference_field(protocol,state):
 if state['center']is not None:
  from independent_corridor import independent_field
  return independent_field(protocol,state)
 bounds=np.asarray(protocol['footprint_bounds'],float);rect=list(protocol['known_rectangles']);circ=list(protocol['known_circles'])
 if state['center']is not None:
  rect.append(state['current_outer_rectangle'])

 return SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(rect).reshape(-1,4),circles=np.asarray(circ).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
