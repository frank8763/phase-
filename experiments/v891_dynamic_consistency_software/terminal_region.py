"""One fixed goal-region search consistent with the causal dynamic occupancy."""
import copy,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v881_timing_accounting_continuation'))
from planner_proxy import field,pose_values,yaw,terminal_goal as old_terminal_goal
from reproduce import intersects,footprint
GOAL_RADIUS=.45
CONTROLLER_TOLERANCE=.20
ENDPOINT_RADIUS=.24  # .24+.20=.44 < original .45 strict arrival region.
OFFSETS=[(0.,0.)]+[(r*math.cos(a),r*math.sin(a))for r in [.08,.16,.24]for a in np.arange(16)*2*math.pi/16]

def terminal_goal(goal,known,dynamic_polygon,configured_footprint):
    if dynamic_polygon is None:
        out,proof=old_terminal_goal(goal,known)
        proof.update(reason='UNSEEN_ORIGINAL_STATIC_TERMINAL',controller_tolerance_m=CONTROLLER_TOLERANCE,worst_case_goal_distance_m=.08+CONTROLLER_TOLERANCE,geometry_truth_used=False)
        return out,proof
    candidates=[[goal.pose.position.x+dx,goal.pose.position.y+dy,yaw(goal)]for dx,dy in OFFSETS]
    clear=pose_values(field(known),candidates);valid=[];rows=[]
    for i,values in enumerate(candidates):
        p=copy.deepcopy(goal);p.pose.position.x=values[0];p.pose.position.y=values[1]
        static_ok=float(clear[i])>=.15+.005
        dynamic_ok=dynamic_polygon is None or not intersects(footprint(p,configured_footprint),dynamic_polygon)
        rows.append(dict(offset=list(OFFSETS[i]),static_lower_m=float(clear[i]),static_ok=static_ok,dynamic_ok=dynamic_ok))
        if static_ok and dynamic_ok:valid.append(i)
    if not valid:return None,dict(reason='NO_ADMISSIBLE_TERMINAL_WAIT',candidate_count=len(candidates),candidates=rows,geometry_truth_used=False)
    # Same static-clearance preference among admissible candidates; stable tie break.
    i=max(valid,key=lambda j:(float(clear[j]),-math.hypot(*OFFSETS[j]),-j))
    out=copy.deepcopy(goal);out.pose.position.x=candidates[i][0];out.pose.position.y=candidates[i][1]
    return out,dict(reason='ADMISSIBLE_TERMINAL',selected_xy=candidates[i][:2],displacement_m=math.hypot(*OFFSETS[i]),public_static_clearance_m=float(clear[i]),candidate_count=len(candidates),admissible_count=len(valid),endpoint_radius_m=ENDPOINT_RADIUS,controller_tolerance_m=CONTROLLER_TOLERANCE,worst_case_goal_distance_m=ENDPOINT_RADIUS+CONTROLLER_TOLERANCE,candidates=rows,geometry_truth_used=False)
