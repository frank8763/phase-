"""Same full scientific audit, with the original 1e-8 t0 pose contract."""
import sys, types
from pathlib import Path

R = Path(__file__).resolve().parents[2]
ORIGINAL = R / 'experiments/rpccr_execution_core/fresh_audit.py'
OLD = "p['body'][:3]==task['start_xy']+[task['start_yaw']]"
NEW = "np.max(np.abs(np.asarray(p['body'][:3])-np.asarray(task['start_xy']+[task['start_yaw']])))<=1e-8"

def patched_source():
    source = ORIGINAL.read_text()
    assert source.count(OLD) == 1
    patched = source.replace(OLD, NEW)
    assert patched.replace(NEW, OLD) == source
    return patched

def load_audit():
    module = types.ModuleType('v1086_tolerant_initial_pose_audit')
    module.__file__ = str(ORIGINAL)
    exec(compile(patched_source(), str(ORIGINAL), 'exec'), module.__dict__)
    return module

if __name__ == '__main__':
    exec(compile(patched_source(), str(ORIGINAL), 'exec'),
         dict(__name__='__main__', __file__=str(ORIGINAL)))
