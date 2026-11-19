"""Signed geometry agreement and same-request full planner timing, zero models."""
import ast
import copy
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


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:
            raise AssertionError('GEOMETRY_QUALIFICATION_NO_PHYSICAL '+name)


sys.meta_path.insert(0,NoPhysical())
import numpy as np
from fast_clearance import Geometry
import candidate

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('QUALIFICATION_900S')));signal.alarm(900)
    original=load('unaltered_v1348_observed_route',R/'experiments/v1348_recoverable_tracking/observed_route.py')
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.array(known['known_rectangles']),circles=np.array(known['known_circles']),
        sensor_points=np.empty((0,2)),sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    rng=np.random.default_rng(1349)
    poses=np.c_[rng.uniform(-6.,6.,(40000,2)),rng.uniform(-4*np.pi,4*np.pi,40000)]
    raw=R/'runs/v858_nav2_verified/v1348/rpp_async_default_dynamic_main'
    with np.load(raw/'physics/NATIVE_TRACE.npz',allow_pickle=False) as z:
        q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
        saved=np.c_[q[:,:2]-.3*np.c_[np.cos(yaw),np.sin(yaw)],yaw]
    poses=np.vstack([poses,saved]);results=[];maximum=0.;classifications=0
    fixtures=[field]
    varied=copy.deepcopy(field);varied.half=np.array([.2,.47]);varied.center_local=np.array([-.12,.08])
    varied.sensor_points=rng.uniform(-4.,4.,(12,2));varied.sensor_extra=.035
    varied.circles=np.vstack([varied.circles,[2.93,-.98,.62]]);fixtures.append(varied)
    for f in fixtures:
        accelerated=Geometry(f);old_time=new_time=0.;field_error=0.
        for offset in range(0,len(poses),2000):
            pp=poses[offset:offset+2000]
            start=time.perf_counter();a=original.geometry.pose_values(f,pp);old_time+=time.perf_counter()-start
            start=time.perf_counter();b=accelerated.values(pp);new_time+=time.perf_counter()-start
            error=float(np.max(abs(a-b)));field_error=max(field_error,error)
            assert error<=1e-10,('GEOMETRY_MISMATCH',offset,error)
            for threshold in [.15,.22,.245,.27]:
                assert np.array_equal(a>=threshold-1e-8,b>=threshold-1e-8)
                classifications+=len(a)
        maximum=max(maximum,field_error)
        results.append(dict(poses=len(poses),max_abs_error=field_error,numpy_wall_s=old_time,compiled_wall_s=new_time,speedup=old_time/new_time))
    # Constructed exact acceptance boundaries and just-inside/outside samples
    # for circles, workspace and signed overlap. No random threshold luck.
    simple=copy.deepcopy(field);simple.rectangles=np.empty((0,4));simple.circles=np.array([[0.,0.,.1]])
    boundary=[]
    for angle in [0.,.2,math.pi/4,math.pi/2,math.pi]:
        for threshold in [0.,.15,.22,.245,.27]:
            for epsilon in [-1e-7,0.,1e-7]:
                # Robot local+x circle separation with rear-frame offset.
                d=.44+.1+threshold+epsilon
                boundary.append([-(d+.3)*math.cos(angle),-(d+.3)*math.sin(angle),angle])
    a=original.geometry.pose_values(simple,boundary);b=Geometry(simple).values(boundary)
    assert np.max(abs(a-b))<=1e-10
    for threshold in [.15,.22,.245,.27]:assert np.array_equal(a>=threshold-1e-8,b>=threshold-1e-8)
    try:Geometry(field).values([[float('nan'),0.,0.]])
    except AssertionError:pass
    else:raise AssertionError('NONFINITE_GEOMETRY_ACCEPTED')
    geometry_proof=dict(passed=True,fields=results,max_abs_error=maximum,
        threshold_classifications=classifications,constructed_boundary_poses=len(boundary),
        nonfinite_denied=True,models=0,physical_native=0)
    (O/'GEOMETRY_QUALIFICATION.json').write_text(json.dumps(geometry_proof,indent=2)+'\n')
    print(json.dumps(dict(geometry_passed=True,maximum_error=maximum,fields=results)),flush=True)
    benchmarks=[]
    for index in [1,4,8]:
        request=json.loads((raw/'planner_jobs'/('request%02d.json'%index)).read_text())
        ball=(np.asarray(request['ball'][:2]),request['ball'][2]);args=(request['known'],request['body'],request['goal'],ball)
        start=time.perf_counter();old_path,old_report=original.propose(*args,guard=.22);old_elapsed=time.perf_counter()-start
        start=time.perf_counter();new_path,new_report=candidate.propose(*args,guard=.22);new_elapsed=time.perf_counter()-start
        assert old_path is not None and new_path is not None,(index,old_report,new_report)
        accepted,dense=original.revalidate(request['known'],new_path,request['body'],ball,guard=.22)
        assert accepted,('ORIGINAL_NUMPY_CERTIFICATE_REJECTED',index,dense)
        exact_shape=old_path.shape==new_path.shape
        path_error=float(np.max(abs(old_path-new_path))) if exact_shape else None
        row=dict(saved_request=index,numpy_wall_s=old_elapsed,compiled_wall_s=new_elapsed,
                 speedup=old_elapsed/new_elapsed,old_report=old_report,new_report=new_report,
                 same_shape=exact_shape,maximum_path_element_error=path_error,
                 exact_path_equal=bool(exact_shape and np.array_equal(old_path,new_path)),
                 original_numpy_dense_validation=dense,new_full_goal=new_report['status']=='GLOBAL_GOAL_PATH')
        benchmarks.append(row)
        (O/('SAVED_PROPOSAL%02d.json'%index)).write_text(json.dumps(dict(request=request,new_path=new_path.tolist(),old_path=old_path.tolist()),indent=2)+'\n')
        print(json.dumps(row),flush=True)
        (O/'PARTIAL_BENCHMARK.json').write_text(json.dumps(benchmarks,indent=2)+'\n')
    proof=dict(passed=True,scope='saved-data distance and planner latency qualification only',
        geometry=geometry_proof,benchmarks=benchmarks,
        every_new_path_independently_validated_original_numpy=True,
        all_paths_equal_within1e8=all(x['same_shape'] and x['maximum_path_element_error']<=1e-8 for x in benchmarks),
        binary_sha256=hashlib.sha256((O/'libclearance.so').read_bytes()).hexdigest(),
        full_goal_successes=sum(x['new_full_goal'] for x in benchmarks),
        physical_navigation_tested=False,realtime_proven=False,models=0,physical_native=0)
    (O/'QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');signal.alarm(0)
    print(json.dumps(dict(passed=True,models=0,all_paths_equal=proof['all_paths_equal_within1e8'],full_goals=proof['full_goal_successes'])),flush=True)


if __name__=='__main__':main()
