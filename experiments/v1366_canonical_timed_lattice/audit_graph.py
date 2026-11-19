"""Independent canonical endpoints, original static geometry and safe prefix."""
import ast
import importlib.util
import json
import math
import os
from pathlib import Path
import time
from types import SimpleNamespace
import numpy as np
from numpy.polynomial import polynomial as poly

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'INDEPENDENT_GRAPH_AUDIT.json';assert not target.exists()
    graph=json.loads((O/'GRAPH_INPUT.json').read_text());headings=graph['headings'];maximum_endpoint=0.;maximum_k=0.;maximum_slew=0.
    for edge in graph['edges']:
        a=np.array(edge['coefficient']);grid=np.linspace(0,1,10001)
        xy=np.c_[poly.polyval(grid,a[:,0]),poly.polyval(grid,a[:,1])]
        dx=np.c_[poly.polyval(grid,poly.polyder(a[:,0])),poly.polyval(grid,poly.polyder(a[:,1]))]
        ddx=np.c_[poly.polyval(grid,poly.polyder(a[:,0],2)),poly.polyval(grid,poly.polyder(a[:,1],2))]
        curve=edge['gear']*(dx[:,0]*ddx[:,1]-dx[:,1]*ddx[:,0])/np.linalg.norm(dx,axis=1)**3
        assert abs(curve).max()<=.5+1e-8
        initial=headings[edge['start_heading']] if edge['start_heading']<16 else 0.
        yaw0=math.atan2(dx[0,1],dx[0,0])+(math.pi if edge['gear']<0 else 0.)
        yaw1=math.atan2(dx[-1,1],dx[-1,0])+(math.pi if edge['gear']<0 else 0.)
        errors=[float(abs(xy[0]).max()),float(abs(xy[-1]-.2*np.array(edge['offset'])).max()),
                abs(math.atan2(math.sin(yaw0-initial),math.cos(yaw0-initial))),abs(math.atan2(math.sin(yaw1-headings[edge['end_heading']]),math.cos(yaw1-headings[edge['end_heading']])))]
        maximum_endpoint=max(maximum_endpoint,*errors);assert max(errors)<1e-8
        rows=np.array(edge['samples']);assert abs(rows[-1,4])<1e-10 and abs(rows[-1,5])<1e-8
        assert np.all(np.diff(rows[:,3])>0) and np.max(np.diff(rows[:,3]))<=.05000001
        slew=float(np.max(abs(np.diff(rows[:,5]))/np.diff(rows[:,3])));assert slew<=.6+1e-5
        maximum_slew=max(maximum_slew,slew);maximum_k=max(maximum_k,float(abs(curve).max()))
    # Original NumPy full rectangle geometry, separately from new C++ graph.
    geometry=module('original_rectangle_geometry',R/'experiments/v855_renewal_worker/exact_footprint.py')
    req=graph['request'];known=req['known']
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.array(known['known_rectangles']),circles=np.array(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    static_result=json.loads((O/'GRAPH_BOUNDARIES_V2.json').read_text())['cases'][0];assert static_result['code']==0
    path=np.array(static_result['path']);static=geometry.pose_values(field,path[:,:3]);assert static.min()>=.274-1e-8
    endpoint=path[-1,:2]+.3*np.array([math.cos(path[-1,2]),math.sin(path[-1,2])]);goal_distance=float(np.linalg.norm(endpoint-req['goal']));assert goal_distance<=.32+1e-8
    assert np.max(abs(np.diff(path[:,3])-.05))<1e-7 and abs(path[-40:,4]).max()<1e-8
    # Select exactly the first edge, retaining all its waiting and stop samples.
    first=int(path[1,8]);finish=next((i for i in range(2,len(path)) if int(path[i,8])!=first),len(path))
    prefix=path[:finish];assert abs(prefix[-40:,4]).max()<1e-8
    ball=req['ball'];nominal=module('old_original_ball_geometry',R/'experiments/v1361_dynamic_reserve_consistency/observed_route.py')
    ball_values=[]
    for rear in prefix[:,:3]:
        body=[rear[0]+.3*math.cos(rear[2]),rear[1]+.3*math.sin(rear[2]),rear[2]]
        ball_values.append(nominal.nominal_clearance(body,ball[:2],ball[2]))
    minimum=min(float(static[:finish].min()),min(ball_values));assert minimum>=.274-1e-8,'FIRST_EDGE_NOT_ALL_FUTURE_DISK_CERTIFIED'
    moving=prefix[abs(prefix[:,4])>=.005];gear=1 if moving[0,4]>0 else -1;assert (moving[:,4]*gear>0).all()
    unique=[prefix[0,:3].tolist()]
    for row in prefix[1:]:
        if np.linalg.norm(row[:2]-unique[-1][:2])>1e-7 or abs(row[2]-unique[-1][2])>1e-7:unique.append(row[:3].tolist())
    prefix_result=dict(passed=True,scope='first safe recovery edge only, not complete dynamic route',samples=prefix.tolist(),
        path_segment=dict(gear=gear,poses=unique),allfuture_ball=req['ball'],minimum_static_and_all_future_ball_clearance_m=minimum,
        duration_s=float(prefix[-1,3]),actual_controls_or_timing_qualified=False,models=0,physical_native=0)
    (O/'SAFE_PREFIX.json').write_text(json.dumps(prefix_result,indent=2)+'\n')
    result=dict(passed=True,canonical_edges=len(graph['edges']),maximum_endpoint_and_heading_error=maximum_endpoint,
        maximum_sampled_curvature_m_inv=maximum_k,maximum_sampled_nominal_steering_rate_rad_s=maximum_slew,
        static_counterfactual_full_route=dict(goal_distance_m=goal_distance,minimum_static_clearance_m=float(static.min()),nominal_elapsed_s=float(path[-1,3]),is_dynamic_trial=False),
        safe_prefix_minimum_m=minimum,safe_prefix_duration_s=float(prefix[-1,3]),original_dynamic_full_route_qualified=False,
        models=0,physical_native=0,wall_s=time.monotonic()-begin)
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
