"""Exact C ABI signature binding. Source inspection is not solver permission."""
import ctypes
from context import O,R,read,sha
def inspect_library(source):
 build=read(O/'BUILD_RESULT.json');assert build['passed']and build['closed']
 path=R/build['library_path'];assert source[str(path.relative_to(R))]==sha(path)==build['library_sha256'],'SVG_BRIDGE_BINARY_CHANGED'
 core=R/'runs/v1655_svg_original_build_flags/libphase_svg_author_cpu.so'
 assert source[str(core.relative_to(R))]==sha(core),'SVG_CORE_BINARY_CHANGED'
 lib=ctypes.CDLL(str(path))
 dp=ctypes.POINTER(ctypes.c_double);ip=ctypes.POINTER(ctypes.c_int);vp=ctypes.c_void_p;integer=ctypes.c_int
 for name in ['phase_svg_abi_version','phase_svg_state_dimension','phase_svg_control_dimension']:
  fn=getattr(lib,name);fn.argtypes=[];fn.restype=integer
 lib.phase_svg_error.argtypes=[ctypes.POINTER(ctypes.c_char),integer];lib.phase_svg_error.restype=integer
 lib.phase_svg_create.argtypes=[dp,integer,ip,integer];lib.phase_svg_create.restype=vp
 lib.phase_svg_set_maps.argtypes=[vp,integer,integer,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,dp,dp,dp];lib.phase_svg_set_maps.restype=integer
 lib.phase_svg_solve.argtypes=[vp,dp,integer,dp,integer,dp];lib.phase_svg_solve.restype=integer
 lib.phase_svg_call_counts.argtypes=[vp,ctypes.POINTER(ctypes.c_ulonglong),integer];lib.phase_svg_call_counts.restype=integer
 lib.phase_svg_destroy.argtypes=[vp];lib.phase_svg_destroy.restype=None
 return lib
