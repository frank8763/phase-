"""Zero-physics property checks against the frozen bounded sensor model."""
import ast,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from perception import measured_points
repo=Path(__file__).resolve().parents[2]
source=repo/'runtime/home/mkmini_g11b_budget162_confirmatory_v1_1/g11b_budget162_confirmatory_v1.py'
values={}
for n in ast.parse(source.read_text()).body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id in {'LIDAR_CLIP_M','DEPTH_CLIP_M'}:values[t.id]=ast.literal_eval(n.value)
assert values=={'LIDAR_CLIP_M':.06,'DEPTH_CLIP_M':.09}
e=SimpleNamespace(robot_xy=np.zeros(2),robot_yaw=0.,phase17c_lidar_max_range=3.,phase17c_depth_max_range=3.)
cases=[]
for bound,channel in [(.06,'lidar'),(.09,'depth')]:
 for epsilon in np.linspace(-bound,bound,1001):
  e.phase17c_last_lidar=np.ones(32);e.phase17c_last_depth=np.ones(15)
  getattr(e,'phase17c_last_'+channel)[0]=np.clip(3.+epsilon,0,3)/3
  new,_,_=measured_points(e,bounded=True)
  assert len(new)==0,'NO_HIT_BECAME_OCCUPIED'
 cases.append({'channel':channel,'bounded_no_hit_cases':1001,'spurious_occupied_endpoints':0})
e.phase17c_last_lidar=np.ones(32);e.phase17c_last_depth=np.ones(15)
e.phase17c_last_lidar[0]=.5/3;e.phase17c_last_depth[7]=.5/3
points,_,_=measured_points(e,bounded=True);assert np.allclose(points,[[.5,0],[.5,0]],atol=1e-12)
result={'status':'PASS','cases':cases,'declared_bounds_match_frozen_source':True,'central_ray_projection_checked':True,'simulation_steps':0,'scope':'no-hit classification under this bounded corruption model only; not a navigation safety guarantee'}
out=repo/'runs/v648_static_unknown/perception_contract_check.json';out.write_text(json.dumps(result,indent=2));print(json.dumps(result))
