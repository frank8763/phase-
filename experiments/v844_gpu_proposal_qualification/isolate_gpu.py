"""CUDA tensor-only entry derived from the canonical Phase mount isolation."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
OUTPUT = REPO / 'runs/v844_gpu_proposal_qualification'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', choices=['probe_gpu.py', 'prepare_gpu.py', 'qualify_gpu.py'])
    parser.add_argument('--cap', type=int, default=120)
    args = parser.parse_args()
    assert 0 < args.cap <= 900
    OUTPUT.mkdir(parents=True, exist_ok=True)
    lock = (REPO / 'runs/v648_static_unknown/execution.lock').open('rb')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    guard = (REPO / 'REVIEW_PENDING').read_bytes()
    spec = importlib.util.spec_from_file_location('phase_canonical_isolation', REPO / 'tools/isolate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    command = module.command(PACKAGE / args.target, writable=True)
    index = command.index('CUDA_VISIBLE_DEVICES')
    assert command[index + 1] == ''
    command[index + 1] = '0'
    devices = [Path('/dev') / name for name in ['nvidia0', 'nvidiactl', 'nvidia-uvm', 'nvidia-uvm-tools']]
    assert all(path.exists() for path in devices[:3]), 'CUDA_DEVICE_NODES_MISSING'
    added = []
    for path in devices:
        if path.exists():
            added += ['--dev-bind', str(path), str(path)]
    mount = command.index('--chdir')
    command[mount:mount] = added
    environment = dict(os.environ, TORCH_HOME=str(OUTPUT / 'torch_cache'),
                       CUDA_MODULE_LOADING='LAZY', PHASE_GPU_COMPONENT_ONLY='1',
                       PHASE_GPU_COMPONENT_DEADLINE=str(min(time.time() + args.cap, 1794009600.)))
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    record = dict(target=args.target, devices=[str(path) for path in devices if path.exists()],
                  derived_from='tools/isolate.py', original_entry_unchanged=True,
                  no_mujoco_permitted=True, cap_s=args.cap, gpu_processes_queried=False)
    (OUTPUT / ('ISOLATION_' + args.target + '.json')).write_text(json.dumps(record, indent=2) + '\n')
    process = subprocess.Popen(command, cwd=REPO, env=environment, start_new_session=True)
    try:
        return process.wait(timeout=args.cap)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        assert (REPO / 'REVIEW_PENDING').read_bytes() == guard, 'REVIEW_GUARD_CHANGED'


if __name__ == '__main__':
    raise SystemExit(main())
