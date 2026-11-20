"""Current stopped-body causal interval prerequisite, no motion/model claims."""
import ast
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main'

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('NO_MODEL_DIAGNOSTIC '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
    s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def function(path,name):
    node=next(n for n in ast.parse((R/path).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    env=dict(np=np,math=math);exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/path),'exec'),env);return env[name]

def scalar_distance(body,polygon):
    x,y,yaw=body[:3];cs,sn=math.cos(yaw),math.sin(yaw)
    corners=np.array([[x+cs*a-sn*b,y+sn*a+cs*b] for a,b in [(-.44,-.375),(.44,-.375),(.44,.375),(-.44,.375)]])
    q=np.asarray(polygon);edges=np.roll(q,-1,axis=0)-q
    axes=[np.array([cs,sn]),np.array([-sn,cs])]+[np.array([-e[1],e[0]]) for e in edges]
    separated=any(float((corners@n).max())<float((q@n).min()) or float((q@n).max())<float((corners@n).min()) for n in axes)
    if not separated:return 0.
    def point_segment(p,a,b):
        d=b-a;t=min(1.,max(0.,float(np.dot(p-a,d)/np.dot(d,d))));v=p-a-t*d;return math.hypot(v[0],v[1])
    values=[point_segment(p,a,b) for points,poly in [(corners,q),(q,corners)] for p in points for a,b in zip(poly,np.roll(poly,-1,axis=0))]
    return min(values)

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));started=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    manifest=read(O/'SNAPSHOT_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in manifest['files'].items())
    fixed=read(O/'FIXED_INPUTS.json');assert fixed['source_native_tick']==32210 and fixed['models_authorized'] is False
    model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200 and model['last_observed_time']<=322.1+1e-8
    body=read(RAW/'APPLIED_JOURNAL.json')[32210]['body'];known=read(RAW/'physics/SETUP.json')['known'];vertices=model['periodic']['vertices']
    origin=model['last_observed_time'];assert abs(origin-322.1)<1e-7
    swept=load('phase_original_interval_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped')
    distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    geometry=load('phase_original_static_footprint','experiments/v855_renewal_worker/exact_footprint.py')
    normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    static=float(geometry.pose_values(field,[rear])[0]);rows=[];error=0.
    for horizon in [0.,.2,1.5,3.,5.,10.,40.]:
        for uncertainty in [0.,.2]:
            bounds=swept.swept_bounds(vertices,origin,origin+horizon+uncertainty)+.10
            polygon=clipped(normals,bounds);a=float(distances(np.array([body[:3]]),polygon)[0]);b=scalar_distance(body,polygon);error=max(error,abs(a-b));assert abs(a-b)<=1e-8
            lower=-bounds[[8,12]];upper=bounds[[0,4]];center=(lower+upper)/2;radius=float(np.linalg.norm((upper-lower)/2))
            circle_field=SimpleNamespace(**vars(field));circle_field.circles=np.array([*known['known_circles'],[*center,radius]])
            circle=float(geometry.pose_values(circle_field,[rear])[0])
            # The disk wraps the same actor-radius-inflated coordinate box.
            # Its lower bound must never exceed the polygon/static lower bound.
            assert circle<=min(static,a)+1e-8
            rows.append(dict(hold_horizon_s=horizon,future_time_uncertainty_s=uncertainty,interval_start=origin,interval_end=origin+horizon+uncertainty,
                original_polygon_body_distance_m=a,independent_scalar_distance_m=b,known_static_distance_m=static,combined_lower_m=min(a,static),
                outer_coordinate_disk_lower_m=circle,original22cm_prerequisite_passed=min(a,static)>=.22-1e-8,
                support=bounds.tolist(),polygon=polygon.tolist()))
    result=dict(passed=True,diagnostic_only=True,source_native_tick=32210,coefficient_source_tick=32200,source_body=body,
        fixed_body_hold_assumption=True,not_a_coupled_steering_or_motion_certificate=True,rows=rows,independent_distance_max_error_m=error,
        complete_motion_witness=False,new_actual_response_qualified=False,models=0,physical_native=0,private_native=0,replay_native=0,wall_s=time.monotonic()-started)
    target=O/'STOPPED_BODY_INTERVAL_PREREQUISITE.json';assert not target.exists();target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert all(sha(R/p)==h for p,h in manifest['files'].items())
    print(json.dumps(dict(passed=True,rows=len(rows),distance_error=error,intervals=[dict(h=r['hold_horizon_s'],u=r['future_time_uncertainty_s'],minimum=r['combined_lower_m'],passed=r['original22cm_prerequisite_passed']) for r in rows],models=0,physical_native=0)))
if __name__=='__main__':main()
