"""Sensor-error directional support experiment on the same causal prefix only."""
import gzip
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
    s=importlib.util.spec_from_file_location('original_periodic_clip',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
    coeff=importlib.util.module_from_spec(s);s.loader.exec_module(coeff);tracker=coeff.PeriodicSupport()
    n=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    sensors=json.load(gzip.open(raw/'physics/SENSORS.json.gz','rt'));packets={z['native_tick']:z for z in sensors}
    records=json.loads((raw/'CAUSAL_OBSERVATIONS.json').read_text());used=[]
    for row in records:
        if row['native_tick']>req['native_tick']:break
        source=packets[row['native_tick']];d=(np.array(row['point'])-source['xy'])/row['range']
        assert abs(np.linalg.norm(d)-1)<1e-6
        # Same declared .10actor+.06noise+.04backend+.04geometry budget.
        # Range error is along its actual ray, not an arbitrary direction:
        # center in observedpoint + disk(.14) + segment[-.10,.10]*raydirection.
        # Prototype only until source and original hit-ray containment audited.
        support=n@np.array(row['point'])+.14+.10*np.abs(n@d)
        tracker.update(row['sim_time'],row['native_tick'],support.tolist());used.append(row)
    vertices=[z.v for z in tracker.polytopes]
    allperiod=np.array([max(v[:,0]+np.hypot(v[:,1],v[:,2]))+2e-7 for v in vertices]+
                       [max(-v[:,0]+np.hypot(v[:,1],v[:,2]))+2e-7 for v in vertices])
    lower=-allperiod[[8,12]];upper=allperiod[[0,4]];center=(lower+upper)/2;radius=np.linalg.norm((upper-lower)/2)+.1
    ball=[*center.tolist(),float(radius)]
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'))
    from observed_route import revalidate
    s=importlib.util.spec_from_file_location('original_full_search',R/'experiments/v1358_terminal_contract/planner.py');planner=importlib.util.module_from_spec(s);s.loader.exec_module(planner)
    path,report=planner.propose(req['known'],req['body'],req['goal'],(ball[:2],ball[2]),mode=1,maxexpand=22000,maxwall=1.5)
    passed,proof=revalidate(req['known'],path,req['body'],(ball[:2],ball[2]),guard=.22)
    from connectivity import component
    connected=component(req['known'],ball,req['body'],req['goal'])
    result=dict(prototype_only=True,source_and_containment_qualification_still_required=True,causal_prefix_only=True,
                original_ball=req['ball'],directional_ball=ball,coefficient_source_tick=tracker.source_tick,
                allperiod_lower=lower.tolist(),allperiod_upper=upper.tolist(),
                path=None if path is None else path.tolist(),search=report,live_dense_passed=passed,dense_geometry=proof,
                optimistic_connectivity=connected,models=0,physical_native=0,wall_s=time.monotonic()-begin)
    (O/'DIRECTIONAL_PROTOTYPE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='path'}))


if __name__=='__main__':main()
