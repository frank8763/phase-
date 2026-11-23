"""Pure route authority shared by owner and native admission; no model imports."""
def qualified(task,variant):
 assert task['case_id']=='EAST_WEST'and variant in {'full','no_time'},'FORMAL_ROUTE_BACKEND_NOT_QUALIFIED'
 assert task['scope']=='same_known_course_new_phase_only'and task['slot']is None
 assert task['sensor_seed_unchanged']and task['from_actual_native_zero']and task['historical_prefix_native']==0
 return True
