"""Check why interval-spatial paths are not complete time-feasible plans."""
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
    saved=json.loads((O/'CONNECTIVITY_AND_SHAPE.json').read_text());vertices=saved['coefficient_snapshot']['vertices']
    timed=json.loads((O/'TIMED_FORECAST_PROBE.json').read_text());rows=[]
    s=importlib.util.spec_from_file_location('original_swept_interval',R/'experiments/v1020_terminal_two_route_development/periodic_support.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
    sys.path.insert(0,str(R/'experiments/v1361_dynamic_reserve_consistency'));from observed_route import nominal_clearance
    for case in timed['rows']:
        if case['report']['status']!='GLOBAL_GOAL_PATH':continue
        path=np.array(case['path']);clock=case['interval_start'];samples=[];gear=int(path[1,3]);length=0.;switches=0
        for a,b in zip(path[:-1],path[1:]):
            distance=float(np.linalg.norm(b[:2]-a[:2]));duration=distance/.1
            if int(b[3])!=gear:
                switches+=1;gear=int(b[3])
                for dt in np.linspace(0,2.5,26):samples.append((clock+dt,a[:3]))
                clock+=2.5
            angle=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
            for ratio in np.linspace(0,1,max(2,math.ceil(distance/.008)),endpoint=False):
                pose=[a[0]+ratio*(b[0]-a[0]),a[1]+ratio*(b[1]-a[1]),a[2]+ratio*angle]
                samples.append((clock+ratio*duration,pose))
            clock+=duration;length+=distance
        samples.append((clock,path[-1,:3]));minimum=math.inf;bad=0
        for stamp,rear in samples:
            # Instantaneous causal occupied disk, not a full braking tube.
            bounds=p.swept_bounds(vertices,stamp,stamp);lo=-bounds[[8,12]];hi=bounds[[0,4]]
            center=(lo+hi)/2;radius=np.linalg.norm((hi-lo)/2)+.1
            body=[rear[0]+.3*math.cos(rear[2]),rear[1]+.3*math.sin(rear[2]),rear[2]]
            clearance=nominal_clearance(body,center,radius);minimum=min(minimum,clearance);bad+=clearance<.22
        rows.append(dict(interval_index=case['index'],delay_s=case['delay_s'],path_length_m=length,
                         nominal_speed_m_s=.1,gear_switches=switches,cusp_hold_s=2.5,
                         total_nominal_traversal_s=clock-case['interval_start'],spatial_certificate_interval_s=2.2,
                         nominal_timed_minimum_causal_clearance_m=minimum,samples_below22cm=bad,samples=len(samples),
                         naive_time_assignment_passed=bad==0,actual_vehicle_dynamics_qualified=False))
    value=dict(models=0,physical_native=0,rows=rows,naive_nominal_time_only=True,
               no_new_time_assignment_or_braking_acceptance=True,wall_s=time.monotonic()-begin)
    (O/'NOMINAL_SCHEDULE_PROBE.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))


if __name__=='__main__':main()
