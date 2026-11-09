"""Nominal route endpoint is not a dynamic execution certificate."""
from terminal_region import old_terminal_goal,ENDPOINT_RADIUS

def terminal_goal(goal,known,dynamic_polygon,configured_footprint):
    endpoint,proof=old_terminal_goal(goal,known)
    proof.update(reason='STATIC_TASK_TERMINAL_REFERENCE_ONLY',dynamic_execution_certified=False,observed_future_cost_used_for_route=dynamic_polygon is not None,endpoint_radius_m=.08,controller_tolerance_m=.20,worst_case_goal_distance_m=.28)
    return endpoint,proof
