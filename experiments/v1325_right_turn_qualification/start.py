"""One-shot user-authorized bounded launch after true zero-model entry qualification."""
import fcntl
import os
import subprocess
import sys
from component_context import *


def main():
    assert sources(), 'SOURCE_CHANGED'
    assert read(O/'software/COMPLETION.json')['passed'], 'SOFTWARE_QUALIFICATION_REQUIRED'
    assert read(O/'GEOMETRY_QUALIFICATION.json')['passed'], 'GEOMETRY_QUALIFICATION_REQUIRED'
    assert not (O / 'LAUNCH.json').exists() and not (O / 'ROUND_WINDOW.json').exists(), 'ALREADY_ATTEMPTED'
    assert read(O / 'OUTPUT_SCOPE_QUALIFICATION.json')['passed'], 'ACTUAL_WRITE_GUARD_QUALIFICATION_REQUIRED'
    lock = (R / 'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(lock, fcntl.LOCK_UN)
    O.mkdir(exist_ok=True); guard = (R / 'REVIEW_PENDING').read_bytes(); (O / 'REVIEW_PENDING.before').write_bytes(guard)
    now, mono = time.time(), time.monotonic()
    window = dict(started_unix=now, absolute_deadline_unix=now + 5400, started_monotonic=mono, hard_stop_monotonic=mono + 5400, boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O / 'ROUND_WINDOW.json', window)
    dump(O / 'APPROVAL.json', dict(models_authorized=True, allowed_task_ids=[t['task_id'] for t in read(C / 'TASKS.json')],
                                   absolute_deadline_unix=window['absolute_deadline_unix'],
                                   user_authority='2026-11-18: 下一步继续推进；然后顺便回答我，我们论文后续的步骤; prior agreed next gate turning and braking', window_seconds=5400,
                                   whole_route_or_new24_authorized=False))
    env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='')
    python = '/home/linghu/miniconda3/envs/mk_mujoco/bin/python'
    from campaign import native_environment
    env.update(native_environment())
    isolation_path = R / 'tools/isolate.py'
    import importlib.util
    spec = importlib.util.spec_from_file_location('v1292_isolated_backend', isolation_path)
    isolation = importlib.util.module_from_spec(spec); spec.loader.exec_module(isolation)
    backend = subprocess.run(isolation.command(C / 'backend_check.py', writable=True), cwd=R, env=env, capture_output=True, text=True, timeout=30)
    (O / 'backend.console').write_text(backend.stdout + backend.stderr)
    assert backend.returncode == 0, 'REAL_CPU_CONTEXT_CHECK_FAILED'
    dump(O / 'BACKEND_QUALIFICATION.json', json.loads(backend.stdout.strip().splitlines()[-1]))
    p = subprocess.run([python, '-B', str(C / 'native_component.py'), str(C / 'TASKS_entry.json'), '--entry-check'],
                       cwd=R, env=env, capture_output=True, text=True, timeout=60)
    (O / 'entry.console').write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        dump(O / 'COMPLETION.json', dict(closed=True, passed=False, stop_reason='ZERO_MODEL_ENTRY_REJECTED',
                                         canonical_vehicle_initializations=0, new_actual_native=0, entry_returncode=p.returncode))
        print(p.stdout[-1000:] + p.stderr[-1500:]); return 1
    proof = json.loads(p.stdout.strip().splitlines()[-1]); assert proof['passed'] and proof['models'] == 0
    dump(O / 'ENTRY_QUALIFICATION.json', proof)
    pointer = read(R / 'CURRENT_EXPERIMENT.json'); pointer.update(status='RUNNING_BOUNDED_COMPONENT', active_run=str(O.relative_to(R)), active_window=window, active_entrypoint=str((C / 'campaign.py').relative_to(R)), next_physical_authorized=True); dump(R / 'CURRENT_EXPERIMENT.json', pointer)
    log = (O / 'campaign.console').open('x')
    job = subprocess.Popen([python, '-B', str(C / 'campaign.py')], cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    dump(O / 'LAUNCH.json', dict(pid=job.pid, launched_once=True, deadline_unix=window['absolute_deadline_unix'])); log.close()
    print(json.dumps(dict(started=True, pid=job.pid, scope='Coherent MPPI right arc at registered EAST_WEST start, main and conditional repeat', absolute_deadline_unix=window['absolute_deadline_unix'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
