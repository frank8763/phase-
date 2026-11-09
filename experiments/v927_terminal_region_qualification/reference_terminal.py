"""Fixed inner terminal choices within the original .45m arrival region."""
import copy,math
import numpy as np
from planner_proxy import field,pose_values,yaw
ENDPOINT_RADIUS=.20
OFFSETS=[(0.,0.)]+[(.20*math.cos(a),.20*math.sin(a))for a in np.arange(16)*2*math.pi/16]
def terminal_goal(goal,known,dynamic_polygon,configured_footprint):
    poses=[[goal.pose.position.x+dx,goal.pose.position.y+dy,yaw(goal)]for dx,dy in OFFSETS]
    clear=pose_values(field(known),poses);i=max(range(len(poses)),key=lambda j:(float(clear[j]),-math.hypot(*OFFSETS[j]),-j));out=copy.deepcopy(goal);out.pose.position.x=poses[i][0];out.pose.position.y=poses[i][1]
    return out,dict(selected_xy=poses[i][:2],displacement_m=math.hypot(*OFFSETS[i]),public_static_clearance_m=float(clear[i]),candidate_count=len(poses),endpoint_radius_m=.20,controller_tolerance_m=.20,worst_case_goal_distance_m=.40,original_goal_radius_m=.45,geometry_truth_used=False,dynamic_execution_certified=False)
