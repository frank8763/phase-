"""Independent 300-second CUDA diagnosis; unchanged old isolation and physical source."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;OUT=R/'runs/v847_gpu_reference_diagnosis'
OUT.mkdir(exist_ok=True)
lock=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
freeze=json.loads((C/'FREEZE.json').read_text());assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
guard=(R/'REVIEW_PENDING').read_bytes();started=time.time();deadline=min(started+300.,1794009600.)
assert deadline-started>=299.
with(OUT/'GPU_CLAIM.json').open('x')as f:json.dump(dict(started_unix=started,deadline_unix=deadline,pid=os.getpid(),attempts=1),f)
spec=importlib.util.spec_from_file_location('original_phase_isolation',R/'tools/isolate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
command=module.command(C/'diagnose_gpu.py',writable=True);i=command.index('CUDA_VISIBLE_DEVICES');assert command[i+1]=='';command[i+1]='0';bind=[]
for name in ['nvidia0','nvidiactl','nvidia-uvm','nvidia-uvm-tools']:
 p=Path('/dev')/name
 if p.exists():bind+=['--dev-bind',str(p),str(p)]
i=command.index('--chdir');command[i:i]=bind
env=dict(os.environ,PHASE_GPU_BACKEND_DEADLINE=str(deadline),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});p=subprocess.Popen(command,cwd=R,env=env,start_new_session=True);code=None
try:code=p.wait(timeout=300)
finally:
 if p.poll()is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=2)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 assert(R/'REVIEW_PENDING').read_bytes()==guard
 (OUT/'GPU_OUTER_COMPLETION.json').write_text(json.dumps(dict(closed=True,child_exit=code,guard_exact=True,no_training=True,closed_unix=time.time()),indent=2)+'\n')
sys.exit(code if code is not None else 2)
