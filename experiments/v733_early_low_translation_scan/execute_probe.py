"""Guard restoration and single absolute finite launch, no automatic retries."""
import datetime,fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
assert not (repo/'runs/v733_early_low_translation_scan').exists()
with (repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=repo/'REVIEW_PENDING';assert guard.exists();backup=repo/'runs/v733_review_guard.before';backup.write_bytes(guard.read_bytes())
started=time.time();deadline=started+600;environment={**os.environ,'PHASE_V733_STARTED':str(started),'PHASE_V733_DEADLINE':str(deadline),'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
launch=dict(started_unix=started,absolute_deadline_unix=deadline,deadline_local=datetime.datetime.fromtimestamp(deadline).astimezone().isoformat(),maximum_wall_s=600,pid=os.getpid(),retry_allowed=False)
(repo/'runs/v733_launch.json').write_text(json.dumps(launch,indent=2)+'\n');guard.unlink()
try:
 with (repo/'runs/v733_probe.console').open('x')as stream:
  p=subprocess.Popen([str(repo/'run_phase.sh'),str(own/'probe.py')],cwd=repo,env=environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=max(1,deadline-time.time())+2)
  except BaseException:
   if p.poll()is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=1)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise
finally:guard.write_bytes(backup.read_bytes())
print(json.dumps(dict(child_exit=code,review_guard_restored=guard.exists(),no_automatic_retry=True)));raise SystemExit(code)
