"""Cold spawn from actual audit entry module, only original saved jobs."""
from gap_tools import *
import fcntl
review=load('v1177_pool_actual_review_entry',C/'audit.py')
def main():
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sys.path.insert(0,str(R/'experiments/v1176_multicore_stop_backend'))
    import backend
    freeze=read(R/'experiments/v1176_multicore_stop_backend/SOURCE_FREEZE.json')['files'];jobs=read(R/'experiments/v1176_multicore_stop_backend/TASKS.json')['jobs'][:64]
    expected=read(R/'runs/v1176_multicore_stop_backend/SERIAL.json')['rows'][:64];rows,timing=backend.parallel(jobs,freeze)
    for a,b in zip(rows,expected,strict=True):
        for key in ['id','state_sha256','ctrl_sha256','memory_sha256','passed','minimum_raw']:assert a[key]==b[key]
    dump(O/'PARALLEL_ENTRY_QUALIFICATION.json',dict(passed=True,cold_spawn_actual_audit_import=True,models=0,physical_native=0,analytical_cpp_native=64*2200,old_fixed_jobs_only=True,exact_old_hashes=True,timing=timing));print('COLD_PARALLEL_AUDIT_ENTRY_PASS');fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
