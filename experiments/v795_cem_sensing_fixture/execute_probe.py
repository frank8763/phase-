"""One finite component experiment; original closed windows are never reopened."""
import fcntl, json, os, signal, subprocess, time
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
read = lambda p: json.loads(p.read_text())
assert not (repo/'runs/v795_launch.json').exists()
assert not (repo/'runs/v795_cem_sensing_fixture').exists()
auth = read(repo/'RPCCR_CEM_SENSING_FIXTURE_AUTHORIZATION_20261104.json')
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
guard = repo/'REVIEW_PENDING'; assert guard.exists()
backup = guard.read_bytes()
start = time.time(); deadline = min(start+1200., auth['absolute_deadline_unix'])
assert deadline-start >= 1199., 'INSUFFICIENT_COMPONENT_BUDGET'
(repo/'runs/v795_launch.json').write_text(json.dumps(dict(started_unix=start,
    absolute_deadline_unix=deadline, limit_s=1200, no_retries=True), indent=2)+'\n')
env = dict(os.environ, PHASE_V795_STARTED=str(start), PHASE_V795_DEADLINE=str(deadline),
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
guard.unlink()
try:
    with (repo/'runs/v795_probe.console').open('x') as stream:
        child = subprocess.Popen([str(repo/'run_phase.sh'), str(own/'probe.py')],
            cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = child.wait(timeout=max(1., deadline-time.time())+2.)
        except BaseException:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=1.)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL); child.wait()
            raise
finally:
    guard.write_bytes(backup)
print(json.dumps(dict(child_exit=code, review_guard_restored=guard.exists())))
raise SystemExit(code)
