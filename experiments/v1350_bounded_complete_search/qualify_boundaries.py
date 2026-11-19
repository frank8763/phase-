"""Pure search success/refusal seams, goal region and unchanged exact geometry."""
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
from planner import propose,LIB

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    spec=importlib.util.spec_from_file_location('unaltered_numpy_validator',R/'experiments/v1348_recoverable_tracking/observed_route.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    checks={};known=dict(known_rectangles=[],known_circles=[]);cases=[]
    for name,body,goal in [('forward',[-1.,-1.,0.,0.,0.],[2.,-1.]),
                           ('reverse',[1.,1.,0.,0.,0.],[-2.,1.]),
                           ('mirror',[-1.,1.,0.,0.,0.],[2.,1.]),
                           ('turn',[0.,0.,1.5707963267948966,0.,0.],[2.,2.])]:
        path,report=propose(known,body,goal,None,mode=2)
        assert path is not None and report['status']=='GLOBAL_GOAL_PATH',(name,report)
        valid,proof=old.revalidate(known,path,body,None,guard=.22);assert valid
        yaw=path[-1,2];final=path[-1,:2]+.3*np.array([np.cos(yaw),np.sin(yaw)])
        assert np.linalg.norm(final-goal)<=.32+1e-8
        assert report['expanded']<=22000 and report['wall_s']<1.6
        # Check every signed analytic edge obeys the original car curvature
        # and heading/position step conventions, with no instantaneous yaw.
        delta=np.diff(path[:,:3],axis=0);length=np.linalg.norm(delta[:,:2],axis=1)
        angle=np.arctan2(np.sin(delta[:,2]),np.cos(delta[:,2]))
        assert ((abs(angle)<=.5*length+1e-7)|(length<1e-12)).all()
        assert ((length>1e-12)|(abs(angle)<1e-10)).all()
        cases.append(dict(name=name,passed=True,report=report,independent_original_geometry=proof,
                          body_goal_distance_m=float(np.linalg.norm(final-goal))))
    checks['analytic_root_forward_reverse_turn_mirror_success_original_geometry']=True
    # Search's distance primitive in THIS linked binary must still agree with
    # original signed exact rectangle/circle geometry, not just an older .so.
    lib=ctypes.CDLL(str(LIB));array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
    lib.footprint_values.argtypes=[array,ctypes.c_size_t,*([ctypes.c_double]*6),array,ctypes.c_size_t,array,ctypes.c_size_t,array,ctypes.c_size_t,ctypes.c_double,array]
    source=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),
        rectangles=np.array(source['known_rectangles']),circles=np.array(source['known_circles']),
        sensor_points=np.empty((0,2)),sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    rng=np.random.default_rng(1350);poses=np.ascontiguousarray(np.c_[rng.uniform(-5.5,5.5,(3000,2)),rng.uniform(-np.pi,np.pi,3000)])
    a=old.geometry.pose_values(field,poses);b=np.empty(len(poses));lib.footprint_values(poses,len(poses),.44,.375,.3,0.,-5.,5.,field.rectangles,len(field.rectangles),field.circles,len(field.circles),field.sensor_points,0,0.,b)
    error=float(np.max(abs(a-b)));assert error<=1e-10
    for threshold in [.15,.22,.245,.27]:assert np.array_equal(a>=threshold-1e-8,b>=threshold-1e-8)
    checks['current_linked_binary_signed_geometry_thresholds']=True
    dangerous=source.copy();dangerous['known_circles']=[*source['known_circles'],[0.,0.,2.]]
    path,report=propose(dangerous,[0.,0.,0.,0.,0.],[2.,-1.],None,mode=2)
    assert path is None and report['status']=='START_BELOW_HARD_FLOOR'
    checks['unsafe_start_refuses']=True
    for bad in ['nan','budget','mode','negative_radius']:
        args=dict(known=known,body=[0.,0.,0.,0.,0.],goal=[2.,-1.],ball=None,mode=2)
        if bad=='nan':args['body'][0]=float('nan')
        if bad=='budget':args['maxexpand']=22001
        if bad=='mode':args['mode']=3
        if bad=='negative_radius':args['ball']=([1.,1.],-.1)
        try:propose(**args)
        except AssertionError:pass
        else:raise AssertionError('INVALID_FFI_INPUT_ACCEPTED '+bad)
    checks['nonfinite_oversized_work_mode_and_negative_radius_denied']=True
    result=dict(passed=all(checks.values()),checks=checks,cases=cases,
                current_binary_geometry_maximum_error=error,geometry_queries=3000,
                binary_sha256=hashlib.sha256(LIB.read_bytes()).hexdigest(),models=0,physical_native=0,
                synthetic_empty_field_only=True,real_saved_complete_route_readiness=False)
    (O/'BOUNDARY_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
