#!/usr/bin/env python3
"""Keep historical frozen source unchanged inside a Phase-only Linux mount namespace."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
LEGACY_HOME = Path('/home/linghu')
LEGACY_ROOT = LEGACY_HOME / 'catkin_ws/src/mk-mini'


def command(script, writable=False):
    if shutil.which('bwrap') is None:
        raise RuntimeError('bubblewrap is required; refusing an unisolated fallback')
    conda = Path(os.environ.get('PHASE_CONDA_ROOT', '/home/linghu/miniconda3')).resolve()
    python = conda / 'envs/mk_mujoco/bin/python'
    if not python.is_file():
        raise RuntimeError('Set PHASE_CONDA_ROOT to an existing miniconda tree containing mk_mujoco')
    args = ['bwrap', '--die-with-parent', '--new-session', '--unshare-all',
            '--ro-bind', '/', '/', '--tmpfs', '/home', '--tmpfs', '/tmp',
            '--proc', '/proc', '--dev', '/dev',
            '--ro-bind', str(conda), str(LEGACY_HOME / 'miniconda3'),
            '--ro-bind', str(REPO), str(REPO),
            '--ro-bind', str(REPO / 'runtime/mk-mini'), str(LEGACY_ROOT),
            '--ro-bind', str(REPO / 'runtime/home/mkmini_g11b_budget162_confirmatory_v1_1'),
            str(LEGACY_HOME / 'mkmini_g11b_budget162_confirmatory_v1_1')]
    if writable:
        args += ['--bind', str(REPO / 'runs'), str(REPO / 'runs')]
    args += ['--chdir', str(LEGACY_ROOT),
             '--setenv', 'HOME', str(LEGACY_HOME),
             '--setenv', 'PYTHONPATH', str(LEGACY_ROOT),
             '--setenv', 'PYTHONDONTWRITEBYTECODE', '1',
             '--setenv', 'MPLCONFIGDIR', '/tmp/matplotlib',
             '--setenv', 'MUJOCO_GL', 'egl',
             '--setenv', 'CUDA_VISIBLE_DEVICES', '',
             '--setenv', 'OMP_NUM_THREADS', '1',
             '--setenv', 'OPENBLAS_NUM_THREADS', '1',
             '--setenv', 'MKL_NUM_THREADS', '1',
             '--setenv', 'PHASE_REPO', str(REPO),
             '--setenv', 'PHASE_RUNS', str(REPO / 'runs'),
             str(LEGACY_HOME / 'miniconda3/envs/mk_mujoco/bin/python'), '-B', str(script)]
    return args


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--run', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.probe:
        return subprocess.run(command(REPO / 'tools/import_probe.py'), check=False).returncode
    if (REPO / 'REVIEW_PENDING').exists():
        raise RuntimeError('PAUSED_PENDING_USER_REVIEW')
    if not args.run:
        parser.error('--run requires an experiments/ script')
    target = (REPO / args.run[0]).resolve()
    if not target.is_relative_to(REPO / 'experiments') or not target.is_file():
        raise ValueError('Only a real script inside experiments/ may be executed')
    return subprocess.run(command(target, writable=True) + args.run[1:], check=False).returncode


if __name__ == '__main__':
    sys.exit(main())

