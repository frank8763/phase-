"""Full robot/support model comparison by robot geom order, zero integrations."""
import os,json,hashlib
from pathlib import Path
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v687_control_curriculum'
old=mujoco.MjModel.from_binary_path(str(repo/'runs/v686_dynamic_open_curriculum/open01/paired/scene_model.mjb'));actor=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_BODY,'phase_dynamic_actor')
records=[]
for file in sorted(root.glob('*/paired/geometry_memory/result.json')):
 pair=file.parents[1];m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));checks={'state_actuator_dimensions':(m.nq,m.nv,m.nu)==(old.nq,old.nv,old.nu),'only_actor_body_absent':m.nbody==old.nbody-1 and actor==old.nbody-1 and m.nmocap==0}
 for k in ['body_pos','body_quat','body_mass','body_inertia','body_ipos','body_iquat']:checks[k]=bool(np.array_equal(getattr(m,k),getattr(old,k)[:m.nbody]))
 for k in ['qpos0','dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_forcerange','actuator_ctrlrange','jnt_range','jnt_limited']:checks[k]=bool(np.array_equal(getattr(m,k),getattr(old,k)))
 own=np.flatnonzero(m.geom_bodyid>0);prior=np.flatnonzero((old.geom_bodyid>0)&(old.geom_bodyid!=actor))
 checks['same_robot_geom_body_attachment']=bool(np.array_equal(m.geom_bodyid[own],old.geom_bodyid[prior]))
 for k in ['geom_type','geom_pos','geom_quat','geom_size','geom_friction','geom_solref','geom_solimp','geom_margin','geom_gap','geom_contype','geom_conaffinity']:checks['robot_'+k]=bool(np.array_equal(getattr(m,k)[own],getattr(old,k)[prior]))
 floor=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'floor');previous_floor=mujoco.mj_name2id(old,mujoco.mjtObj.mjOBJ_GEOM,'floor')
 for k in ['geom_friction','geom_solref','geom_solimp','geom_type','geom_pos','geom_size']:checks['floor_'+k]=bool(np.array_equal(getattr(m,k)[floor],getattr(old,k)[previous_floor]))
 for k in ['timestep','integrator','solver','iterations','tolerance','cone','jacobian','gravity']:checks['opt_'+k]=bool(np.array_equal(getattr(m.opt,k),getattr(old.opt,k)))
 records.append({'run':str(pair.relative_to(repo)),'passed':all(checks.values()),'checks':checks})
out={'status':'ALL_ROBOT_SUPPORT_PARAMETERS_UNCHANGED'if records and all(x['passed']for x in records)else'FAIL','records':records,'integration_steps':0,'scope':'vehicle/support parameters, not actor-only controlled ablation'}
(root/'COMPLETE_VEHICLE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'tasks':len(records),'failed_checks':[{k:v for k,v in x['checks'].items()if not v}for x in records]},indent=2));assert out['status']!='FAIL'
