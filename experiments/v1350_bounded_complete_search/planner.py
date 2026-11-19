"""Pure bounded search FFI; original NumPy must revalidate any returned path."""
import ctypes
from pathlib import Path
import time
import numpy as np

R=Path(__file__).resolve().parents[2];O=R/'runs/v1350_bounded_complete_search'
LIB=O/'libsearch.so';_library=None
_array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')


def propose(known,body,goal,ball,guard=.22,mode=1,maxwall=1.5,maxexpand=22000):
    global _library
    assert mode in [0,1,2] and 0<maxwall<=15. and type(maxexpand) is int and 0<maxexpand<=22000
    assert len(body)==5 and len(goal)==2 and np.isfinite([*body,*goal,guard,maxwall]).all()
    assert .22<=guard<=.30
    if _library is None:
        _library=ctypes.CDLL(str(LIB))
        _library.plan_route.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,
            _array,_array,ctypes.c_double,ctypes.c_double,ctypes.c_int,ctypes.c_double,
            ctypes.c_int,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array]
        _library.plan_route.restype=ctypes.c_int
    rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4)
    circles=list(known['known_circles'])
    if ball is not None:
        assert np.asarray(ball[0]).shape==(2,) and np.isfinite([*ball[0],ball[1]]).all() and ball[1]>=0.
        circles.append([*ball[0],ball[1]])
    circles=np.ascontiguousarray(circles,dtype=float).reshape(-1,3)
    assert np.isfinite(rect).all() and np.isfinite(circles).all()
    assert (rect[:,2:]>0).all() and (circles[:,2]>=0).all()
    yaw=body[2];start=np.ascontiguousarray([body[0]-.3*np.cos(yaw),body[1]-.3*np.sin(yaw),yaw])
    goal=np.ascontiguousarray(goal,dtype=float);out=np.empty((4096,4));stats=np.zeros(8);count=ctypes.c_int()
    begin=time.perf_counter()
    code=_library.plan_route(rect,len(rect),circles,len(circles),start,goal,.50,max(.27,guard),maxexpand,maxwall,mode,out,len(out),ctypes.byref(count),stats)
    names={0:'GLOBAL_GOAL_PATH' if stats[3] else 'SAFE_PROGRESS_PREFIX',1:'NO_MEANINGFUL_GLOBAL_PROGRESS_WITHIN_BUDGET',2:'START_BELOW_HARD_FLOOR',3:'OUTPUT_CAPACITY_REFUSAL',4:'DENSE_CERTIFICATE_REJECTED'}
    assert code in names,'SEARCH_INTERNAL_ERROR'
    assert 0<=count.value<=len(out) and 0<=stats[0]<=22000
    report=dict(status=names[code],expanded=int(stats[0]),wall_s=time.perf_counter()-begin,
                kernel_wall_s=float(stats[1]),guard_m=float(stats[2]),generated_nodes=int(stats[4]),
                minimum_clearance_m=float(stats[5]),body_goal_distance_m=float(stats[7]),
                mode='original_euclidean' if mode==0 else ('obstacle_guided_body_goal' if mode==1 else 'analytic_reeds_shepp_body_goal'),
                nominal_curvature_m_inv=.50,models=0,physical_native=0)
    if code:return None,report
    path=out[:count.value].copy();assert np.isfinite(path).all()
    return path,report
