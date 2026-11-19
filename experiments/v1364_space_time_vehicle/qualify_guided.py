"""Original terminal joint interval/rectangle search, plus fixed boundaries."""
import ctypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import numpy as np
from planner import _array

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    target=O/'GUIDED_RESULT.json';assert not target.exists(),'QUALIFICATION_ALREADY_RECORDED'
    req=json.loads((R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json').read_text())
    saved=json.loads((R/'runs/v1362_terminal_route_diagnosis/CONNECTIVITY_AND_SHAPE.json').read_text())
    assert saved['coefficient_source_tick']<=req['native_tick']
    vertices=saved['coefficient_snapshot']['vertices']
    spec=importlib.util.spec_from_file_location('phase_exact_swept_bounds',R/'experiments/v1020_terminal_two_route_development/periodic_support.py')
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);table=[]
    for tick in range(401):
        lower_time=req['sim_time']+tick*.2-.2;upper_time=req['sim_time']+(tick+1)*.2+.2
        bounds=p.swept_bounds(vertices,lower_time,upper_time);lo=-bounds[[8,12]];hi=bounds[[0,4]]
        table.append([*((lo+hi)/2),*((hi-lo)/2)])
    lib=ctypes.CDLL(str(O/'libinterval_guided.so'))
    lib.plan_interval_guided.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,_array,ctypes.c_int,ctypes.c_double,ctypes.c_int,ctypes.c_double,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array]
    lib.plan_interval_guided.restype=ctypes.c_int;cases=[]
    tests=[('original_terminal',req['known'],req['body'],req['goal'],table),
           ('empty_forward',dict(known_rectangles=[],known_circles=[]),[0.,0.,0.,0.,0.],[1.,0.],np.tile([4.,4.,.1,.1],(401,1))),
           ('blocked_start',req['known'],req['body'],req['goal'],np.tile([*req['body'][:2],1.,1.],(401,1)))]
    for name,known,body,goal,boxes in tests:
        rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4);circles=np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3)
        yaw=body[2];start=np.ascontiguousarray([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw]);output=np.empty((4096,7));stats=np.zeros(8);count=ctypes.c_int()
        code=lib.plan_interval_guided(rect,len(rect),circles,len(circles),start,np.ascontiguousarray(goal,dtype=float),np.ascontiguousarray(boxes,dtype=float),401,.2,22000,1.5,output,len(output),ctypes.byref(count),stats)
        row=dict(name=name,body=body,goal=goal,code=code,stats=stats.tolist(),path=output[:count.value].tolist() if code==0 else None)
        cases.append(row);print(json.dumps({k:v for k,v in row.items() if k!='path'}),flush=True)
    assert cases[1]['code']==0 and cases[2]['code']==2
    result=dict(cases=cases,forecast_center_rectangle_table=table,source_tick=saved['coefficient_source_tick'],time_origin=req['sim_time'],
                unchanged_actor_radius_m=.1,library_sha256=hashlib.sha256((O/'libinterval_guided.so').read_bytes()).hexdigest(),
                models=0,physical_native=0,actual_braking_and_tracking_qualified=False,automatic_physics=False,wall_s=time.monotonic()-begin,
                review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
    assert result['review_pending_unchanged'] and result['current_pointer_unchanged']
    target.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
