"""Optimistic grid exclusion proof for the disk model, plus causal coefficient replay."""
from collections import deque
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def component(known, ball, body, goal, step=.025):
    n=round(10/step);axis=-5+(np.arange(n)+.5)*step;x,y=np.meshgrid(axis,axis)
    # Any rectangular vehicle contains a radius.375 centered disk, whatever
    # its heading.22cm clearance therefore requires point clearance>=.595.
    values=np.minimum.reduce([x+5,5-x,y+5,5-y])
    for cx,cy,hx,hy in known['known_rectangles']:
        dx,dy=abs(x-cx)-hx,abs(y-cy)-hy
        signed=np.where(np.maximum(dx,dy)<=0,np.maximum(dx,dy),np.hypot(np.maximum(dx,0),np.maximum(dy,0)))
        values=np.minimum(values,signed)
    for cx,cy,radius in list(known['known_circles'])+([ball] if ball is not None else []):
        values=np.minimum(values,np.hypot(x-cx,y-cy)-radius)
    # Signed obstacle distance is1-Lipschitz. Remove ONLY cells entirely below
    # the necessary radius+margin floor; every ambiguous cell remains traversable.
    optimistic=values+step/math.sqrt(2)>=.595-1e-10
    sx=int((body[0]+5)/step);sy=int((body[1]+5)/step)
    assert optimistic[sy,sx]
    seen=np.zeros_like(optimistic);seen[sy,sx]=True;q=deque([(sx,sy)])
    while q:
        ix,iy=q.popleft()
        for dx,dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx,ny=ix+dx,iy+dy
            if 0<=nx<n and 0<=ny<n and optimistic[ny,nx] and not seen[ny,nx]:
                seen[ny,nx]=True;q.append((nx,ny))
    candidate=np.hypot(x-goal[0],y-goal[1])<=.45+step/math.sqrt(2)
    return dict(step_m=step,necessary_inscribed_radius_plus_margin_m=.595,
                cells=n*n,ambiguous_cells_retained=True,eight_neighbor_including_corner_connections=True,
                start_component_cells=int(seen.sum()),optimistic_goal_cells=int((candidate&optimistic).sum()),
                reachable_goal_cells=int((candidate&seen).sum()),
                disk_model_goal_disconnected_proved=not bool((candidate&seen).any()))


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    raw=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main'
    req=json.loads((raw/'planner_jobs/request03.json').read_text())
    results=[dict(dynamic_disk_present=occupied,**component(req['known'],req['ball'] if occupied else None,req['body'],req['goal'])) for occupied in [True,False]]
    # The saved record is the causal algorithm's actual selected range return.
    # Reconstruct coefficients from its prefix only; no later record/truth input.
    s=importlib.util.spec_from_file_location('public_periodic_coefficients',R/'experiments/v1037_periodic_norm_source/periodic_norm.py')
    p=importlib.util.module_from_spec(s);s.loader.exec_module(p);tracker=p.PeriodicSupport()
    normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    records=json.loads((raw/'CAUSAL_OBSERVATIONS.json').read_text());used=[]
    for row in records:
        if row['native_tick']>req['native_tick']:break
        tracker.update(row['sim_time'],row['native_tick'],(normals@np.array(row['point'])+.24).tolist());used.append(row)
    assert used and tracker.source_tick<=req['native_tick']
    vertices=[z.v for z in tracker.polytopes]
    # All-period directional maxima can be evaluated exactly on each coefficient
    # vertex. The actor disk adds.10 to each unit-normal support bound.
    supports=np.array([max(v[:,0]+np.hypot(v[:,1],v[:,2]))+2e-7 for v in vertices]+
                      [max(-v[:,0]+np.hypot(v[:,1],v[:,2]))+2e-7 for v in vertices])+.10
    polygon=[]
    for i in range(16):
        for j in range(i):
            matrix=normals[[j,i]]
            if abs(np.linalg.det(matrix))<1e-10:continue
            point=np.linalg.solve(matrix,supports[[j,i]])
            if (normals@point<=supports+1e-9).all():polygon.append(point)
    polygon=np.unique(np.round(polygon,12),axis=0)
    centroid=polygon.mean(axis=0);angles=np.arctan2(polygon[:,1]-centroid[1],polygon[:,0]-centroid[0]);polygon=polygon[np.argsort(angles)]
    print(json.dumps(dict(connectivity=results,source_tick=tracker.source_tick,allfuture_polygon=polygon.tolist(),last_row=used[-1],wall_s=time.monotonic()-begin)))
    result=dict(connectivity=results,causal_prefix_only=True,causal_records=len(used),request_native_tick=req['native_tick'],
                coefficient_source_tick=tracker.source_tick,coefficient_snapshot=tracker.snapshot(),
                allfuture_normals=normals.tolist(),allfuture_support= supports.tolist(),allfuture_polygon=polygon.tolist(),
                actor_radius_included_m=.10,public_frequency=.32,models=0,physical_native=0,wall_s=time.monotonic()-begin)
    (O/'CONNECTIVITY_AND_SHAPE.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
