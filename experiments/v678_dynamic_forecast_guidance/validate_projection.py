"""Zero-integration old packets and one locked initial geometric route."""
import os,sys,json,hashlib,time,signal,importlib.util,traceback
from pathlib import Path
import numpy as np
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
repo=Path(os.environ['PHASE_REPO']);src=Path(__file__).resolve().parent
from future_guide import route_world
from union_belief import future_cells
from exact_footprint import build
from planner import search
root=repo/'runs/v676_dynamic_canonical_commands/dev43_95000011_canonical/paired';r=repo/'runs/v678_dynamic_forecast_guidance';r.mkdir(exist_ok=True);out=r/'PRE_NAV_VALIDATION_RETRY02.json';assert not out.exists()
read=lambda p:json.loads(p.read_text());rows=[json.loads(s)for s in(root/'geometry_memory/motion_estimate.jsonl').read_text().splitlines()];assert len(rows)==881
started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PROJECTION_VALIDATION_180S')));signal.alarm(180);status='FAILED';error=None;maxexcess=-1e9;count=0;route=None;stats=None
try:
 for state in rows:
  world,meta=route_world({'rectangles':[],'circles':[],'sensor_points':[]},state);lo,hi=future_cells(state['outer_state_cells'],np.linspace(0,3.28,329));lower=np.asarray(meta['projected_center_lower']);upper=np.asarray(meta['projected_center_upper']);excess=float(max((lower-lo).max(),(hi-upper).max()));maxexcess=max(maxexcess,excess);assert excess<=1e-8,'PROJECTED_GUIDE_DOES_NOT_COVER_NATIVE_JOINT_CELLS';count+=1
 sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
 file=repo/'current/footprint_map_b70_v513.py';spec=importlib.util.spec_from_file_location('v678_readonly_geometry',file);F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
 old=read(root/'geometry_memory/planning_0000.json');world,meta=route_world(old['causal_input'],rows[0]);field=build(F,world);field.base_heuristic=F.base._heuristic_grid
 route,stats=search(field,old['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
 if stats['status']!='GLOBAL_GOAL_PATH':
  preferred=route;previous=stats;route,stats=search(field,old['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.155,budget=8.,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
  if route is None and preferred is not None:route,stats=preferred,dict(previous)
  stats['preferred_search']=previous
 assert route is not None,'NO_REGISTERED_PROJECTED_PATH'
 status='PASS'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
 signal.alarm(0);result={'status':status,'error':error,'elapsed_s':time.monotonic()-started,'packets':count,'future_grid_per_packet':329,'maximum_joint_cell_outside_projection_m':maxexcess,'initial_route':None if route is None else route.tolist(),'route_stats':stats,'simulation_integrations':0,'new_navigation_tasks':0,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in src.glob('*.py')},'input_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [root/'geometry_memory/motion_estimate.jsonl',root/'geometry_memory/planning_0000.json']},'scope':'proposal projection coverage and one geometric route; not native reachability or dynamic acceptance'};out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['source_sha256','input_sha256','initial_route']},indent=2));assert status=='PASS',error
