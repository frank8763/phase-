"""Replay saved causal planner inputs only. No navigation or hidden world inputs."""
import os,json,time
from pathlib import Path
from factory import initialize
from instrumentation import dump
from exact_footprint import build
from planner import search
root=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown';out=root/'offline_search_probe_16';out.mkdir();begin=time.monotonic()
c,native=initialize(91000002,out/'paired');F=c['F'];source=root/'static_pilot_15_single_seed2/paired/memory/planning_0489.json';d=json.loads(source.read_text());w=d['causal_input'];rows=[]
for exact,guard in [(False,.18),(True,.18),(True,.15)]:
 field=build(F,w)if exact else F.FootprintMap(w);field.base_heuristic=F.base._heuristic_grid
 path,stats=search(field,d['pose'],w['goal'],w['wheel_base'],w['max_steer'],guard=guard,budget=12.)
 rows.append({'exact_rectangle_distance':exact,'requested_guard':guard,'stats':stats,'path':path});print(rows[-1]['stats'],flush=True)
dump(c['out']/'probe.json',{'input':str(source),'rows':rows,'actual_navigation_physics_steps':0,'elapsed_s':time.monotonic()-begin})
