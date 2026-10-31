"""Offline control-log replay for native-state clearance reconstruction.
This performs physics integration and is charged as replay, never as a new trial.
It certifies no replay metric unless every recorded full public qpos/qvel matches.
World truth is evaluator-only, never an input to an online decision.
"""
import argparse,hashlib,json,math,signal,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from instrumentation import dump
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--condition',default='geometry_memory');p.add_argument('--interrupted',action='store_true');a=p.parse_args();root=Path(a.paired);cell=root/a.condition
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *args:(_ for _ in()).throw(TimeoutError('30S_REPLAY_BUDGET')));signal.alarm(30)
protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text());recorded=[json.loads(x)for x in(cell/'v648_execution.jsonl').read_text().splitlines()];result=json.loads((cell/('interrupted.json' if a.interrupted else 'result.json')).read_text());m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m)
d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;d.ctrl[:]=0.;mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco)
field=SimpleNamespace(half=None,center_local=None,rectangles=np.array(protocol['known_rectangles']).reshape(-1,4),circles=np.array(protocol['known_circles']+[[*x['xy'],x['radius']]for x in protocol['physical_unknown_obstacles']]).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
minimum=float('inf');below=0;steps=0;worst_q=0.;worst_v=0.;obstacle_contacts=0;domain_margin=float('inf');status='FAILED';error=None
try:
 for row in recorded:
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);steps+=1;mujoco.mj_kinematics(m,d);b=geometry.actual(m,d);field.half=(b[2:]-b[:2])/2;field.center_local=(b[2:]+b[:2])/2;q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
   clearance=float(pose_values(field,[[q[0],q[1],yaw]])[0]);minimum=min(minimum,clearance);below+=int(clearance<.15-1e-8);domain_margin=min(domain_margin,float(containment_margin(b,protocol['footprint_bounds'])))
   for contact in d.contact:
    ga,gb=int(contact.geom1),int(contact.geom2);ba,bb=int(m.geom_bodyid[ga]),int(m.geom_bodyid[gb])
    if (ba>0)!=(bb>0):
     other=ga if ba==0 else gb
     if int(m.geom_type[other])!=int(mujoco.mjtGeom.mjGEOM_PLANE):obstacle_contacts+=1
  eq=float(np.max(abs(d.qpos-row['qpos_full'])));ev=float(np.max(abs(d.qvel-row['qvel_full'])));worst_q=max(worst_q,eq);worst_v=max(worst_v,ev)
  if eq>1e-8 or ev>1e-8:raise RuntimeError(f'FULL_STATE_REPLAY_MISMATCH_PUBLIC_STEP_{row["step"]}:q={eq},v={ev}')
 assert steps==result['physics_steps']==8*result['public_steps']
 status='MATCHED_RECORDED_PUBLIC_STATES'
except BaseException as e:error={'type':type(e).__name__,'message':str(e)}
finally:
 signal.alarm(0)
 output={'status':status,'error':error,'condition':a.condition,'replay_integration_steps':steps,'new_navigation_trials':0,'maximum_full_public_qpos_error':worst_q,'maximum_full_public_qvel_error':worst_v,'minimum_reconstructed_native_actual_axis_AABB_clearance_m':minimum if status.startswith('MATCHED')else None,'reconstructed_native_states_below_015':below if status.startswith('MATCHED')else None,'minimum_reconstructed_self_domain_margin_m':domain_margin if status.startswith('MATCHED')else None,'replay_obstacle_contact_records':obstacle_contacts,'scene_model_sha256':hashlib.sha256((root/'scene_model.mjb').read_bytes()).hexdigest(),'recorded_state_log_sha256':hashlib.sha256((cell/'v648_execution.jsonl').read_bytes()).hexdigest(),'elapsed_s':time.monotonic()-started,'scope':__doc__,'limits':'reconstruction from recorded constant-per-public-step controls and t0 state; public-state match is an empirical replay validation, not independent trial or continuous-time safety proof'}
 dump(root/'NATIVE_REPLAY_AUDIT.json',output);print(json.dumps(output,indent=2))
