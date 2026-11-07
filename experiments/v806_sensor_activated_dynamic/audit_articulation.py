"""Offline reconstruction from recorded full qpos; zero integration steps.
Hidden world geometry is evaluator-only. Public samples cannot certify the
continuous trajectory; physical contact recording covers native physics ticks.
"""
import argparse,json,math,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
from self_envelope import extract_self_envelope
from self_geometry import SelfGeometry
from exact_footprint import pose_values
p=argparse.ArgumentParser();p.add_argument('paired');a=p.parse_args();root=Path(a.paired)
protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text());model=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));data=mujoco.MjData(model)
env=SimpleNamespace(model=model,data=data,inner=SimpleNamespace(max_steer=0,max_wheel_delta=0))
actual_axis_geometry=SelfGeometry(model,mujoco)
initial=np.array(protocol['footprint_bounds']);worldcircles=protocol['known_circles']+[[*x['xy'],x['radius']]for x in protocol['physical_unknown_obstacles']]
rows=[];started=time.monotonic()
for execution in sorted(root.glob('*/v648_execution.jsonl')):
    entries=[json.loads(x)for x in execution.read_text().splitlines()];margins=[];axis_margins=[];escapes=[];bounds=[];max_velocity=0
    for e in entries:
        data.qpos[:]=e['qpos_full'];data.qvel[:]=e['qvel_full'];mujoco.mj_forward(model,data)
        b=np.asarray(extract_self_envelope(env,mujoco)['bounds_xy']);bounds.append(b)
        escapes.append(float(max(0,*(initial[:2]-b[:2]),*(b[2:]-initial[2:]))))
        q=data.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
        field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.array(protocol['known_rectangles']).reshape(-1,4),circles=np.array(worldcircles).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
        margins.append(float(pose_values(field,[[q[0],q[1],yaw]])[0]));max_velocity=max(max_velocity,float(np.linalg.norm(data.qvel[:2])))
        actual_b=actual_axis_geometry.actual(model,data);field.half=(actual_b[2:]-actual_b[:2])/2;field.center_local=(actual_b[2:]+actual_b[:2])/2
        axis_margins.append(float(pose_values(field,[[q[0],q[1],yaw]])[0]))
    if not margins:continue
    row={'condition':execution.parent.name,'public_samples':len(margins),'legacy_sphere_envelope_escape_from_planning_domain_m':max(escapes),'legacy_sphere_samples_exceed_planning_domain_1e_5m':sum(x>1e-5 for x in escapes),'minimum_legacy_rotation_sphere_envelope_clearance_m':min(margins),'legacy_sphere_public_samples_below_015':sum(x<.15 for x in margins),'minimum_actual_axis_projected_self_AABB_clearance_m':min(axis_margins),'actual_axis_public_samples_below_015':sum(x<.15 for x in axis_margins),'maximum_root_xy_speed_m_s':max_velocity,'legacy_sphere_observed_union_bounds_xy':[*np.min(np.asarray(bounds)[:,:2],axis=0),*np.max(np.asarray(bounds)[:,2:],axis=0)]}
    row={k:(v.item()if isinstance(v,np.generic)else v)for k,v in row.items()};rows.append(row)
result={'scope':'offline full-qpos robot geometry at public samples; actual_axis uses exact axis-dependent primitive support AABB; legacy_sphere uses the older rotation-invariant cylinder sphere proxy and may be overconservative; no integration or planner truth access, not continuous-time clearance certification','rows':rows,'elapsed_s':time.monotonic()-started,'navigation_steps':0}
(root/'ARTICULATION_AUDIT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
