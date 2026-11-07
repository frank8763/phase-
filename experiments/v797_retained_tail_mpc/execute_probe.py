"""One finite component experiment; original closed windows are never reopened."""
import fcntl, json, os, signal, subprocess, time
from pathlib import Path
repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
read = lambda p: json.loads(p.read_text())
assert not (repo/'runs/v797_launch.json').exists()
assert not (repo/'runs/v797_retained_tail_mpc').exists()
auth = read(repo/'RPCCR_RETAINED_MPC_AUTHORIZATION_20261104.json')
assert read(repo/'runs/v795_cem_sensing_fixture/FINALIZED.json')['component_qualified']
assert read(repo/'runs/v797_preparation/QUALIFICATION.json')['status']=='SAVED_RETAINED_MPC_INTERFACE_QUALIFIED'
with (repo/'runs/v648_static_unknown/execution.lock').open('a+') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
guard = repo/'REVIEW_PENDING'; assert guard.exists()
backup = guard.read_bytes()
(repo/'runs/v797_review_guard.before').write_bytes(backup)
start = time.time(); deadline = min(start+1800., auth['absolute_deadline_unix'])
assert deadline-start >= 1799., 'INSUFFICIENT_COMPONENT_BUDGET'
(repo/'runs/v797_launch.json').write_text(json.dumps(dict(started_unix=start,
    absolute_deadline_unix=deadline, limit_s=1800, no_retries=True), indent=2)+'\n')
env = dict(os.environ, PHASE_V797_STARTED=str(start), PHASE_V797_DEADLINE=str(deadline),
           OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('OUTER_TERMINATED')))
guard.unlink()
try:
    with (repo/'runs/v797_probe.console').open('x') as stream:
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
