"""Read-only data and exact existing FFI boundary for zero-model diagnostics."""
import ctypes
import hashlib
import json
import math
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
RAW=R/'runs/v858_nav2_verified/v1361/sweep_terminal_dynamic_main'
_array=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS')
ARGUMENTS=[_array,ctypes.c_int,_array,ctypes.c_int,_array,_array,_array,ctypes.c_int,
           ctypes.c_double,ctypes.c_int,ctypes.c_double,_array,ctypes.c_int,ctypes.POINTER(ctypes.c_int),_array]


def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def inputs():
    req=read(R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json')
    old=read(R/'runs/v1364_space_time_vehicle/KINODYNAMIC_RESULT.json')
    assert old['source_tick']==req['native_tick']==15105
    table=np.ascontiguousarray(old['forecast_center_rectangle_table'],dtype=float)
    body=req['body'];yaw=body[2];known=req['known']
    args=[np.ascontiguousarray(known['known_rectangles'],dtype=float).reshape(-1,4),len(known['known_rectangles']),
          np.ascontiguousarray(known['known_circles'],dtype=float).reshape(-1,3),len(known['known_circles']),
          np.ascontiguousarray([body[0]-.3*math.cos(yaw),body[1]-.3*math.sin(yaw),yaw]),
          np.ascontiguousarray(req['goal'],dtype=float),table,len(table),.2,22000,1.5]
    return req,args


def call(path,symbol,mode=None):
    lib=ctypes.CDLL(str(path));function=getattr(lib,symbol)
    function.argtypes=ARGUMENTS+([ctypes.c_int] if mode is not None else []);function.restype=ctypes.c_int
    req,args=inputs();output=np.empty((4096,7));stats=np.zeros(16);count=ctypes.c_int()
    args.extend([output,len(output),ctypes.byref(count),stats])
    if mode is not None:args.append(mode)
    code=function(*args)
    return dict(code=code,stats=stats.tolist(),path=None if code else output[:count.value].tolist(),
                saved_request_sha256=sha(R/'runs/v1362_terminal_route_diagnosis/ORIGINAL_REQUEST03.json'))
