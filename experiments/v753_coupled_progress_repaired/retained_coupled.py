"""Generalize the validated observation cache to four predeclared targets only.
No simulator state writes; requires a complete admitted328 proof and real first8.
"""
import copy
import numpy as np

def prepare_retained(proof, real, command_map):
    """Return a proposed remaining320 cache; do not mutate a retained contract.

    The caller must keep the old proof until this succeeds, explicitly commit the
    returned controller metadata, and retain it on every failed future handover.
    This adapter alone does not authorize any actuator command.
    """
    assert proof['schema']=='V749_COUPLED_01'
    assert proof['total_native_ticks']==328 and proof['first_held_command_ticks']==8
    assert proof['brake_after_native_ticks']==168
    assert proof['hidden_world_geometry_used']is False
    state=proof['forecast_state'];assert state['center']is None and state['hidden_world_geometry_used']is False
    start=float(proof['start_time']);assert abs(float(state['time'])-start)<=1e-10
    q=np.asarray(proof['qpos'],float);v=np.asarray(proof['qvel'],float);poses=np.asarray(proof['poses'],float);controls=np.asarray(proof['controls'],float)
    prefix=np.asarray(proof['prefix_command'],float);target=np.asarray(proof['target'],float)
    assert q.shape==(328,len(real.qpos))and v.shape==(328,len(real.qvel))
    assert poses.shape==(328,3)and controls.shape==(328,4)
    assert all(np.isfinite(a).all()for a in[q,v,poses,controls,prefix,target])
    assert np.array_equal(target[:2],[0.,0.])and tuple(target[2:])in [(8.,-8.),(2.,2.),(-4.,8.),(8.,-4.)]
    expected=np.vstack([np.repeat([prefix],8,axis=0),command_map.sequence(target,prefix,320,160)])
    assert np.array_equal(controls,expected),'OBSERVATION_COMMAND_SCHEDULE_CHANGED'
    assert proof['minimum_causal_predicted_clearance_m']>=.155
    assert proof['minimum_predicted_self_domain_margin_m']>=.002
    assert np.linalg.norm(v[-1,:2])<=.025 and np.linalg.norm(v[-1,3:6])<=.025
    assert max(np.max(abs(real.qpos-q[7])),np.max(abs(real.qvel-v[7])))<=1e-8,'OBSERVATION_PREFIX_FULL_STATE_MISMATCH'
    assert abs(float(real.time)-start-.08)<=1e-9,'OBSERVATION_PREFIX_TIME_MISMATCH'
    assert np.max(abs(np.asarray(real.ctrl)[command_map.ids]-prefix))<=1e-12,'OBSERVATION_PREFIX_APPLIED_CTRL_MISMATCH'
    cache=dict(score=None,recovery_kind='COUPLED_OBSERVATION_BRAKE',created_step=int(proof['created_step']),created_time=start,start_time=start+.08,initial_qpos=q[7].copy(),initial_qvel=v[7].copy(),prefix_command=prefix.copy(),qpos=q[8:].copy(),qvel=v[8:].copy(),poses=poses[8:].copy(),controls=controls[8:].copy(),brake_after_native_ticks=160,forecast_state=copy.deepcopy(state),minimum_causal_predicted_clearance_m=float(proof['minimum_causal_predicted_clearance_m']),minimum_predicted_self_domain_margin_m=float(proof['minimum_predicted_self_domain_margin_m']),terminal_speed_m_s=float(np.linalg.norm(v[-1,:2])),terminal_angular_speed_rad_s=float(np.linalg.norm(v[-1,3:6])),signed_reverse_displacement_m=None,signed_longitudinal_displacement_m=None,target=target.copy(),prefix_poses=poses[:8].copy())
    evidence=dict(status='COUPLED_CACHE_PREPARED_REQUIRES_NATIVE_VERIFICATION',actual_prefix_native_steps=8,remaining_native_steps=320,original_full_native_steps=328,real_state_writes=0,new_geometry_or_sensor_information=False,requires_explicit_controller_metadata_commit=True)
    return cache,evidence
