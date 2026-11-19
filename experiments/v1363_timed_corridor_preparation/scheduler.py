"""Finite time assignment to one existing exact-footprint path; no vehicle."""
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def clearances(rear,centers,radii):
    rear=np.asarray(rear);angles=rear[:,2];c=np.cos(angles)[:,None];s=np.sin(angles)[:,None]
    xy=rear[:,:2]+.3*np.c_[np.cos(angles),np.sin(angles)]
    dx=centers[None,:,0]-xy[:,None,0];dy=centers[None,:,1]-xy[:,None,1]
    a=np.abs(c*dx+s*dy)-.44;b=np.abs(-s*dx+c*dy)-.375
    maximum=np.maximum(a,b)
    return np.where(maximum<=0,maximum,np.hypot(np.maximum(a,0),np.maximum(b,0)))-radii[None,:]


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic();O.mkdir(exist_ok=True)
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    with (O/'RUN_CLAIM.json').open('x') as f:json.dump(dict(started_unix=time.time(),software_seconds=120,models=0),f)
    base=R/'runs/v1362_terminal_route_diagnosis';timed=json.loads((base/'TIMED_FORECAST_PROBE.json').read_text())
    possibilities=[z for z in timed['rows'] if z['report']['status']=='GLOBAL_GOAL_PATH' and z['live_dense_passed']]
    chosen=min(possibilities,key=lambda z:(sum(math.dist(a[:2],b[:2]) for a,b in zip(z['path'][:-1],z['path'][1:])),z['index']))
    original=np.array(chosen['path']);spacing=.02;poses=[original[0,:3]];gears=[int(original[1,3])];cusp=[False]
    for a,b in zip(original[:-1],original[1:]):
        pieces=max(1,round(np.linalg.norm(b[:2]-a[:2])/spacing));turn=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]))
        for j in range(1,pieces+1):
            poses.append([a[0]+j/pieces*(b[0]-a[0]),a[1]+j/pieces*(b[1]-a[1]),a[2]+j/pieces*turn]);gears.append(int(b[3]));cusp.append(False)
    poses=np.array(poses);gears=np.array(gears);cusp=np.array(cusp)
    for i in range(len(poses)-1):
        if gears[i+1]!=gears[i]:cusp[i]=True
    dt=.2;total=400;stamp=chosen['interval_start']-chosen['delay_s'];times=stamp+np.arange(total+1)*dt
    s=importlib.util.spec_from_file_location('unchanged_causal_interval_support',R/'experiments/v1020_terminal_two_route_development/periodic_support.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
    vertices=json.loads((base/'CONNECTIVITY_AND_SHAPE.json').read_text())['coefficient_snapshot']['vertices'];centers=[];radii=[]
    for t in times:
        bounds=p.swept_bounds(vertices,t-.2,t+dt+.2);lo=-bounds[[8,12]];hi=bounds[[0,4]]
        centers.append((lo+hi)/2);radii.append(np.linalg.norm((hi-lo)/2)+.1)
    centers=np.array(centers);radii=np.array(radii)
    node_ok=clearances(poses,centers,radii)>=.22-1e-8
    angles=np.arctan2(np.sin(poses[1:,2]-poses[:-1,2]),np.cos(poses[1:,2]-poses[:-1,2]));edge_ok=np.ones((len(poses)-1,total+1),bool)
    for ratio in np.linspace(0,1,5):
        mid=np.c_[poses[:-1,:2]+ratio*(poses[1:,:2]-poses[:-1,:2]),poses[:-1,2]+ratio*angles]
        edge_ok &= clearances(mid,centers,radii)>=.22-1e-8
    n=len(poses);pre=np.full((n,total+1),-2,np.int32);pre[0,0]=-3
    wait_nodes=cusp.copy();wait_nodes[0]=wait_nodes[-1]=True
    end=None
    for tick in range(total):
        assert time.monotonic()-begin<110,'SOFTWARE_DEADLINE'
        for i in np.flatnonzero(pre[:,tick]!=-2):
            if wait_nodes[i] and node_ok[i,tick] and pre[i,tick+1]==-2:pre[i,tick+1]=-1
            if i==n-1:end=(i,tick);break
            hold=13 if cusp[i] else 0;arrive=tick+hold+1
            if arrive>total:continue
            if hold and not node_ok[i,tick:tick+hold].all():continue
            if edge_ok[i,tick+hold] and pre[i+1,arrive]==-2:pre[i+1,arrive]=tick
        if end is not None:break
    schedule=[];wait=0.;minimum=math.inf
    if end is not None:
        i,tick=end
        while not (i==0 and tick==0):
            prev=int(pre[i,tick]);assert prev!=-2
            if prev==-1:
                schedule.append(dict(action='WAIT',path_index=i,start_tick=tick-1,end_tick=tick));wait+=dt;tick-=1
            else:
                schedule.append(dict(action='MOVE_WITH_CUSP_HOLD' if tick-prev>1 else 'MOVE',path_index=i-1,start_tick=prev,end_tick=tick))
                wait+=max(0,tick-prev-1)*dt;i-=1;tick=prev
        schedule.reverse()
        for step in schedule:
            i=step['path_index'];start=step['start_tick'];endtick=step['end_tick']
            if step['action']=='WAIT':assert wait_nodes[i] and node_ok[i,start]
            else:
                assert edge_ok[i,endtick-1]
                if endtick-start>1:assert cusp[i] and node_ok[i,start:endtick-1].all()
        assert wait<=40.+1e-8,'ORIGINAL_WAIT_BUDGET_EXCEEDED'
    result=dict(geometric_schedule_found=end is not None,scope='one_saved_terminal_path_nominal_timing_only',chosen_interval_witness=chosen['index'],
                path=poses.tolist(),incoming_gears=gears.tolist(),time_origin=stamp,time_step_s=dt,timing_tolerance_s=.2,
                terminal_tick=None if end is None else end[1],nominal_elapsed_s=None if end is None else end[1]*dt,
                total_wait_and_cusp_hold_s=wait,waiting_pose_indices=np.flatnonzero(wait_nodes).tolist(),schedule=schedule,
                actual_braking_and_tracking_qualified=False,whole_navigation_passed=False,automatic_physics=False,
                models=0,physical_native=0,wall_s=time.monotonic()-begin,
                review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['path','incoming_gears','schedule']}))


if __name__=='__main__':main()
