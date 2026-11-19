"""One saved-state call plus fixed empty/blocked software boundaries."""
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
from planner import interval_table,solve

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes();begin=time.monotonic()
    claim=O/'RUN_CLAIM.json'
    with claim.open('x') as f:json.dump(dict(started_unix=time.time(),software_limit_s=120,models=0),f)
    req=json.loads((R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json').read_text())
    prefix=json.loads((R/'runs/v1362_terminal_route_diagnosis/CONNECTIVITY_AND_SHAPE.json').read_text())
    assert prefix['coefficient_source_tick']<=req['native_tick']
    balls=interval_table(prefix['coefficient_snapshot']['vertices'],req['sim_time'])
    cases=[]
    tests=[('original_terminal',req['known'],req['body'],req['goal'],balls),
           ('empty_forward',dict(known_rectangles=[],known_circles=[]),[0.,0.,0.,0.,0.],[1.,0.],np.tile([4.,4.,.1],(401,1))),
           ('blocked_start',req['known'],req['body'],req['goal'],np.tile([*req['body'][:2],1.],(401,1)))]
    for name,known,body,goal,table in tests:
        path,report=solve(known,body,goal,np.ascontiguousarray(table,dtype=float))
        case=dict(name=name,body=body,goal=goal,report=report,path=None if path is None else path.tolist())
        cases.append(case);print(json.dumps({k:v for k,v in case.items() if k!='path'}),flush=True)
    assert cases[1]['report']['goal_found'] and cases[2]['report']['status']=='START_BELOW22'
    result=dict(executed=True,cases=cases,causal_prefix_source_tick=prefix['coefficient_source_tick'],
                fixed_saved_request=3,forecast_table=balls.tolist(),timing_tolerance_s=.2,
                library_sha256=hashlib.sha256((O/'libtimed.so').read_bytes()).hexdigest(),
                actual_braking_and_tracking_qualified=False,automatic_physics=False,models=0,physical_native=0,
                wall_s=time.monotonic()-begin,review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,
                current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(executed=True,original_goal_found=cases[0]['report']['goal_found'],models=0,wall_s=result['wall_s'])))


if __name__=='__main__':main()
