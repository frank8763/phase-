"""Fixed24 forecast intervals from one saved prefix; no new navigation trials."""
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    raw=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main';req=json.loads((raw/'planner_jobs/request03.json').read_text())
    saved=json.loads((O/'CONNECTIVITY_AND_SHAPE.json').read_text());vertices=saved['coefficient_snapshot']['vertices']
    assert saved['coefficient_source_tick']<=req['native_tick']
    s=importlib.util.spec_from_file_location('exact_interval_support',R/'experiments/v1020_terminal_two_route_development/periodic_support.py')
    p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
    from observed_route import revalidate
    s=importlib.util.spec_from_file_location('original_planner_no_changes',R/'experiments/v1358_terminal_contract/planner.py')
    planner=importlib.util.module_from_spec(s);s.loader.exec_module(planner)
    rows=[];period=math.tau/.32
    # Fixed diagnostic phase samples of the same current coefficient enclosure,
    # never24newtask/seed/scene/navigation samples.2.2s is a geometric probe,
    # not a certified physical braking duration or a new operating contract.
    for index,delay in enumerate(np.arange(24)*period/24):
        t0=req['sim_time']+float(delay);t1=t0+2.2
        support=p.swept_bounds(vertices,t0,t1);lower=-support[[8,12]];upper=support[[0,4]]
        center=(lower+upper)/2;radius=float(np.linalg.norm((upper-lower)/2))+.1
        ball=[*center.tolist(),radius]
        path,report=planner.propose(req['known'],req['body'],req['goal'],(center,radius),mode=1,maxexpand=22000,maxwall=1.5)
        valid,proof=revalidate(req['known'],path,req['body'],(center,radius),guard=.22)
        rows.append(dict(index=index,delay_s=float(delay),interval_start=t0,interval_end=t1,ball=ball,
            report=report,live_dense_passed=valid,dense_geometry=proof,
            path=None if path is None else path.tolist(),route_traversal_not_time_certified=True))
    result=dict(executed=True,scope='24timeintervalprobes_on_one_original_saved_input_not24confirmation',
        original_coefficient_source_tick=saved['coefficient_source_tick'],future_observations_used=0,
        tested_horizon_s=2.2,geometric_interval_not_braking_certificate=True,rows=rows,
        full_goal_path_count=sum(row['report']['status']=='GLOBAL_GOAL_PATH' and row['live_dense_passed'] for row in rows),
        progress_prefix_count=sum(row['report']['status']=='SAFE_PROGRESS_PREFIX' and row['live_dense_passed'] for row in rows),
        private_or_physical_native=0,models=0,wall_s=time.monotonic()-begin,automatic_physics=False)
    (O/'TIMED_FORECAST_PROBE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    print(json.dumps([dict(index=z['index'],delay_s=z['delay_s'],radius=z['ball'][2],status=z['report']['status'],live_dense_passed=z['live_dense_passed']) for z in rows]))


if __name__=='__main__':main()
