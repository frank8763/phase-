"""One bounded fixed qualification; no algorithm/source retries."""
import fcntl
import json
import os
import signal
import subprocess
import time
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
assert not (repo / 'runs/v792_launch.json').exists()
assert not (repo / 'runs/v792_complete_joint_qualification').exists()
authorization = json.loads((repo / 'RPCCR_GLOBAL_METHOD_REVIEW_AUTHORIZATION_20261104.json').read_text())
with (repo / 'runs/v648_static_unknown/execution.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
guard = repo / 'REVIEW_PENDING'
assert guard.exists()
backup = repo / 'runs/v792_review_guard.before'
backup.write_bytes(guard.read_bytes())
start = time.time()
deadline = start + 600
assert deadline + 5 < authorization['absolute_deadline_unix'], 'INSUFFICIENT_NEW_ROUND_BUDGET'
env = dict(os.environ, PHASE_V792_STARTED=str(start), PHASE_V792_DEADLINE=str(deadline),
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
(repo / 'runs/v792_launch.json').write_text(json.dumps(dict(
    started_unix=start, absolute_deadline_unix=deadline, limit_s=600,
    overall_absolute_deadline_unix=authorization['absolute_deadline_unix'], pid=os.getpid(),
    no_retries=True), indent=2) + '\n')
guard.unlink()
try:
    with (repo / 'runs/v792_probe.console').open('x') as stream:
        p = subprocess.Popen([str(repo / 'run_phase.sh'), str(own / 'probe.py')], cwd=repo,
                             env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = p.wait(timeout=max(1, deadline - time.time()) + 2)
        except BaseException:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    p.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()
            raise
finally:
    guard.write_bytes(backup.read_bytes())
print(json.dumps(dict(child_exit=code, review_guard_restored=guard.exists(), no_retry=True)))
raise SystemExit(code)
