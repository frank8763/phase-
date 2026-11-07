"""Observation-triggered upgrade of a partial goal reference; no control authority."""
import math
import numpy as np

def evaluate(field,current,goal,state,step,last_plan,reference_kind):
    if reference_kind!='SAFE_PROGRESS_PREFIX' or state.get('center') is None or not state.get('observed_this_frame',False) or step-last_plan<12:
        return None
    field.free=field.clearance>=.15-field.config.resolution/math.sqrt(2)
    guide=field.base_heuristic(field,np.asarray(goal,float))
    index=field.indices([np.asarray(current,float)[:2]])[0]
    inside=bool(guide is not None and(index>=0).all()and(index<guide.shape).all())
    value=float(guide[tuple(index)])if inside else math.inf
    connected=bool(math.isfinite(value))
    return dict(step=int(step),last_plan=int(last_plan),active_reference_kind=reference_kind,
        observed_this_frame=True,observation_age_s=float(state['age_s']),minimum_plan_interval_public=12,
        goal_guide_finite=connected,goal_guide_m=value if connected else None,should_replan=connected,
        source='current causal map, actual root pose, original public goal and new actual range packet',
        reference_only=True,authorizes_control=False,complete_328_gate_unchanged=True,hidden_world_geometry_used=False)
