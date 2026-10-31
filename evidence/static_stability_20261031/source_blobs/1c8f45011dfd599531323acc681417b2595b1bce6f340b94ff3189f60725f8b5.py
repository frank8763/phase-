"""Offline replay of a recorded causal planning input; zero simulation steps."""
import argparse,importlib.util,json,os,sys,time
from pathlib import Path
from planner import search
from instrumentation import dump
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--name',required=True);p.add_argument('--guard',type=float,default=.15);p.add_argument('--budget',type=float,default=6);p.add_argument('--exact',action='store_true');a=p.parse_args()
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(Path('/home/linghu/catkin_ws/src/mk-mini/experiments/phase_rpccr_p0b68_v1')))
spec=importlib.util.spec_from_file_location('offline_F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
j=json.loads(Path(a.input).read_text());world=j['causal_input'];field=F.FootprintMap(world)
if a.exact:
    from exact_footprint import build
    field=build(F,world)
field.base_heuristic=F.base._heuristic_grid
begin=time.monotonic();path,stats=search(field,j['pose'],world['goal'],float(world['wheel_base']),.6108652381980153,guard=a.guard,budget=a.budget)
dump(Path(os.environ['PHASE_RUNS'])/'v649_static_stability'/a.name,{'input':a.input,'guard':a.guard,'exact_euclidean_rectangles':a.exact,'stats':stats,'path':path,'elapsed_s':time.monotonic()-begin,'navigation_steps':0,'scope':'recorded causal map only; no hidden geometry, no executed navigation'})
print(stats,flush=True)
