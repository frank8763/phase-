"""Canonical graph FFI. Source and preprocessing costs are explicit."""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
_array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')


def solve(graph,known=None,body=None,goal=None,boxes=None,initial_gear=None):
    begin=time.monotonic();req=graph['request'];known=known or req['known'];body=req['body'] if body is None else body;goal=req['goal'] if goal is None else goal
    boxes=np.ascontiguousarray(graph['center_rectangle_table'] if boxes is None else boxes,dtype=float)
    metadata=[];samples=[]
    for edge in graph['edges']:
        rows=np.asarray(edge['samples']);still=(abs(rows[:-1,4])<=1e-10)&(abs(rows[1:,4])<=1e-10)
        rest=float(np.diff(rows[:,3])[still].sum());rest_ticks=math.ceil(rest/.2-1e-8)
        metadata.append([edge['start_heading'],edge['end_heading'],*edge['offset'],edge['gear'],len(samples),len(rows),round(edge['duration_s']/.2),rest_ticks]);samples.extend(rows.tolist())
    metadata=np.ascontiguousarray(metadata,dtype=float);samples=np.ascontiguousarray(samples,dtype=float)
    rect=np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4);circles=np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3)
    library=ctypes.CDLL(str(O/'libgraph.so'));f=library.plan_graph
    f.argtypes=[_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,_array,ctypes.c_int,_array,_array,ctypes.c_int,_array,ctypes.c_int,ctypes.c_int,ctypes.c_double,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array];f.restype=ctypes.c_int
    output=np.empty((4096,10));stats=np.zeros(16);count=ctypes.c_int();prepared=time.monotonic()
    code=f(rect,len(rect),circles,len(circles),np.ascontiguousarray(body,dtype=float),np.ascontiguousarray(goal,dtype=float),boxes,len(boxes),
           np.ascontiguousarray(graph['headings'],dtype=float),metadata,len(metadata),samples,
           graph['initial_gear'] if initial_gear is None else initial_gear,22000,1.5,output,len(output),ctypes.byref(count),stats)
    assert code in [0,1,2,3,6]
    return dict(code=code,stats=stats.tolist(),path=None if code else output[:count.value].tolist(),
                preprocessing_s=prepared-begin,total_call_wall_s=time.monotonic()-begin,
                same22000and1p5s_bounds=True,canonical_primitive_edges=len(metadata),
                models=0,physical_native=0,physical_response_qualified=False)
