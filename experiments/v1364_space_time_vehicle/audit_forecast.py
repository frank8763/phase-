"""Evaluator-only interval support audit; never imported by search or control."""
import ctypes
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from planner import _array

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def extrema(vertices,a,b):
    minimum=math.inf;maximum=-math.inf
    for c,sine,cosine in vertices:
        values=[c+sine*math.sin(.32*t)+cosine*math.cos(.32*t) for t in [a,b]]
        phase=math.atan2(sine,cosine)
        first=math.ceil((.32*a-phase)/math.pi)
        last=math.floor((.32*b-phase)/math.pi)
        for k in range(first,last+1):
            t=(phase+k*math.pi)/.32
            if a-1e-10<=t<=b+1e-10:values.append(c+sine*math.sin(.32*t)+cosine*math.cos(.32*t))
        minimum=min(minimum,*values);maximum=max(maximum,*values)
    return minimum-2e-7,maximum+2e-7


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'INDEPENDENT_FORECAST_AUDIT.json';assert not target.exists()
    result=json.loads((O/'KINODYNAMIC_RESULT.json').read_text());table=np.array(result['forecast_center_rectangle_table'])
    old=json.loads((R/'runs/v1362_terminal_route_diagnosis/CONNECTIVITY_AND_SHAPE.json').read_text());vertices=old['coefficient_snapshot']['vertices']
    stamp=result['time_origin'];error=0.;maximum=-math.inf;count=0
    # Offline actor truth is confined to this evaluator. Predictor/search
    # source and inputs remain causal saved coefficient vertices only.
    setup=json.loads((R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main/physics/SETUP.json').read_text())['actor']
    assert setup['amplitude_m']==.25 and setup['omega_rad_s']==.32 and setup['radius_m']==.1
    for i,row in enumerate(table):
        a=stamp+i*.2-.2;b=stamp+(i+1)*.2+.2
        xlo,xhi=extrema(vertices[0],a,b);ylo,yhi=extrema(vertices[4],a,b)
        expected=np.array([(xlo+xhi)/2,(ylo+yhi)/2,(xhi-xlo)/2,(yhi-ylo)/2])
        error=max(error,float(np.max(abs(row-expected))))
        times=np.linspace(a,b,61)
        actual=np.asarray(setup['anchor_xy'])+.25*np.sin(times*.32+setup['phase_rad'])[:,None]*np.asarray(setup['axis_xy'])
        excess=np.max(abs(actual-row[:2])-row[2:],axis=1)
        maximum=max(maximum,float(excess.max()));count+=len(times)
    assert error<=1e-8 and maximum<=1e-8,'FORECAST_SUPPORT_OR_OFFLINE_COVERAGE'
    # Inspect the original ordering heuristic only. Its grid is not an
    # executable plan or safety certificate; a finite value proves neither.
    request=json.loads((R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json').read_text())
    known=request['known'];rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4);circles=np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3)
    seam=ctypes.CDLL(str(O/'libqualification_seams.so'))
    seam.time_guide_probe.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,ctypes.c_double,_array]
    guide=np.empty(401)
    seam.time_guide_probe(rect,len(rect),circles,len(circles),np.ascontiguousarray(table),401,
        np.ascontiguousarray(request['body'],dtype=float),np.ascontiguousarray(request['goal'],dtype=float),.27,guide)
    proof=dict(passed=True,independent_interval_support_error_m=error,interval_rows=len(table),coefficient_source_tick=old['coefficient_source_tick'],
        original_request_tick=request['native_tick'],future_observations_used=0,truth_used_only_afterwards_in_evaluator=True,
        offline_future_samples=count,maximum_actor_center_outside_forecast_rectangle_m=maximum,actor_radius_retained_m=.10,
        ordering_guide_root_cost_s=None if guide[0]>=1e99 else float(guide[0]),ordering_guide_never_approves_control=True,
        original_terminal_route_qualified=False,models=0,physical_native=0,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))


if __name__=='__main__':main()
