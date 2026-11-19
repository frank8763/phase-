"""Time-lattice FFI and causal interval table, without model imports."""
import ctypes
import importlib.util
import math
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
_array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')


def interval_table(vertices,stamp):
    s=importlib.util.spec_from_file_location('phase_original_interval_support',R/'experiments/v1020_terminal_two_route_development/periodic_support.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);rows=[]
    for i in range(401):
        lower_time=stamp+i*.2-.2;upper_time=stamp+(i+1)*.2+.2
        bounds=m.swept_bounds(vertices,lower_time,upper_time)
        lower=-bounds[[8,12]];upper=bounds[[0,4]]
        center=(lower+upper)/2;radius=float(np.linalg.norm((upper-lower)/2))+.1
        rows.append([*center,radius])
    return np.ascontiguousarray(rows,dtype=float)


def solve(known,body,goal,balls):
    assert len(body)==5 and len(goal)==2 and np.isfinite([*body,*goal]).all()
    assert max(abs(v) for v in body[3:])<=.003,'START_NOT_AT_MEASURED_REST'
    assert balls.shape==(401,3) and np.isfinite(balls).all() and (balls[:,2]>=0).all()
    lib=ctypes.CDLL(str(O/'libtimed.so'))
    lib.plan_timed.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,_array,ctypes.c_int,
                            ctypes.c_double,ctypes.c_int,ctypes.c_double,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array]
    lib.plan_timed.restype=ctypes.c_int
    rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4)
    circles=np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3)
    yaw=body[2];start=np.ascontiguousarray([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw])
    out=np.empty((4096,7));stats=np.zeros(8);count=ctypes.c_int()
    code=lib.plan_timed(rect,len(rect),circles,len(circles),start,np.ascontiguousarray(goal,dtype=float),balls,len(balls),.2,
                        22000,1.5,out,len(out),ctypes.byref(count),stats)
    assert code in [0,1,2,3]
    return out[:count.value].copy() if code==0 else None,dict(code=code,expanded=int(stats[0]),kernel_wall_s=float(stats[1]),
             required_m=float(stats[2]),goal_found=bool(stats[3]),nodes=int(stats[4]),closest_goal_distance_m=float(stats[5]),
             elapsed_route_s=float(stats[6]),samples=int(stats[7]),max_expand=22000,max_wall_s=1.5,
             status=['COMPLETE_NOMINAL_TIMED_ROUTE','NO_COMPLETE_TIMED_ROUTE_WITHIN_BUDGET','START_BELOW22','CAPACITY_REFUSAL'][code])
