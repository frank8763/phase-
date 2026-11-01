"""Zero-integration check of the declared curriculum scene transformation."""
from pathlib import Path
import os,json,hashlib
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v686_dynamic_open_curriculum';pair=root/'open01/paired'
old=repo/'runs/v680_dynamic_later_stop_reserve/dev47_95000011_laterstop/paired/scene_model.mjb'
a=mujoco.MjModel.from_binary_path(str(old));b=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'))
checks={'same_robot_dimensions':(a.nq,a.nv,a.nu,a.ngeom,a.nbody)==(b.nq,b.nv,b.nu,b.ngeom,b.nbody)}
for key in ['body_pos','body_quat','body_mass','body_inertia','body_ipos','body_iquat','qpos0','dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','jnt_range','jnt_limited']:
 # Only mocap body's initial world anchor is intentionally changed.
 aa=getattr(a,key);bb=getattr(b,key)
 if key=='body_pos':aa=aa[:-1];bb=bb[:-1]
 checks[key]=bool(np.array_equal(aa,bb))
ids=np.flatnonzero(b.geom_bodyid!=0)
for key in ['geom_type','geom_pos','geom_quat','geom_size','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_contype','geom_conaffinity']:
 checks['robot_'+key]=bool(np.array_equal(getattr(a,key)[ids],getattr(b,key)[ids]))
for key in ['timestep','integrator','solver','iterations','tolerance','cone','jacobian','gravity']:
 checks['opt_'+key]=bool(np.array_equal(getattr(a.opt,key),getattr(b.opt,key)))
p=json.loads((pair/'STATIC_PROTOCOL.json').read_text());construction=json.loads((pair/'ARENA_CONSTRUCTION.json').read_text())
checks['empty_known_map']=p['known_rectangles']==p['known_circles']==[]
checks['declared_start_goal']=np.array_equal(np.asarray(p['start_qpos'])[:2],[-3.,-2.])and p['goal_xy']==[1.,-2.]
checks['twenty_physically_disabled']=len(construction['removed_static_geometries'])==20 and all(b.geom_contype[mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,name)]==0 and b.geom_conaffinity[mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,name)]==0 and b.geom_pos[mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,name),2]==-10 for name in construction['removed_static_geometries'])
out={'status':'PASS'if all(checks.values())else'FAIL','checks':{k:bool(v)for k,v in checks.items()},'integration_steps':0,'old_model':str(old.relative_to(repo)),'new_model':str((pair/'scene_model.mjb').relative_to(repo)),'scope':'declared new scene; unchanged robot/support physics, not same task or policy-learning comparison'}
(root/'VEHICLE_ARENA_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert all(checks.values())
