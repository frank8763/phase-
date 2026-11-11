"""Post-close saved-only pairing proves forecast change, not plant/controller change."""
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1044_curvature_speed_prediction';old=R/'runs/v1043_speed_predictor_identification/input/selected';new=R/'runs/v858_nav2_verified/v1044';rows=[]
for task,n in [('straight',500),('left',343)]:
 a=np.load(old/task/'physics/NATIVE_TRACE.npz');b=np.load(new/task/'physics/NATIVE_TRACE.npz');maximum=0.
 for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  x=a[key];y=b[key][:n];assert x.shape==y.shape
  if x.size:maximum=max(maximum,float(abs(x-y).max()))
 sa=json.loads((old/task/'physics/SETUP.json').read_text());sb=json.loads((new/task/'physics/SETUP.json').read_text());assert sa['model_sha256']==sb['model_sha256']and maximum<=1e-8
 rows.append(dict(task=task,paired_native=n,maximum_qpos_qvel_ctrl_mocap_error=maximum,model_sha_equal=True))
result=dict(passed=True,rows=rows,models=0,integrations=0,meaning='only predictor changed; original physical prefixes and controller outputs reproduced exactly',new_samples_beyond_old_failure=dict(left_tail_native=157,right_native=500))
(O/'UNCHANGED_PLANT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
