"""Planner steering bound from the robot's own joints and actuators only.
This ideal Ackermann constraint is not a measured dynamics reachability proof.
The native rollout gate remains responsible for every actual command.
"""
import math

def planner_steering_bound(env, mj):
    entries = []
    for side in ('left', 'right'):
        jid = mj.mj_name2id(env.model, mj.mjtObj.mjOBJ_JOINT, f'{side}_front_steer_joint')
        aid = mj.mj_name2id(env.model, mj.mjtObj.mjOBJ_ACTUATOR, f'{side}_front_steer_act')
        assert jid >= 0 and aid >= 0
        assert env.model.jnt_limited[jid] and env.model.actuator_ctrllimited[aid]
        entries.append({'joint':f'{side}_front_steer_joint', 'joint_range':env.model.jnt_range[jid].tolist(), 'actuator_range':env.model.actuator_ctrlrange[aid].tolist()})
    wheel_limit = min(abs(v) for entry in entries for key in ('joint_range','actuator_range') for v in entry[key])
    wheel_base = float(env.inner.wheel_base)
    track_width = float(env.inner.track_width)
    assert wheel_base > 0 and track_width > 0 and 0 < wheel_limit < math.pi/2
    center_limit = math.atan(wheel_base/(wheel_base/math.tan(wheel_limit)+track_width/2))
    bound = min(center_limit, float(env.inner.max_steer))
    return bound, {'steering':entries, 'wheel_base_m':wheel_base, 'track_width_m':track_width, 'ideal_ackermann_center_angle_limit_rad':bound, 'controller_steer_candidate_limit_rad':float(env.inner.max_steer), 'source':'robot joint and actuator limits; no obstacle truth', 'limitation':'ideal geometry constraint, not measured native dynamics feasibility'}
