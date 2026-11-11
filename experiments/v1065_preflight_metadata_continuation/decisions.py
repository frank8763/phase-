"""Pure campaign gates; functional failure never substitutes a trial."""
FUNCTIONAL_ERRORS=('NO_ORIGINAL_GOAL_INPUT_SEED','NO_COMPLETE_OBSERVATION_APPROACH','SOURCE_PRODUCER_FAILED','SOURCE_MISSED_FIXED_HOLD_DEADLINE','FRESH_ORIGINAL_GOAL_AND_STOP','FRESH_ONE_METRE_AFTER_DISCOVERY','REAL_SENSOR_DISCOVERY_REQUIRED','FIXED_EPOCH_LIMIT','EXECUTION_OR_REPLAY_RESERVE','FULL_OWN_REPLAY_RESERVE')
def can_continue_after_failure(result,audit):
 return bool(not result['passed']and audit['safety_passed']and audit['prediction']['passed']and any(x in result.get('error','')for x in FUNCTIONAL_ERRORS))
def three_gate(rows,comparisons):
 cases=['NORTH_SOUTH','EAST_WEST','WEST_EAST']
 return all(any(r['task']['case_id']==case and r['task']['kind']==kind and r['passed']for r in rows)for case in cases for kind in ['main','repeat'])and len(comparisons)==3 and all(c['passed']for c in comparisons)
def confirmation_gate(rows,pool):
 if len(rows)!=24:return False
 good={r['task']['slot']for r in rows if r['passed']}
 if len(good)<23:return False
 return all(sum(x['slot']in good for x in pool if x['case_id']==case)>=7 for case in ['WEST_EAST','NORTH_SOUTH','EAST_WEST'])and all(sum(x['slot']in good for x in pool if x['initial_axis_motion_direction']==direction)>=11 for direction in ['POSITIVE_AXIS','NEGATIVE_AXIS'])
