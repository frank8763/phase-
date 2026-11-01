"""Zero-integration fixed73 route and all saved extended causal coverage."""
import os,sys,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v693_discovery_renewal_preview';root.mkdir(exist_ok=True)
pair=repo/'runs/v691_discovery_in_motion/moving_discovery01/paired';cell=pair/'geometry_memory'
sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from future_guide import route_world,HORIZON
from union_belief import future_cells
from exact_footprint import build
from planner import search
spec=importlib.util.spec_from_file_location('v693_saved_field',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text());states=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()];config=read(pair/'DYNAMIC_PROTOCOL.json');protocol=read(pair/'STATIC_PROTOCOL.json');plan=read(cell/'planning_0073.json')
times=np.linspace(0,HORIZON,657);worst=-1e9;projection=-1e9
for state in states:
    truth=np.asarray(config['anchor_xy'])+np.sin((state['time']+times)*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy'])
    if state['center']is None:
        radius=np.maximum(0,3-np.sqrt(2)*.12*(state['time']+times));excess=float(np.max(radius-np.linalg.norm(truth-[-4.,-2.],axis=1)))
    else:
        low,high=future_cells(state['outer_state_cells'],times)
        excess=float(np.maximum(low-truth[:,None,:],truth[:,None,:]-high).max(axis=2).min(axis=1).max())
        _,metadata=route_world({'rectangles':[]},state);lo=np.asarray(metadata['projected_center_lower']);hi=np.asarray(metadata['projected_center_upper'])
        projection=max(projection,float(max(np.max(lo-low),np.max(high-hi))))
    worst=max(worst,excess)
world,metadata=route_world(plan['causal_input'],states[73]);field=build(F,world);field.base_heuristic=F.base._heuristic_grid
path,stats=search(field,plan['pose'],protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.18,work_limit=4000,dense_requested_guard=True)
if stats['status']!='GLOBAL_GOAL_PATH':
    path,stats=search(field,plan['pose'],protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.155,resolution=.05,heading_bins=144,work_limit=16000,dense_requested_guard=True)
checks={'registered_horizon':HORIZON==6.56,'all409_extended_truth_covered':len(states)==409 and worst<=1e-7,'all_extended_joint_cells_contained':projection<=1e-7,'fixed73_global_route':path is not None and stats['status']=='GLOBAL_GOAL_PATH','dense_route_floor':path is not None and stats['minimum_clearance_m']>=.155-1e-8}
out={'status':'PASS'if all(checks.values())else'FAIL','checks':checks,'saved_decision_frames':len(states),'finite_future_samples_per_frame':657,'maximum_evaluator_center_excess_m':worst,'maximum_joint_projection_excess_m':projection,'locked_step':73,'route':None if path is None else path.tolist(),'route_stats':stats,'causal_world':plan['causal_input'],'causal_route_world':world,'causal_state':states[73],'pose':plan['pose'],'metadata':metadata,'robot_integrations':0,'scope':'offline causal proposal and evaluator-only finite containment, no execution proof'}
(root/'PRE_NAV_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['route','causal_world','causal_route_world','causal_state']},indent=2));assert out['status']=='PASS'
