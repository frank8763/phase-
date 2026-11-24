"""Audit exact original mapping, including one terminal unapplied refusal.

This never returns a usable command for a refused proposal. Actual trajectory,
control, memory, geometry, source, stop and replay checks remain in the caller.
"""
ALLOWED={
 'TEB_RAW_CURVATURE_OUTSIDE_COMMON_CAP',
 'TEB_RAW_SPEED_IN_BRAKING_DEADBAND',
 'TEB_IN_PLACE_ROTATION_REFUSED',
}

def verify(frames,answer,config,row,first,is_last):
 assert answer['passed'] is True and row['query_returned'] is True
 assert row['native_answer']==answer,'AUDIT_RAW_RESPONSE_MISMATCH'
 try:
  mapped=frames.command(answer['proposal'],config)
 except AssertionError as error:
  assert str(error) in ALLOWED,'UNQUALIFIED_MAPPING_REFUSAL'
  assert is_last is True,'MAPPING_REFUSAL_MUST_BE_LAST_QUERY'
  assert first is not None and first['stage']=='normal' and first['error']==repr(error),'CANONICAL_MAPPING_REFUSAL_MISMATCH'
  assert type(row['executed_native'])is int and row['executed_native']==0,'REFUSED_MAPPING_ALREADY_EXECUTED'
  assert not any(k in row for k in ['command','original_ROS_saturation_explicit_port','reference_trajectory_body_centre','admissions','proof','kind']),'REFUSED_MAPPING_HAS_ACCEPTED_COMMAND'
  return dict(refused_unapplied=True,original_error=repr(error),command_returned=False,canonical_error_preserved=True)
 assert row['command']==mapped['body_request'][:2] and row['original_ROS_saturation_explicit_port']==mapped
 assert row['reference_trajectory_body_centre']==frames.trajectory(answer['proposal'],config)
 return dict(refused_unapplied=False,original_success_mapping_unchanged=True)
