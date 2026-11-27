"""One public-map-only kinematic route check, no models or actor geometry."""
from pathlib import Path
import os,json,hashlib,importlib.util,sys,time
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={4}and not(S/'PUBLIC_ROUTE_PREFLIGHT.json').exists()
old=R/'runs/v2144_sccr_depth_resource_units/components/SCCR/actual'
read=lambda p:json.loads(p.read_bytes())
setup=read(old/'physics/SETUP.json');body=read(old/'cycle_000000_origin.json')['receipt']['packet']['body'];task=read(S/'components/SCCR/PILOT_TASK.json')
assert np.array_equal(body[:2],task['start_xy'])and body[2]==task['start_yaw']
path=R/'experiments/v1370_overnight_controller_matrix/observed_route.py'
sp=importlib.util.spec_from_file_location('C2168_public_static_route',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
start=time.monotonic();route,report=m.propose(setup['known'],body,task['goal_xy'],None,guard=.22)
passed=route is not None;proof=None;converted=None
if passed:
 valid,proof=m.revalidate(setup['known'],route,body,None,guard=.22)
 converted=route[:,:2]+.3*np.column_stack([np.cos(route[:,2]),np.sin(route[:,2])])
 passed=bool(valid and np.linalg.norm(converted[0]-body[:2])<=1e-8)
v=dict(passed=passed,scope='PUBLIC_MAP_KINEMATIC_ROUTE_ONLY_NO_MODEL_OR_ACTOR_TRUTH',wall_s=time.monotonic()-start,report=report,revalidation=proof,original_virtual_rear_route=None if route is None else route.tolist(),body_center_polyline=None if converted is None else converted.astype(np.float32).tolist(),whole_goal_path_not_implied=True,planning_guard_not_changed=True,models=0,physics=0,neural_inference=0,source_once_claimed=False,source_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__),path,R/'experiments/v855_renewal_worker/task_planner.py',R/'experiments/v855_renewal_worker/exact_footprint.py']})
(S/'PUBLIC_ROUTE_PREFLIGHT.json').write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');print(json.dumps({k:x for k,x in v.items()if k not in ['original_virtual_rear_route','body_center_polyline','source_SHA256']}))
assert passed,'REGISTERED_PUBLIC_ROUTE_COMPONENT_NOT_READY'
