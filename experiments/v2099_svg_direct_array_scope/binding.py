from context import R,O,read,sha,native_authority
def bind():
 a,frozen=native_authority();import ctypes
 p=R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so';assert frozen[str(p.relative_to(R))]==sha(p);lib=ctypes.CDLL(str(p));dp=ctypes.POINTER(ctypes.c_double);ip=ctypes.POINTER(ctypes.c_int);vp=ctypes.c_void_p;i=ctypes.c_int
 for n in ['abi_version','state_dimension','control_dimension']:fn=getattr(lib,'phase_svg_'+n);fn.argtypes=[];fn.restype=i
 lib.phase_svg_error.argtypes=[ctypes.POINTER(ctypes.c_char),i];lib.phase_svg_error.restype=i;lib.phase_svg_create.argtypes=[dp,i,ip,i];lib.phase_svg_create.restype=vp;lib.phase_svg_set_maps.argtypes=[vp,i,i,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,dp,dp,dp];lib.phase_svg_set_maps.restype=i;lib.phase_svg_solve.argtypes=[vp,dp,i,dp,i,dp];lib.phase_svg_solve.restype=i;lib.phase_svg_call_counts.argtypes=[vp,ctypes.POINTER(ctypes.c_ulonglong),i];lib.phase_svg_call_counts.restype=i;lib.phase_svg_destroy.argtypes=[vp];lib.phase_svg_destroy.restype=None;return lib
