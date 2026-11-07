"""Bounded CUDA physics qualification in the original Phase mount isolation."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
OWN = Path(__file__).resolve().parent
ROOT = REPO / 'runs/v846_parallel_backend_qualification'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    lock = (REPO / 'runs/v648_static_unknown/execution.lock').open('rb')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    guard = (REPO / 'REVIEW_PENDING').read_bytes()
    target = OWN / ('prepare.py' if args.prepare else 'benchmark.py')
    cap = 120 if args.prepare else 900
    started = time.time()
    deadline = min(started + cap, 1794009600.)
    assert deadline - started >= cap - 1
    if not args.prepare:
        freeze = json.loads((OWN / 'FREEZE.json').read_text())
        assert all(hashlib.sha256((REPO / p).read_bytes()).hexdigest() == h for p, h in freeze['files'].items())
        with (ROOT / 'LAUNCH_CLAIM.json').open('x') as out:
            json.dump(dict(pid=os.getpid(), started_unix=started, absolute_deadline_unix=deadline,
                           attempts=1, training=0, old_windows_unchanged=True), out)
    spec = importlib.util.spec_from_file_location('canonical_phase_isolation', REPO / 'tools/isolate.py')
    isolate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(isolate)
    command = isolate.command(target, writable=True)
    index = command.index('CUDA_VISIBLE_DEVICES')
    assert command[index+1] == ''
    command[index+1] = '0'
    binds = []
    for name in ['nvidia0', 'nvidiactl', 'nvidia-uvm', 'nvidia-uvm-tools']:
        p = Path('/dev') / name
        if p.exists():
            binds += ['--dev-bind', str(p), str(p)]
    index = command.index('--chdir')
    command[index:index] = binds
    environment = dict(os.environ, PHASE_GPU_BACKEND_DEADLINE=str(deadline),
                       WARP_CACHE_PATH=str(ROOT / 'warp_cache'), OMP_NUM_THREADS='1',
                       OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                       PHASE_GPU_BACKEND_COMPONENT='1', PYTHONDONTWRITEBYTECODE='1')
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    process = subprocess.Popen(command, cwd=REPO, env=environment, start_new_session=True)
    code = None
    try:
        code = process.wait(timeout=cap)
        return code
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        assert (REPO / 'REVIEW_PENDING').read_bytes() == guard
        if not args.prepare:
            (ROOT / 'OUTER_COMPLETION.json').write_text(json.dumps(dict(closed=True, child_exit=code,
                       guard_exact=True, closed_unix=time.time(), no_training_started=True), indent=2)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
