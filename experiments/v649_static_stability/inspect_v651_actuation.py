"""Zero-step structural actuation audit of a recorded scene; evaluator only."""
import json, math, os
from pathlib import Path
import mujoco

repo = Path(os.environ['PHASE_REPO'])
pair = repo/'runs/v650_static_acceptance/confirm_93000074_legacy_two/paired'
model = mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'))
world = json.loads((pair/'geometry_memory/planning_0098.json').read_text())['causal_input']
rows = []
for side in ['left', 'right']:
    jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, f'{side}_front_steer_joint')
    aid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, f'{side}_front_steer_act')
    rows.append({'joint':f'{side}_front_steer_joint', 'joint_limits_rad':model.jnt_range[jid].tolist(), 'actuator_limits_rad':model.actuator_ctrlrange[aid].tolist()})
bound = min(min(abs(x) for x in r[k]) for r in rows for k in ['joint_limits_rad','actuator_limits_rad'])
wheel_base = world['wheel_base']
# Track width is a documented robot dimension, not obstacle or scene geometry.
track_width = .54
center_bound = math.atan(wheel_base/(wheel_base/math.tan(bound)+track_width/2))
out = {'steering':rows, 'wheel_base_m':wheel_base, 'track_width_m':track_width, 'minimum_wheel_steering_limit_rad':bound, 'ideal_ackermann_center_angle_at_inner_wheel_limit_rad':center_bound, 'planner_argument_from_runner_rad':math.radians(35), 'planner_maximum_kinematic_curvature_per_m':math.tan(math.radians(35))/wheel_base, 'ideal_joint_limit_consistent_maximum_curvature_per_m':math.tan(center_bound)/wheel_base, 'simulation_steps':0, 'scope':'Structural mismatch diagnostic only; differential wheel forces/slip and controller lag mean this is not a measured dynamics turning-radius certificate.'}
dest = repo/'runs/v651_static_progress/ACTUATION_STRUCTURE_AUDIT.json'
dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
