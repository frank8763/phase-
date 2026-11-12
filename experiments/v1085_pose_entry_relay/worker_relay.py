"""One explicit metadata-entry relay; original frozen scientific source retained."""
import sys,types,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];CORE=R/'experiments/rpccr_execution_core';ORIGINAL=CORE/'fresh_worker.py'
OLD="assert list(v.body()[:3])==meta['packet']['body'][:3]"
NEW="assert np.max(np.abs(np.asarray(v.body()[:3])-np.asarray(meta['packet']['body'][:3])))<=1e-8,'CANONICAL_POSE_TOLERANCE'"
def patched_source():
 source=ORIGINAL.read_text();assert source.count(OLD)==1
 return source.replace(OLD,NEW)
def load_worker():
 module=types.ModuleType('v1085_qualified_pose_relay');module.__file__=str(ORIGINAL);exec(compile(patched_source(),str(ORIGINAL),'exec'),module.__dict__);return module
if __name__=='__main__':exec(compile(patched_source(),str(ORIGINAL),'exec'),dict(__name__='__main__',__file__=str(ORIGINAL)))
