"""One saved-state diagnostic, preserving the exact review guard."""
from pathlib import Path
import fcntl,json,os,signal,subprocess,sys
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def main():
    assert not O.exists(),'ONE_DIAGNOSTIC_NO_RESTART'
    O.mkdir();guard=(R/'REVIEW_PENDING').read_bytes()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    child=None;rc=1
    try:
        (R/'REVIEW_PENDING').unlink()
        with (O/'CONSOLE.log').open('x') as log:
            child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'qualify.py').relative_to(R))],cwd=R,env=env,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            rc=child.wait(timeout=720)
    finally:
        if child and child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
        (R/'REVIEW_PENDING').write_bytes(guard)
    print(json.dumps(dict(returncode=rc,guard_restored=True)));return rc
if __name__=='__main__':sys.exit(main())
