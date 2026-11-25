"""Lazy metadata and runtime CABI binding; production refuses before DLL load."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def validate_grid(grid,source):
 assert set(grid)=={'source_receipt_sha256','public_map_sha256','width','height','resolution','origin','cells','footprint_xy','inflation_source_sha256'},'RPP_GRID_UNDECLARED_INFORMATION'
 assert grid['source_receipt_sha256']==source['receipt_sha256']and grid['public_map_sha256']==source['public_map_sha256']and grid['inflation_source_sha256']==source['inflation_source_sha256'],'RPP_GRID_SOURCE_BINDING'
 assert type(grid['width'])is int and type(grid['height'])is int and 1<=grid['width']<=512 and 1<=grid['height']<=512 and len(grid['cells'])==grid['width']*grid['height'],'RPP_GRID_SHAPE'
 assert all(type(v)is int and 0<=v<=255 for v in grid['cells']),'RPP_GRID_BYTES'
 return True

def bind(source,*,source_only=False):
 path=R/'runs/v1943_rpp_synchronous_native_api/libphase_rpp_sync.so';assert source[str(path.relative_to(R))]==hashlib.sha256(path.read_bytes()).hexdigest(),'RPP_SYNC_BINARY_CHANGED'
 if not source_only:
  a=R/'runs/v1946_rpp_transitive_tls_dependencies/NUMERICAL_ADMISSION.json';assert a.exists(),'RPP_SYNC_NUMERICAL_ADMISSION_MISSING'
  d=json.loads(a.read_text());assert d.get('controller_calls_authorized')is True and d.get('complete_map_tf_and_current_receipt_qualified')is True,'RPP_SYNC_CURRENT_MAPPING_NOT_QUALIFIED'
 import ctypes
 lib=ctypes.CDLL(str(path));dp=ctypes.POINTER(ctypes.c_double);bp=ctypes.POINTER(ctypes.c_ubyte);integer=ctypes.c_int;vp=ctypes.c_void_p
 lib.phase_rpp_abi_version.argtypes=[];lib.phase_rpp_abi_version.restype=integer
 lib.phase_rpp_request_dimension.argtypes=[];lib.phase_rpp_request_dimension.restype=integer
 lib.phase_rpp_error.argtypes=[ctypes.POINTER(ctypes.c_char),integer];lib.phase_rpp_error.restype=integer
 lib.phase_rpp_create.argtypes=[];lib.phase_rpp_create.restype=vp
 lib.phase_rpp_solve.argtypes=[vp,ctypes.c_longlong,dp,dp,integer,bp,integer,integer,ctypes.c_double,ctypes.c_double,ctypes.c_double,dp,integer,dp];lib.phase_rpp_solve.restype=integer
 lib.phase_rpp_call_count.argtypes=[vp];lib.phase_rpp_call_count.restype=ctypes.c_ulonglong
 lib.phase_rpp_poisoned.argtypes=[vp];lib.phase_rpp_poisoned.restype=integer
 lib.phase_rpp_destroy.argtypes=[vp];lib.phase_rpp_destroy.restype=None
 return lib
