"""Read-only bounded historical trace cache for FUTURE frozen entries.

Not injected into V1039's running process. Every original comparison remains.
No model creation, no physical integration, no mutation of original artifacts.
"""
import hashlib
from pathlib import Path
import numpy as np
KEYS=('qpos','qvel','ctrl','mocap_pos','mocap_quat')
def load_trace(path,expected_sha256,max_bytes=64*1024**2):
 path=Path(path);assert path.is_file()and not path.is_symlink(),'INVALID_TRACE_PATH'
 digest=hashlib.sha256()
 with path.open('rb')as stream:
  for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
 assert digest.hexdigest()==expected_sha256,'HISTORICAL_TRACE_SHA_CHANGED'
 out={};total=0;length=None
 with np.load(path,allow_pickle=False)as compressed:
  for key in KEYS:
   value=compressed[key];total+=value.nbytes;assert total<=max_bytes,'HISTORICAL_TRACE_CACHE_CAP'
   assert np.issubdtype(value.dtype,np.number)and np.isfinite(value).all(),'INVALID_HISTORICAL_ARRAY'
   assert length is None or len(value)==length,'HISTORICAL_ARRAY_LENGTH_MISMATCH'
   length=len(value);value.setflags(write=False);out[key]=value
 return out
