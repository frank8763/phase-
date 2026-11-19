"""Causal16-direction outer actor occupancy, no extra rectangle/circle wrap."""
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def clipped(normals,support):
    points=np.array([[-12.,-12.],[12.,-12.],[12.,12.],[-12.,12.]])
    for normal,bound in zip(normals,support):
        following=[]
        for a,b in zip(points,np.roll(points,-1,axis=0)):
            da=float(a@normal-bound);db=float(b@normal-bound)
            if da<=0:following.append(a)
            if (da<0<db) or (db<0<da):following.append(a+(b-a)*(da/(da-db)))
        points=np.asarray(following);assert len(points)>=3,'CAUSAL_OCCUPANCY_EMPTY'
    assert (points@normals.T<=support+1e-8).all()
    return points


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'FORECAST_POLYGONS.json';assert not target.exists()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());stamp=graph['request']['sim_time']
    old=json.loads((R/'runs/v1362_terminal_route_diagnosis/CONNECTIVITY_AND_SHAPE.json').read_text())
    assert old['coefficient_source_tick']==graph['source_tick']==15105
    vertices=old['coefficient_snapshot']['vertices'];normal=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    spec=importlib.util.spec_from_file_location('same_original_interval_support',R/'experiments/v1020_terminal_two_route_development/periodic_support.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    polygons=[];supports=[]
    for tick in range(401):
        bounds=p.swept_bounds(vertices,stamp+tick*.2-.2,stamp+(tick+1)*.2+.2)+.1
        polygons.append(clipped(normal,bounds).tolist());supports.append(bounds.tolist())
    result=dict(polygons=polygons,supports=supports,normals=normal.tolist(),source_tick=15105,
        actor_radius_already_included_m=.1,coefficient_prefix_unchanged=True,future_observations_used=0,
        models=0,physical_native=0,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(polygons=len(polygons),max_vertices=max(map(len,polygons)),wall_s=result['wall_s'],models=0)))


if __name__=='__main__':main()
