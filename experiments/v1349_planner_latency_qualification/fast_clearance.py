"""Validated ndarray boundary to pure compiled footprint distance arithmetic."""
import ctypes
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
LIB=R/'runs/v1349_planner_latency_qualification/libclearance.so'
_library=None
_array=np.ctypeslib.ndpointer(dtype=np.float64, flags='C_CONTIGUOUS')


class Geometry:
    def __init__(self,field):
        global _library
        if _library is None:
            _library=ctypes.CDLL(str(LIB))
            _library.footprint_values.argtypes=[_array,ctypes.c_size_t,*([ctypes.c_double]*6),
                _array,ctypes.c_size_t,_array,ctypes.c_size_t,_array,ctypes.c_size_t,ctypes.c_double,_array]
            _library.footprint_values.restype=None
        self.half=np.asarray(field.half,float).copy()
        self.offset=np.asarray(field.center_local,float).copy()
        self.rectangles=np.ascontiguousarray(field.rectangles,dtype=float).reshape(-1,4)
        self.circles=np.ascontiguousarray(field.circles,dtype=float).reshape(-1,3)
        self.points=np.ascontiguousarray(field.sensor_points,dtype=float).reshape(-1,2)
        self.lower=float(field.config.lower);self.upper=float(field.config.upper)
        self.sensor_extra=float(field.sensor_extra)
        assert self.half.shape==self.offset.shape==(2,) and (self.half>0).all()
        assert all(np.isfinite(x).all() for x in [self.half,self.offset,self.rectangles,self.circles,self.points])
        assert np.isfinite([self.lower,self.upper,self.sensor_extra]).all() and self.lower<self.upper

    def values(self,poses):
        p=np.ascontiguousarray(poses,dtype=float).reshape(-1,3)
        assert np.isfinite(p).all(),'NONFINITE_DISTANCE_POSES'
        output=np.empty(len(p),dtype=float)
        _library.footprint_values(p,len(p),*self.half,*self.offset,self.lower,self.upper,
            self.rectangles,len(self.rectangles),self.circles,len(self.circles),
            self.points,len(self.points),self.sensor_extra,output)
        return output


def pose_values(field,poses):
    owner=getattr(field,'_compiled_geometry',None)
    if owner is None:
        owner=Geometry(field);field._compiled_geometry=owner
    return owner.values(poses)
