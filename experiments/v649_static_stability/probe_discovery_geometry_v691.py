"""One locked final-state spatial proposal probe, no rollout or robot step."""
import os,sys,json,importlib.util,hashlib
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);root=repo/'runs/v691_discovery_in_motion';pair=root/'moving_discovery01/paired';cell=pair/'geometry_memory';sys.path.insert(0,str(pair.parent/'source_snapshot'));sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from motion_tracker import install_time_gate
from task_planner import search
spec=importlib.util.spec_from_file_location('v691_saved_field',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
read=lambda p:json.loads(p.read_text());plan=read(cell/'planning_0408.json');state=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()][408];protocol=read(pair/'STATIC_PROTOCOL.json');world=plan['causal_input'];field=build(F,world);field.base_heuristic=F.base._heuristic_grid;install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
path,stats=search(field,plan['pose'],protocol['goal_xy'],world['wheel_base'],world['max_steer'],guard=.18,work_limit=4000,dense_requested_guard=True)
out={'status':'FIXED_CURRENT_ONLY_SPATIAL_PROBE','locked_step':408,'source_plan_sha256':hashlib.sha256((cell/'planning_0408.json').read_bytes()).hexdigest(),'original_projected_start_status':plan['stats']['status'],'current_joint_start_clearance_m':float(field.pose_values([plan['pose']])[0]),'spatial_search':stats,'path':None if path is None else path.tolist(),'new_navigation_tasks':0,'robot_integration_steps':0,'private_prediction_steps':0,'gradient_updates':0,'scope':'causal current-occupancy geometry only; no time parameterization, acceleration/actuator feasibility, retained tail or executed navigation proof'}
(root/'CURRENT_ONLY_SPATIAL_PROBE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='path'},indent=2))
