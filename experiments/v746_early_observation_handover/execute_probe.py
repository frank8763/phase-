"""One finite diagnostic launch; old windows remain closed."""
import datetime,fcntl,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
assert not(repo/'runs/v746_early_observation_handover').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=repo/'REVIEW_PENDING';assert guard.exists()
backup=repo/'runs/v746_review_guard.before';backup.write_bytes(guard.read_bytes())
start=time.time();deadline=start+900
env={**os.environ,'PHASE_V746_STARTED':str(start),'PHASE_V746_DEADLINE':str(deadline),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
(repo/'runs/v746_launch.json').write_text(json.dumps(dict(started_unix=start,absolute_deadline_unix=deadline,deadline_local=datetime.datetime.fromtimestamp(deadline).astimezone().isoformat(),limit_s=900,pid=os.getpid(),no_retries=True),indent=2)+'\n')
guard.unlink()
try:
 with(repo/'runs/v746_probe.console').open('x')as log:
  p=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=max(1,deadline-time.time())+2)
  except BaseException:
   if p.poll()is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=1)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise
finally:guard.write_bytes(backup.read_bytes())
print(json.dumps(dict(child_exit=code,review_guard_restored=guard.exists(),no_retry=True)));raise SystemExit(code)
