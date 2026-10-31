"""Offline replay of a recorded causal planning input; zero simulation steps."""
import argparse,importlib.util,json,os,sys,time
from pathlib import Path
from planner import search
from instrumentation import dump
p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--name',required=True);p.add_argument('--guard',type=float,default=.15);p.add_argument('--budget',type=float,default=6);p.add_argument('--exact',action='store_true');p.add_argument('--dense-requested-guard',action='store_true');p.add_argument('--self-domain',action='store_true');p.add_argument('--resolution',type=float,default=.10);p.add_argument('--headings',type=int,default=72);p.add_argument('--max-steer',type=float,default=.43);a=p.parse_args()
repo=Path(os.environ['PHASE_REPO']);sys.path.insert(0,str(Path('/home/linghu/catkin_ws/src/mk-mini/experiments/phase_rpccr_p0b68_v1')))
spec=importlib.util.spec_from_file_location('offline_F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
j=json.loads(Path(a.input).read_text());world=j['causal_input'];
if a.self_domain:
    from geometry_predictor import SELF_DOMAIN
    world['footprint_bounds']=SELF_DOMAIN.tolist()
field=F.FootprintMap(world)
if a.exact:
    from exact_footprint import build
    field=build(F,world)
field.base_heuristic=F.base._heuristic_grid
begin=time.monotonic();path,stats=search(field,j['pose'],world['goal'],float(world['wheel_base']),a.max_steer,guard=a.guard,budget=a.budget,resolution=a.resolution,heading_bins=a.headings,dense_requested_guard=a.dense_requested_guard)
dump(Path(os.environ['PHASE_RUNS']) /'v651_static_progress'/a.name,{'input':a.input,'guard':a.guard,'exact_euclidean_rectangles':a.exact,'self_domain_admission':a.self_domain,'search_resolution_m':a.resolution,'heading_bins':a.headings,'requested_max_steer_rad':a.max_steer,'stats':stats,'path':path,'elapsed_s':time.monotonic()-begin,'navigation_steps':0,'scope':'offline geometry-only replay, no executed navigation; inspect input_scope for truth use','input_scope':j.get('scope','recorded causal planning input')})
print(stats,flush=True)
