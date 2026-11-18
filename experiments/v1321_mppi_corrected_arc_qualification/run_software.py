"""Bounded one-shot software campaign. Does not remove the physical review hold."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name


def dump(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def hashes_ok():
    return all(hashlib.sha256((R / p).read_bytes()).hexdigest() == h
               for p, h in json.loads((C / 'SOURCE_FREEZE.json').read_text())['files'].items())


def main():
    O.parent.mkdir(exist_ok=True)
    O.parent.mkdir(exist_ok=True)
    O.mkdir(exist_ok=False)
    guard = (R / 'REVIEW_PENDING').read_bytes()
    begin = time.monotonic()
    until = begin + 600
    job = None
    result = dict(passed=False, scope='baseline_interface_software_only', models=0,
                  physical_native=0, analytical_vehicle_native=0, training_updates=0,
                  started_unix=time.time(), automatic_physical_continuation=False)
    try:
        os.sched_setaffinity(0, {2, 3, 4, 5})
        os.nice(max(0, 19 - os.getpriority(os.PRIO_PROCESS, 0)))
        for p in C.glob('*.py'):
            ast.parse(p.read_text(), filename=str(p))
        assert hashes_ok(), 'SOURCE_OR_INSTALLED_BINARY_CHANGED'
        from qualify_contract import run
        checks = run()
        dump(O / 'CONTRACT_QUALIFICATION.json', checks)
        assert checks['passed'], 'COMMON_CONTRACT_FAILED'
        envpath = R / 'experiments/v856_nav2_foundation/ros_environment.py'
        spec = importlib.util.spec_from_file_location('v1288_ros_namespace', envpath)
        envmod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(envmod)
        env = envmod.environment()
        env['AMENT_PREFIX_PATH'] = str(R/'runs/v931_deadband_consistent_mppi/install')+':'+env['AMENT_PREFIX_PATH']
        env['LD_LIBRARY_PATH'] = str(R/'runs/v931_deadband_consistent_mppi/install/lib')+':'+env['LD_LIBRARY_PATH']
        env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'), PHASE_COHERENT_NOISE='1', ROS_DOMAIN_ID='188', ROS_LOG_DIR=str(O / 'ros_logs'), CUDA_VISIBLE_DEVICES='')
        cmd = envmod.command(['/usr/bin/python3.12', '-B', str(C / 'controller_probe.py')])
        dump(O / 'RUN_CONTEXT.json', dict(command=cmd, cpus=[2, 3, 4, 5], gpu_used=False,
                                         software_limit_s=600, physical_review_hold_preserved=True))
        with (O / 'software.console').open('x') as log:
            job = subprocess.Popen(cmd, cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            dump(O / 'ACTIVE.json', dict(pid=job.pid, physical=False, software=True))
            while job.poll() is None:
                assert time.monotonic() < until, 'SOFTWARE_DEADLINE'
                assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file()) < 128 * 1024**2, 'SOFTWARE_STORAGE_LIMIT'
                time.sleep(.2)
        result['worker_returncode'] = job.returncode
        proof = json.loads((O / 'CONTROLLER_RESULT.json').read_text())
        from contract import observation, twist
        observations = json.loads((O / 'SYNTHETIC_OBSERVATIONS.json').read_text())
        for i, packet in enumerate(observations):
            observation(packet, run_id='v1288-stationary-software', now=packet['sampled_at'], previous_sequence=i - 1)
            assert packet['sequence'] == i and packet['body'] in [x['body'] for x in json.loads((C/'ALL_SAVED_INPUTS.json').read_text()).values()], 'SYNTHETIC_POSE_CHANGED'
        raw = json.loads((O / 'RAW_COMMANDS.json').read_text())
        expected = json.loads((C / 'TASKS.json').read_text())
        independent = []
        for case in expected:
            rows = [x for x in raw if x['label'] == case['id']]
            bad = []
            for row in rows:
                try:
                    twist(row['v'], row['w'])
                except ValueError as exc:
                    bad.append(dict(error=str(exc), raw=row))
            independent.append(dict(id=case['id'], recorded_commands=len(rows), illegal_commands=bad,
                                    independently_legal=not bad))
        dump(O / 'INDEPENDENT_COMMAND_AUDIT.json', independent)
        result.update(passed=job.returncode == 0 and proof['passed'] and hashes_ok(), controller=proof,
                      contract_checks=len(checks['checks']), source_unchanged=hashes_ok(),
                      independently_revalidated_observations=len(observations),
                      physical_successes=None, physical_trials=0)
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll() is None:
            os.killpg(job.pid, signal.SIGTERM)
            try:
                job.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(job.pid, signal.SIGKILL)
                job.wait(timeout=2)
        result.update(closed=True, wall_s=time.monotonic() - begin, closed_unix=time.time(),
                      review_pending_unchanged=(R / 'REVIEW_PENDING').read_bytes() == guard)
        dump(O / 'COMPLETION.json', result)
        active = O / 'ACTIVE.json'
        if active.exists():
            active.rename(O / 'CLOSED_PROCESS.json')
    print(json.dumps(dict(passed=result['passed'], closed=True, error=result.get('error'),
                         cases=len(result.get('controller', {}).get('cases', [])), models=0, physical_native=0)))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
