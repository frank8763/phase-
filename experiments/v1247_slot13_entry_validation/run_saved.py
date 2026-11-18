"""Bounded zero-vehicle run_phase wrapper, restoring original guard bytes."""
from pathlib import Path
import json,time,os,subprocess,signal,fcntl,hashlib,sys
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs'/C.name
def main():
 name=sys.argv[1];assert name in ['qualify_live.py','complete_live_audit.py']
 output=O/(name+'.console');assert not output.exists()
 guard=(R/'REVIEW_PENDING').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
 child=None
 try:
  (R/'REVIEW_PENDING').unlink()
  with output.open('x')as log:
   child=subprocess.Popen([str(R/'run_phase.sh'),str((C/name).relative_to(R)),*sys.argv[2:]],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   rc=child.wait(timeout=900)
 finally:
  if child and child.poll()is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
  (R/'REVIEW_PENDING').write_bytes(guard)
 print(json.dumps(dict(script=name,returncode=rc,guard_restored=True)));sys.exit(rc)
if __name__=='__main__':main()
