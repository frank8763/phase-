"""Continuous interpolated-pose static clearance, not dynamics feasibility."""
import hashlib,json,math,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'experiments/v793_complete_joint_navigation'))
from exact_footprint import pose_values
root=repo/'runs/v796_corridor_cem_continuation'
assert(repo/'REVIEW_PENDING').exists()and not(root/'CONTINUOUS_PATH_STATIC_CHECK.json').exists()
path_file=repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory/planning_0153.json'
d=json.loads(path_file.read_text());protocol=json.loads((path_file.parent.parent/'STATIC_PROTOCOL.json').read_text())
p=np.asarray(d['path']);half=np.array([.44,.375]);radius=float(np.linalg.norm(half))
field=SimpleNamespace(half=half,center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
dense=[]
for a,b in zip(p[:-1],p[1:]):
    dyaw=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi
    for f in np.arange(5)/5:dense.append([*(a[:2]+f*(b[:2]-a[:2])),a[2]+f*dyaw])
dense.append(p[-1,:3]);dense=np.asarray(dense)
clearance=pose_values(field,dense)
dyaw=(np.diff(dense[:,2])+np.pi)%(2*np.pi)-np.pi
# Distance from any interpolated body to the nearer endpoint body is bounded
# by half the translation plus the rotation Hausdorff chord of the full box.
gaps=np.linalg.norm(np.diff(dense[:,:2],axis=0),axis=1)/2+2*radius*np.sin(abs(dyaw)/4)
bound=float(clearance.min()-gaps.max())
original_lengths=np.linalg.norm(np.diff(p[:,:2],axis=0),axis=1)
original_yaw=(np.diff(p[:,2])+np.pi)%(2*np.pi)-np.pi
result=dict(status='CONTINUOUS_INTERPOLATED_POSE_STATIC_GEOMETRY_VERIFIED'if bound>=.15 else'CONTINUOUS_GEOMETRY_NOT_CERTIFIED',
    source=str(path_file.relative_to(repo)),source_sha256=hashlib.sha256(path_file.read_bytes()).hexdigest(),
    original_path_points=len(p),dense_poses=len(dense),full_body_half_m=half.tolist(),
    minimum_dense_static_clearance_m=float(clearance.min()),maximum_between_pose_hausdorff_m=float(gaps.max()),
    continuous_interpolated_static_clearance_lower_m=bound,
    all_forward_gears=bool(np.all(p[:,3]==1)),maximum_sample_yaw_per_chord_m_inv=float(np.max(abs(original_yaw)/original_lengths)),
    ideal_reference_steering_bound_rad=json.loads((path_file.parent.parent/'PLANNER_CONTROL_CONTRACT.json').read_text())['ideal_ackermann_center_angle_limit_rad'],
    does_not_prove_native_dynamics_tracking=True,does_not_include_unseen_or_dynamic_actor=True,
    no_all_control_impossibility_claim=True,models=0,integrations=0)
(root/'CONTINUOUS_PATH_STATIC_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
