"""Independent complete-pose polygon check and original margin accounting."""
import importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1023_dense_input_route';sys.path.insert(0,str(C));from geometry_model import ref,REQUIRED
s=importlib.util.spec_from_file_location('independent_polygons',R/'experiments/v938_rpccr_recovery_segments/independent_geometry.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
plan=json.loads((O/'we_initial.json').read_text());known=json.loads((R/'runs/v858_nav2_verified/v1020/PREFLIGHTS/we/SETUP.json').read_text())['known'];states=np.asarray(plan['state_path']);rects=[np.array([x,y])+g.SIGNS*np.array([hx,hy])for x,y,hx,hy in known['known_rectangles']];lowest=math.inf;start=time.monotonic()
for x,y,yaw in states[:,:3]:
 c,s=math.cos(yaw),math.sin(yaw);rotation=np.array([[c,-s],[s,c]]);body=g.SIGNS*g.HALF@rotation.T+[x,y];v=float(np.min(5-abs(body)))
 for rectangle in rects:v=min(v,g.polygon_distance(body,rectangle))
 for cx,cy,radius in known['known_circles']:
  d=np.array([cx-x,cy-y])@rotation;v=min(v,float(np.linalg.norm(np.maximum(abs(d)-g.HALF,0)))-radius)
 lowest=min(lowest,v)
assert abs(lowest-plan['minimum_raw_full_cycle_clearance_m'])<=1e-8
assert abs(REQUIRED-(.155+.04+math.hypot(.44,.375)*.035+.1*(.13+math.hypot(.44,.375)*.16)+.02*(.13+math.hypot(.44,.375)*.16+.08)))<=1e-14
out=dict(passed=lowest>=REQUIRED,all_predicted_native_states=len(states),independent_polygon_minimum_m=lowest,original_spatial_delay_and_20ms_reserves_m=ref._old.SPATIAL,required_raw_m=REQUIRED,
 unchanged_prediction_floor_m=.155,unchanged_physical_floor_m=.15,removed_only_sparse_geometric_reference_terms=True,models=0,integrations=0,wall_s=time.monotonic()-start)
(O/'MARGIN_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['passed']
