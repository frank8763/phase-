"""Single coupled repair test, original saved inputs and fixed software cases."""
import importlib.util
import os
import sys
import time
from common import *
from common import _array


def initial_steering():
    req,_=inputs();event=read(RAW/'APPLIED_JOURNAL.json')[req['native_tick']]
    assert max(abs(a-b) for a,b in zip(event['body'],req['body']))<=1e-8
    front=event['last_ctrl'][:2];curvature=[]
    for angle,side in zip(front,[1,-1]):
        tangent=math.tan(angle);curvature.append(tangent/(.6+side*.27*tangent))
    assert abs(curvature[0]-curvature[1])<=1e-8
    return math.atan(.6*sum(curvature)/2),dict(native_tick=req['native_tick'],front_targets=front,
        measured_encoders=event['encoders'],source='original actual controller_memory at saved request03; no reinitialized or invented wheel target')


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'COUPLED_QUALIFICATION.json';assert not target.exists()
    library=ctypes.CDLL(str(O/'libslew_exact.so'));f=library.plan_slew_exact
    f.argtypes=ARGUMENTS+[ctypes.c_double];f.restype=ctypes.c_int
    angle,provenance=initial_steering();cases=[]
    req,args=inputs();far=np.ascontiguousarray(np.tile([4.,4.,.1,.1],(401,1)))
    tests=[('original_terminal',req['known'],req['body'],req['goal'],args[6],angle),
           ('empty_forward',dict(known_rectangles=[],known_circles=[]),[0.,0.,0.,0.,0.],[1.,0.],far,0.),
           ('empty_reverse',dict(known_rectangles=[],known_circles=[]),[0.,0.,0.,0.,0.],[-1.,0.],far,0.)]
    sys.path.insert(0,str(R/'experiments/v1364_space_time_vehicle'))
    spec=importlib.util.spec_from_file_location('unchanged_independent_nominal_audit',R/'experiments/v1364_space_time_vehicle/audit_software.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    for name,known,body,goal,boxes,steering in tests:
        rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4);circles=np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3)
        yaw=body[2];start=np.ascontiguousarray([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw]);output=np.empty((4096,7));stats=np.zeros(16);count=ctypes.c_int()
        code=f(rect,len(rect),circles,len(circles),start,np.ascontiguousarray(goal,dtype=float),boxes,len(boxes),.2,22000,1.5,output,len(output),ctypes.byref(count),stats,steering)
        path=output[:count.value].copy() if code==0 else None
        review=audit.audit_path(path,body,goal,known,boxes,stats[2]) if path is not None else None
        row=dict(name=name,code=code,stats=stats.tolist(),initial_center_steering_rad=steering,review=review,path=None if path is None else path.tolist())
        cases.append(row);print(json.dumps({k:v for k,v in row.items() if k!='path'}),flush=True)
    assert all(z['code']==0 and z['review']['passed'] for z in cases[1:])
    result=dict(cases=cases,actual_saved_initial_steering_provenance=provenance,
        exact_pose_and_steering_slew_integrated_in_same_search=True,
        original_complete_route_found=cases[0]['code']==0,original_physical_timing_qualified=False,
        physical_launch_allowed=False,models=0,physical_native=0,
        source_sha256=sha(C/'slew_search.cpp'),library_sha256=sha(O/'libslew_exact.so'),wall_s=time.monotonic()-begin)
    dump(target,result)


if __name__=='__main__':main()
