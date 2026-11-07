"""Two bounded robot model metadata reads, zero integration or control."""
import json
import os
from pathlib import Path
import time

import mujoco

R=Path(os.environ['PHASE_REPO']);OUT=R/'runs/v847_gpu_reference_diagnosis';deadline=float(os.environ['PHASE_MODEL_ABSOLUTE_DEADLINE']);assert time.time()<deadline
paths=[R/'runs/v842_staged_long_navigation/v843_main_slot02/paired/scene_model.mjb',R/'runtime/mk-mini/training/assets/mkmini_real/mkmini_mobile_manipulator_v1.xml'];rows=[]
for p in paths:
 m=mujoco.MjModel.from_binary_path(str(p))if p.suffix=='.mjb'else mujoco.MjModel.from_xml_path(str(p))
 row=dict(source=str(p.relative_to(R)),bodies=[],actuators=[])
 for name in ['left_front_wheel','right_front_wheel','left_rear_wheel','right_rear_wheel']:
  bid=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,name);geoms=[]
  for g in range(m.ngeom):
   if m.geom_bodyid[g]==bid and(m.geom_contype[g]or m.geom_conaffinity[g]):geoms.append(dict(type=int(m.geom_type[g]),size=m.geom_size[g].tolist()))
  row['bodies'].append(dict(name=name,mass=float(m.body_mass[bid]),geoms=geoms))
 for name in ['left_front_steer_act','right_front_steer_act','left_rear_wheel_act','right_rear_wheel_act']:
  i=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,name);row['actuators'].append(dict(name=name,gear=m.actuator_gear[i].tolist(),gain=m.actuator_gainprm[i].tolist(),bias=m.actuator_biasprm[i].tolist(),limits=m.actuator_ctrlrange[i].tolist()))
 rows.append(row)
assert time.time()<deadline
(OUT/'ROBOT_METADATA.json').write_text(json.dumps(dict(records=rows,model_initializations=2,physics_integrations=0,scope='ROBOT_METADATA_ONLY_NOT_NEW_NAVIGATION'),indent=2)+'\n');print(json.dumps(rows),flush=True)
