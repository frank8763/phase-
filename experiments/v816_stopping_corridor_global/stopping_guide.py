"""A causal 3.28s reachable-union corridor proposal, never a control certificate.

Each retained joint position/velocity cell is swept over the existing complete
braking horizon. Original current occupancy and all known geometry are retained.
No actor truth, arrival-time guess or change to the native execution gate.
"""
import numpy as np
from union_belief import future_cells
from soft_guide import attach as soft_attach

HORIZON=3.28  # exactly the registered decimal duration, 328 native ticks
RADIUS=.10

def sweep_boxes(state):
    cells=np.asarray(state['outer_state_cells'],float)
    assert cells.ndim==3 and cells.shape[1:]==(4,2) and 0<len(cells)<=256
    lo,hi=future_cells(cells,[HORIZON])
    lower=np.minimum(cells[:,0],lo[0]);upper=np.maximum(cells[:,1],hi[0])
    # Every per-axis lower bound is a max of a concave quadratic and a
    # decreasing speed line; the upper bound is the corresponding min of a
    # convex quadratic and an increasing line. Their interval extrema over
    # [0,H] occur at the endpoints. This hull covers every original cell/time.
    keep=[]
    for i in range(len(lower)):
        contained=False
        for j in range(len(lower)):
            if i==j:continue
            if np.all(lower[i]>=lower[j]) and np.all(upper[i]<=upper[j]):
                same=np.array_equal(lower[i],lower[j])and np.array_equal(upper[i],upper[j])
                if not same or j<i:contained=True;break
        if not contained:keep.append(i)
    assert keep
    return lower[keep],upper[keep],len(cells)

def route_world(world,state):
    result=dict(world);result['sensor_points']=[]
    if state['center']is None:
        return result,dict(status='NO_DETECTION_NO_PROJECTION',hidden_world_geometry_used=False)
    assert world['rectangles'][-1]==state['current_outer_rectangle'],'CURRENT_OCCUPANCY_MISSING'
    lo,hi,count=sweep_boxes(state)
    rectangles=np.c_[(lo+hi)/2,(hi-lo)/2+RADIUS].tolist()
    result['rectangles']=[*world['rectangles'],*rectangles]
    metadata=dict(status='STOPPING_HORIZON_REACHABLE_UNION_REFERENCE',horizon_s=HORIZON,
        original_joint_cells=count,retained_sweep_rectangles=len(rectangles),
        construction='per-cell continuous-time hull, discard contained boxes, outward radius square',
        current_causal_rectangle_retained=True,future_reference_is_hard_over_stopping_horizon=True,
        future_cost_is_soft=True,soft_heat_samples=7,soft_heat_horizon_s=6.56,
        heat_decay_s=3.28,heat_clearance_m=.30,heat_scale_m=1.,heat_edge_weight=1.,
        reference_has_no_execution_arrival_clock=True,all_actual_328_native_admission_unchanged=True,
        all_original_657_coverage_unchanged=True,reference_is_not_dynamic_execution_certificate=True,
        hidden_world_geometry_used=False,
        scope='Spatial stopping-room proposal at the current belief time only. Actual approach/braking and later arrival still require the original complete native certificate.')
    return result,metadata

def attach(field,state):
    # pose_values already uses the swept corridor world. Preserve V812's exact
    # seven-sample soft-cost ranking and its no-virtual-clock reference checker.
    field.stopping_reference=state['center']is not None
    return soft_attach(field,state)
