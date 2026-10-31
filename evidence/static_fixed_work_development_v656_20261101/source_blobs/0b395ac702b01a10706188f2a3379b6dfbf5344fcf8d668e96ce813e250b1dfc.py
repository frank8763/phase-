"""Zero-simulation causal-input search replay under two artificial clock rates."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import numpy as np
import planner
from exact_footprint import build

repo=Path(os.environ['PHASE_REPO'])
sys.path.insert(0,'/home/linghu/catkin_ws/src/mk-mini/experiments/phase_rpccr_p0b68_v1')
spec=importlib.util.spec_from_file_location('fixed_work_F',repo/'current/footprint_map_b70_v513.py')
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
source=repo/'runs/v651_static_progress/dev29_seed91000002_single_event/paired/geometry_memory/planning_0134.json'
j=json.loads(source.read_text());world=j['causal_input'];results=[]
for rate in [.25,8.]:
    field=build(F,world);field.base_heuristic=F.base._heuristic_grid
    real_start=time.monotonic()
    planner.time=SimpleNamespace(monotonic=lambda:1000.+rate*(time.monotonic()-real_start))
    path,stats=planner.search(field,j['pose'],world['goal'],world['wheel_base'],world['max_steer'],
                              guard=.18,budget=2.,dense_requested_guard=True,work_limit=4000)
    assert path is not None
    results.append({'artificial_clock_rate':rate,'path_sha256':hashlib.sha256(path.tobytes()).hexdigest(),
                    'stats':stats,'path':path.tolist(),'real_elapsed_s':time.monotonic()-real_start})
assert results[0]['path_sha256']==results[1]['path_sha256']
assert results[0]['stats']['expanded']==results[1]['stats']['expanded']==3197
assert results[0]['stats']['status']==results[1]['stats']['status']=='GLOBAL_GOAL_PATH'
out=repo/'runs/v656_static_deterministic_work';out.mkdir(exist_ok=True)
report={'passed':True,'input':str(source.relative_to(repo)),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'clock_rates':[.25,8.],'same_path_under_32x_clock_rate_change':True,'simulation_steps':0,
        'world_input_scope':'recorded causal planning input only, no hidden-world geometry','results':results}
(out/'FIXED_WORK_ZERO_SIM_REPLAY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='results'}))
