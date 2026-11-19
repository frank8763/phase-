"""Independent software geometry, timing and causal-table readback; no physics."""
import copy
import ctypes
import importlib.util
import json
import math
import os
from pathlib import Path
import time
from types import SimpleNamespace
import numpy as np
from planner import _array

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
spec=importlib.util.spec_from_file_location('original_numpy_whole_footprint',R/'experiments/v855_renewal_worker/exact_footprint.py')
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)


def field(rectangles,circles,bounds=5.):
    return SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.array(rectangles),circles=np.array(circles),sensor_points=[],sensor_extra=0.,
        config=SimpleNamespace(lower=-bounds,upper=bounds))


def audit_path(path,body,goal,known,boxes,margin):
    p=np.array(path,float);assert p.ndim==2 and p.shape[1]==7 and len(p)>=21 and np.isfinite(p).all()
    times=p[:,3];assert abs(times[0])<1e-8 and np.max(abs(np.diff(times)-.1))<1e-8,'TIME_SEQUENCE'
    rear=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]
    assert np.max(abs(p[0,:3]-rear))<1e-8 and abs(p[0,4])<1e-8
    assert np.max(abs(p[:,4]))<=.1+1e-8 and np.isin(p[:,6],[0,1,2,3,4,5]).all()
    dtheta=np.arctan2(np.sin(np.diff(p[:,2])),np.cos(np.diff(p[:,2])))
    chord=np.linalg.norm(np.diff(p[:,:2],axis=0),axis=1)
    ratio=np.ones_like(chord);mask=abs(dtheta)>1e-10;ratio[mask]=abs(dtheta[mask])/(2*np.sin(abs(dtheta[mask])/2))
    length=chord*ratio;expected=.05*(abs(p[1:,4])+abs(p[:-1,4]))
    assert np.max(abs(length-expected))<=1e-8,'VELOCITY_INTEGRATION'
    assert np.max(abs(np.diff(p[:,4])))<=.010000001,'INSTANTANEOUS_VELOCITY_CHANGE'
    moving=length>1e-8
    assert (abs(dtheta[moving])/length[moving]<=.50000001).all(),'CURVATURE_LIMIT'
    wait=(p[1:,6]==4)|(p[1:,6]==5)
    assert np.max(abs(p[1:,4][wait]),initial=0.)<1e-8 and np.max(abs(p[:-1,4][wait]),initial=0.)<1e-8,'WAIT_WHILE_MOVING'
    assert np.max(chord[wait],initial=0.)<1e-8 and np.max(abs(dtheta[wait]),initial=0.)<1e-8
    assert (p[-20:,6]==5).all() and np.max(abs(p[-20:,4]))<=1e-8,'TERMINAL_STOP_TAIL'
    endpoint=p[-1,:2]+.3*np.array([math.cos(p[-1,2]),math.sin(p[-1,2])])
    assert np.linalg.norm(endpoint-goal)<=.32+1e-8,'NOMINAL_BODY_GOAL'
    static=geometry.pose_values(field(known['known_rectangles'],known['known_circles']),p[:,:3]);minimum=float(static.min())
    assert minimum>=margin-1e-8,'STATIC_ROUTE_GEOMETRY'
    for row in p:
        index=int(math.floor((row[3]+1e-8)/.2));assert 0<=index<len(boxes),'FORECAST_HORIZON'
        dynamic=float(geometry.pose_values(field([boxes[index]],[],bounds=1e6),[row[:3]])[0])-.1
        minimum=min(minimum,dynamic);assert dynamic>=margin-1e-8,'TIMED_DYNAMIC_GEOMETRY'
    return dict(passed=True,samples=len(p),nominal_elapsed_s=float(times[-1]),minimum_sampled_clearance_m=minimum,
                actual_steering_tracking_and_braking_qualified=False,models=0)


def run_fixture(lib,name,body,goal,boxes):
    known=dict(known_rectangles=[],known_circles=[])
    rect=np.empty((0,4));circles=np.empty((0,3));out=np.empty((4096,7));stats=np.zeros(8);count=ctypes.c_int()
    yaw=body[2];start=np.ascontiguousarray([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw])
    code=lib.plan_interval_kinodynamic(rect,0,circles,0,start,np.ascontiguousarray(goal,dtype=float),boxes,401,.2,22000,1.5,out,len(out),ctypes.byref(count),stats)
    path=out[:count.value].copy() if code==0 else None
    review=audit_path(path,body,goal,known,boxes,stats[2]) if path is not None else None
    return dict(name=name,code=code,stats=stats.tolist(),body=body,goal=goal,review=review,path=None if path is None else path.tolist())


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'INDEPENDENT_SOFTWARE_AUDIT.json';assert not target.exists()
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    lib=ctypes.CDLL(str(O/'libinterval_kinodynamic.so'))
    lib.plan_interval_kinodynamic.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,_array,ctypes.c_int,ctypes.c_double,ctypes.c_int,ctypes.c_double,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array]
    lib.plan_interval_kinodynamic.restype=ctypes.c_int
    far=np.ascontiguousarray(np.tile([4.,4.,.1,.1],(401,1)));wait=far.copy();wait[:40]=[1.4,0.,.3,.3]
    cases=[run_fixture(lib,'empty_forward',[0.,0.,0.,0.,0.],[1.,0.],far),
           run_fixture(lib,'empty_reverse',[0.,0.,0.,0.,0.],[-1.,0.],far),
           run_fixture(lib,'moving_obstacle_departure',[0.,0.,0.,0.,0.],[2.,0.],wait)]
    assert all(x['code']==0 and x['review']['passed'] for x in cases),'FIXED_SOFTWARE_BOUNDARY_FAILED'
    # Time/stop/source proof fixtures must fail even though stored geometry
    # and a worker exit code may otherwise look positive.
    negatives=[];base=np.array(cases[0]['path'])
    for name in ['backward_clock','instantaneous_speed_jump','nonzero_final_stop','goal_displaced','forecast_tampered']:
        path=base.copy();goal=[1.,0.];boxes=far.copy()
        if name=='backward_clock':path[5,3]=path[4,3]-.1
        elif name=='instantaneous_speed_jump':path[3,4]=.1
        elif name=='nonzero_final_stop':path[-1,4]=.01
        elif name=='goal_displaced':goal=[2.,0.]
        else:boxes[:]=[0.,0.,1.,1.]
        try:audit_path(path,[0.,0.,0.,0.,0.],goal,dict(known_rectangles=[],known_circles=[]),boxes,.27)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('TAMPER_ACCEPTED '+name)
    seam=ctypes.CDLL(str(O/'libqualification_seams.so'))
    seam.box_clearance_probe.argtypes=[_array,ctypes.c_int,_array,ctypes.c_double,_array]
    rng=np.random.default_rng(1364);poses=np.c_[rng.uniform(-3,3,3000),rng.uniform(-3,3,3000),rng.uniform(-math.pi,math.pi,3000)]
    box=np.array([.7,-.9,.31,.24]);exact=geometry.pose_values(field([box],[],bounds=1e6),poses)-.1;errors=[]
    for requested in [1e100,.27]:
        values=np.empty(len(poses));seam.box_clearance_probe(np.ascontiguousarray(poses),len(poses),box,requested,values)
        if requested==1e100:assert np.max(abs(values-exact))<1e-8
        else:assert (values<=exact+1e-8).all() and np.array_equal(values>=.27,exact>=.27)
        errors.append(dict(requested=requested,maximum_error_m=float(np.max(abs(values-exact))),classification_matches=True))
    original=json.loads((O/'KINODYNAMIC_RESULT.json').read_text())['cases'][0]
    assert original['code']==1 and original['path'] is None
    proof=dict(passed=True,scope='software-only fixed fixtures and independent geometry; original terminal NOT_QUALIFIED',cases=cases,
        original_terminal_complete_route_qualified=False,negative_cases=negatives,geometry_cases=3000,geometry_checks=errors,
        models=0,physical_native=0,actual_control_qualification=False,physical_launch=False,wall_s=time.monotonic()-begin,
        review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert proof['review_pending_unchanged'] and proof['current_pointer_unchanged']
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='cases'}))
    print(json.dumps([{k:v for k,v in x.items() if k!='path'} for x in cases]))


if __name__=='__main__':main()
