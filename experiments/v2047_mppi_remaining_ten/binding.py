"""Lazy metadata and runtime CABI binding; production refuses before DLL load."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def validate_grid(grid,source):
 assert set(grid)=={'source_receipt_sha256','public_map_sha256','width','height','resolution','origin','cells','footprint_xy','inflation_source_sha256'},'MPPI_GRID_UNDECLARED_INFORMATION'
 assert grid['source_receipt_sha256']==source['receipt_sha256']and grid['public_map_sha256']==source['public_map_sha256']and grid['inflation_source_sha256']==source['inflation_source_sha256'],'MPPI_GRID_SOURCE_BINDING'
 assert type(grid['width'])is int and type(grid['height'])is int and 1<=grid['width']<=512 and 1<=grid['height']<=512 and len(grid['cells'])==grid['width']*grid['height'],'MPPI_GRID_SHAPE'
 assert all(type(v)is int and 0<=v<=255 for v in grid['cells']),'MPPI_GRID_BYTES'
 return True

def bind(source,*,source_only=False):
 path=R/'runs/v1998_mppi_map_bootstrap_preparation/libphase_mppi_map_bootstrap.so';assert source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'MPPI_SYNC_BINARY_CHANGED'
 assert source_only is False,'MPPI_COMPONENT_NO_SOURCE_ONLY_BYPASS'
 from context import SOURCE,O,read,sha,remaining
 a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');assert a['scope']=='MPPI_CURRENT_COMMON_FULL_TASK'and a['models_authorized']and a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and remaining(w)>30,'MPPI_SCOPE_OR_CLOCK'
 import ctypes
 lib=ctypes.CDLL(str(path));dp=ctypes.POINTER(ctypes.c_double);bp=ctypes.POINTER(ctypes.c_ubyte);integer=ctypes.c_int;vp=ctypes.c_void_p
 lib.phase_mppi_abi_version.argtypes=[];lib.phase_mppi_abi_version.restype=integer
 lib.phase_mppi_request_dimension.argtypes=[];lib.phase_mppi_request_dimension.restype=integer
 lib.phase_mppi_error.argtypes=[ctypes.POINTER(ctypes.c_char),integer];lib.phase_mppi_error.restype=integer
 lib.phase_mppi_create.argtypes=[];lib.phase_mppi_create.restype=vp
 lib.phase_mppi_solve.argtypes=[vp,ctypes.c_longlong,dp,dp,integer,bp,integer,integer,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,integer,dp];lib.phase_mppi_solve.restype=integer
 lib.phase_mppi_call_count.argtypes=[vp];lib.phase_mppi_call_count.restype=ctypes.c_ulonglong
 lib.phase_mppi_poisoned.argtypes=[vp];lib.phase_mppi_poisoned.restype=integer
 lib.phase_mppi_destroy.argtypes=[vp];lib.phase_mppi_destroy.restype=None
 return lib
