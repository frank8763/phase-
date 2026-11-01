"""Zero integration: same saved causal failure input, same fixed-work search."""
import importlib.util,json,os,sys,time
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO'])
sys.path.insert(0,str(repo/'current'))
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0,str(repo/'experiments/v663_dynamic_interval_tracking'))
from exact_footprint import build
from planner import search
from motion_tracker import forecast_corridor_world
spec=importlib.util.spec_from_file_location('footprint_probe',repo/'current/footprint_map_b70_v513.py')
F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
root=repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe0/paired/geometry_memory'
plan_path=sorted(root.glob('planning_*.json'))[-1]
plan=json.loads(plan_path.read_text());states=[json.loads(s)for s in (root/'motion_estimate.jsonl').read_text().splitlines()]
state=states[-1];world=plan['causal_input'];results=[]
for mode in ['full_projection','current_proposal']:
    inputs=forecast_corridor_world(world,state)if mode=='full_projection'else world
    field=build(F,inputs);field.guard=.15;field.base_heuristic=F.base._heuristic_grid
    started=time.monotonic()
    candidate,stats=search(field,plan['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.18,dense_requested_guard=True,work_limit=4000)
    if stats['status']!='GLOBAL_GOAL_PATH':
        preferred=candidate;preferred_stats=stats
        candidate,stats=search(field,plan['pose'],world['goal'],world['wheel_base'],world['max_steer'],guard=.155,resolution=.05,heading_bins=144,dense_requested_guard=True,work_limit=16000)
        if candidate is None and preferred is not None:candidate,stats=preferred,dict(preferred_stats)
        stats['preferred_search']=preferred_stats
    results.append({'mode':mode,'stats':stats,'path':None if candidate is None else candidate.tolist(),'elapsed_s':time.monotonic()-started})
result={'saved_failure_input':str(plan_path.relative_to(repo)),'simulation_steps':0,'hidden_world_geometry_used':False,'safety_gate_changed':False,'results':results,'scope':'path proposal feasibility only; no command, arrival or future safety claim'}
out=repo/'runs/v663_dynamic_interval_tracking/OFFLINE_ROUTE_PROJECTION_DIAGNOSIS.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({**result,'results':[{k:v for k,v in r.items()if k!='path'}for r in results]},indent=2))
