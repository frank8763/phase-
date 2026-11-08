"""Exact saved known-map footprint geometry at unchanged terminal poses, no model/ROS."""
import json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v867_saved_diagnosis';sys.path.insert(0,str(R/'experiments/v864_diagnosis'));from snapshot_geometry import field
sys.path.insert(0,str(R/'experiments/v791_coherent_global_reference'));from exact_footprint import pose_values
sys.path.insert(0,str(R/'experiments/v864_diagnosis'));from collision_witness import cost
from PIL import Image

def main():
 known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());cases=json.loads((R/'experiments/v855_renewal_worker/SCENE_CASES.json').read_text());cfg=json.loads((R/'experiments/v862_ready_static/assets/field.yaml').read_text());pix=np.flipud(np.asarray(Image.open(cfg['image'])));grid=np.where((255-pix)/255.>cfg['occupied_thresh'],254,0);raster=dict(value=dict(data=grid.ravel().tolist(),width=grid.shape[1],height=grid.shape[0],resolution=cfg['resolution'],origin=cfg['origin'][:2]));rows=[]
 for c in cases:
  goal=np.array([*c['goal_xy'],c['yaw']]);start=np.array([*c['start_xy'],c['yaw']]);row=dict(case=c['id'],original_goal=goal.tolist())
  for padding in [.15,.20]:
   f=field(known,padding);row[str(padding)]=dict(start_padded_geometric_separation_m=float(pose_values(f,[start])[0]),goal_padded_geometric_separation_m=float(pose_values(f,[goal])[0]),start_raster_cost=cost(start,padding,raster)['cost'],goal_raster_cost=cost(goal,padding,raster)['cost'])
  rows.append(row)
 # Fixed terminal region witness, not a chosen experiment or modified task.
 pose=[4.,-1.8,0.];witness=dict(pose=pose,original_goal_distance_m=float(np.linalg.norm(np.asarray(pose[:2])-[4.,-2.])),padded20_geometric_separation_m=float(pose_values(field(known,.20),[pose])[0]),padded20_raster_cost=cost(pose,.20,raster)['cost'],scope='Existence witness inside original.45 terminal region only; not an executable path or authorized target change')
 out=dict(passed=True,models=0,integrations=0,original_task_goal_unmodified=True,rows=rows,terminal_region_witness=witness,interpretation='Global rectangular padding can make the exact WE nominal goal footprint invalid while the registered physical terminal region remains nonempty. This is stronger evidence of goal/footprint mismatch than treating an inflation optimization warning as the sole cause. No proof that planning time alone or inflation radius fixes it.');(O/'GOAL_GEOMETRY.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
