"""Zero-integration route-only counterfactual on fixed saved causal inputs.

Does not create or deploy a new navigation candidate. Original planner bytes
are retained; this evaluator removes reverse edges in a local function copy.
"""
import os,sys,json,hashlib,importlib.util,signal,time,traceback
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);src=repo/'experiments/v688_dynamic_distance_curriculum';sys.path.insert(0,str(src));sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from planner import search
from learned_proposer import Proposer
root=repo/'runs/v688_dynamic_distance_curriculum';pair=root/'teacher6m/paired';cell=pair/'geometry_memory'
assert json.loads((root/'ROUND_WINDOW.json').read_text())['round_closed'],'DO_NOT_COMPETE_WITH_PHYSICS'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=(src/'planner.py').read_text();needle='for gear in (1,-1):'
assert original.count(needle)==1
namespace={'__name__':'v688_forward_only_diagnostic'};exec(compile(original.replace(needle,'for gear in (1,):'),'<local-forward-edge-diagnostic>','exec'),namespace)
spec=importlib.util.spec_from_file_location('v688_geometry_frozen',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('THREE_FIXED_GEOMETRY_90S')));signal.alarm(90)
records=[];status='RUNNING';error=None;begun=time.monotonic()
try:
 for step in [32,103,132]:
  file=cell/f'planning_{step:04d}.json';x=read(file);world=x['causal_route_input'];field=build(F,world);field.base_heuristic=F.base._heuristic_grid
  route,stats=namespace['search'](field,x['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.18,dense_requested_guard=True,work_limit=4000)
  if stats['status']!='GLOBAL_GOAL_PATH':
   route,stats=namespace['search'](field,x['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.155,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
  old=np.asarray(x['path']);records.append({'step':step,'input_sha256':sha(file),'original_route_status':x['stats']['status'],'original_reverse_poses':int(np.sum(old[:,3]==-1)),'forward_only_status':stats,'forward_only_path':None if route is None else route.tolist(),'scope':'geometric route only; no robot/command/backup rollout, not proof a forward-only policy will pass'})
 status='ZERO_INTEGRATION_PROBE_COMPLETE'
except BaseException as e:error={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()};status='FAILED'
finally:
 signal.alarm(0);out={'status':status,'error':error,'fixed_steps':[32,103,132],'records':records,'elapsed_s':time.monotonic()-begun,'original_planner_sha256':sha(src/'planner.py'),'local_substitution':needle+' -> for gear in (1,):','robot_integrations':0,'new_navigation_candidates':0,'training_updates':0};(root/'FORWARD_GEOMETRY_PROBE.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='records'},indent=2))
