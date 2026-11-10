"""Bounded failure closure without prematurely killing the native wrapper.

This parent module has no model/ROS imports. It never launches or retries work.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time


def dump(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def request_stop(out, run_id, reason, socket_dir=None):
    request = dict(run_id=run_id, reason=reason, requested_monotonic=time.monotonic())
    dump(Path(out)/'PARENT_STOP_REQUEST.json', request)
    # Immediate existing protocol STOP; the durable file also covers a lost datagram.
    if socket_dir is not None:
        packet = dict(kind='stop', run_id=run_id, issued_at=time.monotonic(), reason=reason)
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.settimeout(.01)
            try:
                sock.sendto(json.dumps(packet).encode(), str(Path(socket_dir)/'physics.sock'))
            except (FileNotFoundError, ConnectionRefusedError, BlockingIOError, socket.timeout):
                pass


def stop_requested(out, run_id):
    path = Path(out)/'PARENT_STOP_REQUEST.json'
    if not path.exists():
        return None
    request = json.loads(path.read_text())
    assert request['run_id'] == run_id, 'FOREIGN_PARENT_STOP_REQUEST'
    assert isinstance(request['reason'], str), 'MALFORMED_PARENT_STOP_REQUEST'
    return request


def terminate_group(child, hard_until):
    if child.poll() is not None:
        return False
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    try:
        child.wait(timeout=max(0., min(1., hard_until-time.monotonic()-.05)))
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=1.)
    return True


def supervise_workers(jobs, out, run_id, task_until, root_deadline_unix,
                      socket_dir=None, closure_grace_s=40., initial_failure=None):
    assert 0 < closure_grace_s <= 40., 'CLOSURE_GRACE_CHANGED'
    assert jobs and all(p.pid != os.getpid() for p in jobs)
    # Convert the already fixed root cutoff once; wall-clock adjustments cannot
    # extend this parent's kill deadline. Native also retains its absolute alarm.
    hard_until = min(task_until, time.monotonic()+max(0., root_deadline_unix-time.time())-1.)
    failure = initial_failure
    close_until = hard_until
    forced = []
    if failure is not None:
        dump(Path(out)/'WORKER_FAILURE.json', failure)
        request_stop(out, run_id, failure['reason'], socket_dir)
        close_until = min(hard_until, time.monotonic()+closure_grace_s)
    try:
        while any(p.poll() is None for p in jobs):
            failed = [dict(pid=p.pid, returncode=p.returncode) for p in jobs if p.poll() is not None and p.returncode != 0]
            now = time.monotonic()
            reason = 'FIRST_WORKER_FAILURE' if failed else ('TASK_OR_ROOT_DEADLINE' if now >= hard_until else None)
            if reason is not None and failure is None:
                failure = dict(reason=reason, failed=failed, detected_monotonic=now)
                dump(Path(out)/'WORKER_FAILURE.json', failure)
                request_stop(out, run_id, reason, socket_dir)
                close_until = min(hard_until, now+closure_grace_s)
            if now >= close_until:
                break
            time.sleep(.01)
    except BaseException as error:
        failure = dict(reason='PARENT_EXCEPTION', error=repr(error))
        dump(Path(out)/'WORKER_FAILURE.json', failure)
        request_stop(out, run_id, 'PARENT_EXCEPTION', socket_dir)
        close_until = min(hard_until, time.monotonic()+closure_grace_s)
        # A handled parent interruption still permits bounded STOP/save before
        # wrapper escalation. It never turns failure into successful navigation.
        while any(p.poll() is None for p in jobs) and time.monotonic() < close_until:
            time.sleep(.01)
    finally:
        for p in reversed(jobs):
            if terminate_group(p, hard_until):
                forced.append(p.pid)
    # A nonzero exit observed in the final polling interval still fails the batch.
    if failure is None and any(p.returncode != 0 for p in jobs):
        failure = dict(reason='WORKER_NONZERO', failed=[dict(pid=p.pid, returncode=p.returncode) for p in jobs if p.returncode != 0])
        dump(Path(out)/'WORKER_FAILURE.json', failure)
    answer = dict(passed=failure is None and all(p.returncode == 0 for p in jobs),
                  failure=failure, forced_process_groups=forced,
                  hard_stop_monotonic=hard_until, closed_monotonic=time.monotonic(),
                  navigation_restart=False, root_deadline_unchanged=True)
    dump(Path(out)/'WORKER_CLOSURE.json', answer)
    return answer


def accounting_receipt(vehicle, timing, task, result, status):
    origin = task.get('origin_native_tick', 0)
    total = None if vehicle is None else vehicle.count
    uncertain = bool(getattr(timing, 'native_integration_uncertain', False))
    completed = getattr(timing, 'native_completed', None)
    mismatch = vehicle is not None and completed is not None and completed != vehicle.count-origin
    if uncertain or mismatch:
        total = None
    return dict(status=status, final=False, environment_initialization_attempted=result.get('environment_initialization_attempted', False),
                environment_initialization_completed=result.get('environment_initialization_completed', False),
                historical_restore_native=origin if result.get('environment_initialization_completed') else None,
                actual_native_exact=total,
                native_calls_completed=completed,
                new_branch_native_exact=None if total is None else max(0, total-origin),
                new_branch_native_observed_lower_bound=0 if vehicle is None else max(0, vehicle.count-origin, completed or 0),
                count_status='UNKNOWN_INTERRUPTED_NATIVE_CALL' if uncertain else ('RETURN_AND_RECORDED_COUNT_MISMATCH' if mismatch else ('COMPLETED_RETURN_COUNT' if total is not None else 'INITIALIZATION_NOT_COMPLETED_TOTAL_UNKNOWN')),
                own_full_trace_replay_native_exact=None,
                replay_status='NOT_STARTED_AT_ACCOUNTING_CHECKPOINT',
                full_safety_verdict=False, navigation_passed=False)
