"""Once-only native qualification, bounded driver restoring the review guard."""
import fcntl
import signal
import subprocess
import time
import traceback

from common import *


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    lock = (ROOT / 'driver.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert read(ROOT / 'PREPARATION.json')['passed']
    unchanged()
    assert not (ROOT / 'native01').exists()
    with (REPO / 'runs/v648_static_unknown/execution.lock').open('rb') as probe:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
    guard = (REPO / 'REVIEW_PENDING').read_bytes()
    (ROOT / 'REVIEW_PENDING.before').write_bytes(guard)
    started = time.time()
    deadline = min(started + 900., 1794009600.)
    assert deadline - started >= 899.
    with (ROOT / 'LAUNCH_CLAIM.json').open('x') as stream:
        json.dump(dict(started_unix=started, absolute_deadline_unix=deadline, pid=os.getpid(), attempts=1), stream)
    environment = dict(os.environ, PHASE_MODEL_ABSOLUTE_DEADLINE=str(deadline),
                       PHASE_PRIVATE_NATIVE_CAP='5376', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                       OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                       PHASE_PROPOSAL_MODEL=str(REPO / 'runs/v690_visible_eight_meter/training_8m/proposer.json'))
    process, result = None, None
    status = 'STARTING'
    try:
        (REPO / 'REVIEW_PENDING').unlink()
        with (ROOT / 'native.console').open('x') as out:
            process = subprocess.Popen([str(REPO / 'run_phase.sh'), str((OWN / 'probe.py').relative_to(REPO))],
                                        cwd=REPO, env=environment, stdout=out, stderr=subprocess.STDOUT,
                                        start_new_session=True)
            save(ROOT / 'ACTIVE.json', dict(pid=process.pid, script='probe.py', model_deadline_unix=deadline))
            code = process.wait(timeout=905)
            assert code == 0, 'NATIVE_COMPONENT_FAILED_NO_RETRY'
        (REPO / 'REVIEW_PENDING').write_bytes(guard)
        with (ROOT / 'audit.console').open('x') as out:
            audit = subprocess.run([sys.executable, '-B', str(OWN / 'audit_saved.py')], cwd=REPO,
                                    env=environment, stdout=out, stderr=subprocess.STDOUT, timeout=300)
        assert audit.returncode == 0, 'NATIVE_SAVED_AUDIT_FAILED'
        result = read(ROOT / 'native01/INDEPENDENT_AUDIT.json')
        status = 'FIXED_GPU_NATIVE_CANDIDATES_QUALIFIED' if result['all_four_states_have_candidate'] else 'STOPPED_FIXED_GPU_NATIVE_CANDIDATES_REJECTED'
    except BaseException as error:
        status = 'STOPPED_EXCEPTION'
        save(ROOT / 'DRIVER_ERROR.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        (REPO / 'REVIEW_PENDING').write_bytes(guard)
        save(ROOT / 'COMPLETION.json', dict(status=status, closed=True, result=result,
                                            deadline_unix=deadline, elapsed_s=time.time()-started,
                                            no_automatic_navigation=True, no_new24=True,
                                            review_guard_exact=True, no_retries=True))
        print(status, flush=True)


if __name__ == '__main__':
    main()
