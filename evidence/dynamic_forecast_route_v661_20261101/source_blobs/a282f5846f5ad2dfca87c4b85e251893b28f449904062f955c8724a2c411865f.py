"""Evaluator-only control replay with the exact prescribed mocap time input."""
import argparse,hashlib,json,math,signal,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
import sys,os
sys.path.insert(0,str(Path(os.environ['PHASE_REPO'])/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from instrumentation import dump
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--condition',default='geometry_memory');a=p.parse_args()
root=Path(a.paired);cell=root/a.condition;started=time.monotonic()
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('DYNAMIC_REPLAY_30S')));signal.alarm(30)
protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text());config=json.loads((root/'DYNAMIC_PROTOCOL.json').read_text());motion=Motion(config)
rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];result=json.loads((cell/'result.json').read_text())
m=mujoco.MjModel.from_binary_path(str(root/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];d.qvel[:]=0.;motion.apply(m,d);mujoco.mj_forward(m,d)
geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,root/'assets/isolated_indoor.xml')
minimum=float('inf');margin=float('inf');below=0;contacts=0;unknown=0;steps=0;worst_q=0.;worst_v=0.;worst_mocap=0.;status='FAILED';error=None
try:
 for row in rows:
  d.ctrl[:]=row['ctrl']
  for _ in range(8):
   mujoco.mj_step(m,d);motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);steps+=1
   bounds=geometry.actual(m,d);q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
   field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,
       rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray([*protocol['known_circles'],[*motion.xy(d.time),config['radius_m']]]).reshape(-1,3),
       sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
   clearance=float(pose_values(field,[[q[0],q[1],yaw]])[0]);minimum=min(minimum,clearance);below+=int(clearance<.15-1e-8)
   margin=min(margin,float(containment_margin(bounds,protocol['footprint_bounds'])))
   for c in d.contact:
    kind=catalog.classify(c,steps,row['step'],float(d.time))['contact_type']
    contacts+=int(kind in ['robot_obstacle_contact','robot_obstacle_penetration']);unknown+=int(kind=='unknown_contact')
  worst_q=max(worst_q,float(np.max(abs(d.qpos-row['qpos_full']))));worst_v=max(worst_v,float(np.max(abs(d.qvel-row['qvel_full']))))
  worst_mocap=max(worst_mocap,float(np.max(abs(d.mocap_pos-row['mocap_pos']))))
  assert max(worst_q,worst_v,worst_mocap)<=1e-8,'FULL_DYNAMIC_REPLAY_MISMATCH'
 assert steps==result['physics_steps']==8*result['public_steps']
 status='MATCHED_RECORDED_PUBLIC_STATES'
except BaseException as e:error={'type':type(e).__name__,'message':str(e)}
finally:
 signal.alarm(0)
 output={'status':status,'error':error,'condition':a.condition,'replay_integration_steps':steps,'new_navigation_trials':0,
         'maximum_full_public_qpos_error':worst_q,'maximum_full_public_qvel_error':worst_v,'maximum_public_mocap_error':worst_mocap,
         'minimum_reconstructed_native_actual_axis_AABB_clearance_m':minimum if status.startswith('MATCHED')else None,
         'reconstructed_native_states_below_015':below,'minimum_reconstructed_self_domain_margin_m':margin if status.startswith('MATCHED')else None,
         'replay_obstacle_contact_records':contacts,'replay_unknown_contact_records':unknown,
         'scene_model_sha256':hashlib.sha256((root/'scene_model.mjb').read_bytes()).hexdigest(),'elapsed_s':time.monotonic()-started,
         'scope':'dynamic evaluator-only prescribed mocap replay; not another independent navigation task or continuous-time guarantee'}
 dump(root/'NATIVE_REPLAY_AUDIT.json',output);print(json.dumps(output,indent=2))
