"""Exact saved end-state search refusal; no vehicle model or integration."""
import importlib.util
import json
import os
from pathlib import Path
import sys

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
    from observed_route import revalidate
    s=importlib.util.spec_from_file_location('original_bounded_planner',R/'experiments/v1358_terminal_contract/planner.py')
    planner=importlib.util.module_from_spec(s);s.loader.exec_module(planner)
    raw=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main'
    request=json.loads((raw/'planner_jobs/request03.json').read_text())
    ball=request['ball'];ball=(ball[:2],ball[2])
    path,report=planner.propose(request['known'],request['body'],request['goal'],ball,
        guard=request['guard'],mode=request['planner_mode'],maxwall=1.5,maxexpand=22000)
    assert path is None and report['status']=='NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET'
    assert report['expanded']==22000
    assert revalidate(request['known'],path,request['body'],ball,guard=.22)[0] is False
    value=dict(reproduced=True,request=3,saved_body=request['body'],causal_ball=request['ball'],
               report=report,exact_full_budget_refusal=True,models=0,physical_native=0)
    (O/'ORIGINAL_REPRODUCTION.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))


if __name__=='__main__':main()
