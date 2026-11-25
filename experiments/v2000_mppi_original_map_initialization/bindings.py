"""Exact preexisting ABI signatures; no dlopen until lane authority verified."""
from common import R,ROOT,O,read,sha,authority
import ctypes

def bind_mppi():
 a,frozen=authority();p=R/'runs/v1998_mppi_map_bootstrap_preparation/libphase_mppi_map_bootstrap.so';assert frozen['files'][str(p.relative_to(R))]==sha(p);lib=ctypes.CDLL(str(p));dp=ctypes.POINTER(ctypes.c_double);bp=ctypes.POINTER(ctypes.c_ubyte);vp=ctypes.c_void_p;i=ctypes.c_int
 for name in ['abi_version','request_dimension']:fn=getattr(lib,'phase_mppi_'+name);fn.argtypes=[];fn.restype=i
 lib.phase_mppi_error.argtypes=[ctypes.POINTER(ctypes.c_char),i];lib.phase_mppi_error.restype=i;lib.phase_mppi_create.argtypes=[];lib.phase_mppi_create.restype=vp
 lib.phase_mppi_solve.argtypes=[vp,ctypes.c_longlong,dp,dp,i,bp,i,i,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,i,dp];lib.phase_mppi_solve.restype=i
 lib.phase_mppi_call_count.argtypes=[vp];lib.phase_mppi_call_count.restype=ctypes.c_ulonglong;lib.phase_mppi_poisoned.argtypes=[vp];lib.phase_mppi_poisoned.restype=i;lib.phase_mppi_destroy.argtypes=[vp];lib.phase_mppi_destroy.restype=None;return lib

def bind_svg():
 a,frozen=authority();p=R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so';assert frozen['files'][str(p.relative_to(R))]==sha(p);lib=ctypes.CDLL(str(p));dp=ctypes.POINTER(ctypes.c_double);ip=ctypes.POINTER(ctypes.c_int);vp=ctypes.c_void_p;i=ctypes.c_int
 for name in ['abi_version','state_dimension','control_dimension']:fn=getattr(lib,'phase_svg_'+name);fn.argtypes=[];fn.restype=i
 lib.phase_svg_error.argtypes=[ctypes.POINTER(ctypes.c_char),i];lib.phase_svg_error.restype=i;lib.phase_svg_create.argtypes=[dp,i,ip,i];lib.phase_svg_create.restype=vp;lib.phase_svg_set_maps.argtypes=[vp,i,i,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,dp,dp,dp];lib.phase_svg_set_maps.restype=i
 lib.phase_svg_solve.argtypes=[vp,dp,i,dp,i,dp];lib.phase_svg_solve.restype=i;lib.phase_svg_call_counts.argtypes=[vp,ctypes.POINTER(ctypes.c_ulonglong),i];lib.phase_svg_call_counts.restype=i;lib.phase_svg_destroy.argtypes=[vp];lib.phase_svg_destroy.restype=None;return lib
