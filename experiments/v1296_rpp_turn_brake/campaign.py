"""Finite original-main/conditional-repeat owner, exact hold restoration."""
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import time
import traceback
from component_context import *

def native_environment():
    env = dict(os.environ)
    lib = R / 'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH'] = str(lib) + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.update(CUDA_VISIBLE_DEVICES='', MUJOCO_GL='osmesa', PYOPENGL_PLATFORM='osmesa', LIBGL_ALWAYS_SOFTWARE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env



def stop(job):
    if job.poll() is None:
        os.killpg(job.pid, signal.SIGTERM)
        try:
            job.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(job.pid, signal.SIGKILL); job.wait(timeout=2)


def main():
    window = read(O / 'ROUND_WINDOW.json'); guard = (O / 'REVIEW_PENDING.before').read_bytes(); results = []; jobs = []
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('CAMPAIGN_STOP')))
    result = dict(passed=False, scope='current_adapter_rpp_left_right_turn_brake', results=results, unexecuted=[t['task_id'] for t in read(C / 'TASKS.json')])
    try:
        for task in read(C / 'TASKS.json'):
            authorize(task, window); out = Path(task['output']); out.mkdir(parents=True, exist_ok=False); dump(out / 'TASK.json', task)
            (R / 'REVIEW_PENDING').unlink()
            try:
                envpath = R / 'experiments/v856_nav2_foundation/ros_environment.py'; spec = importlib.util.spec_from_file_location('v1290_ros_namespace', envpath); envmod = importlib.util.module_from_spec(spec); spec.loader.exec_module(envmod)
                env = envmod.environment(); env.update(ROS_DOMAIN_ID='190', ROS_LOG_DIR=str(out / 'ros_logs'), CUDA_VISIBLE_DEVICES='')
                arguments = [str(out / 'TASK.json')]
                definitions = [('ros', envmod.command(['/usr/bin/python3.12', '-B', str(C / 'ros_component.py'), *arguments]), env),
                               ('native', [str(R / 'run_phase.sh'), str((C / 'native_component.py').relative_to(R)), *arguments], native_environment())]
                files = []
                for name, cmd, environment in definitions:
                    log = (out / (name + '.console')).open('x'); files.append(log)
                    jobs.append(subprocess.Popen(cmd, cwd=R, env=environment, stdout=log, stderr=subprocess.STDOUT, start_new_session=True))
                dump(O / 'ACTIVE.json', dict(task=task['task_id'], pids=[p.pid for p in jobs]))
                until = min(time.monotonic() + 340, window['hard_stop_monotonic'] - 5)
                while any(p.poll() is None for p in jobs):
                    if any(p.poll() not in (None, 0) for p in jobs):
                        for child in jobs:
                            if child.poll() is None:
                                stop(child)
                        break
                    assert time.monotonic() < until and remaining(window) > 5, 'OUTER_TASK_DEADLINE'
                    assert sum(p.stat().st_size for root in [O, RAW] for p in root.rglob('*') if p.is_file()) < 2 * 1024**3, 'STORAGE_LIMIT'
                    time.sleep(.25)
            finally:
                for job in jobs:
                    stop(job)
                for f in locals().get('files', []):
                    f.close()
                (R / 'REVIEW_PENDING').write_bytes(guard)
            native = read(out / 'RESULT.json'); ros = read(out / 'ROS_RESULT.json')
            proof = None
            if native.get('evidence_saved'):
                env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
                code = 'import sys,json;sys.path.insert(0,sys.argv[1]);from audit import audit;print(json.dumps(audit(json.load(open(sys.argv[2])))))'
                p = subprocess.run(['/home/linghu/miniconda3/envs/mk_mujoco/bin/python', '-B', '-c', code, str(C), str(out / 'TASK.json')], cwd=R, env=env, capture_output=True, text=True, timeout=40)
                (out / 'audit.console').write_text(p.stdout + p.stderr)
                if p.returncode == 0:
                    proof = json.loads(p.stdout); dump(out / 'FINAL_INDEPENDENT_AUDIT.json', proof)
            entry = dict(task=task['task_id'], passed=native['passed'] and ros['passed'] and bool(proof and proof['passed']), native=native, ros=ros, audit=proof, worker_returncodes=[p.returncode for p in jobs])
            results.append(entry); result['unexecuted'].remove(task['task_id']); dump(O / 'PARTIAL_RESULTS.json', results); jobs = []
            if not entry['passed']:
                result['stop_reason'] = 'FIRST_COMPONENT_OR_EVIDENCE_FAILURE'; break
        result['passed'] = len(results) == 4 and all(x['passed'] for x in results)
        if result['passed']:
            result['stop_reason'] = 'RPP_LEFT_RIGHT_TURN_BRAKE_COMPLETE'
    except BaseException as exc:
        result.update(error=repr(exc), traceback=traceback.format_exc(), stop_reason='OPERATION_STOP_NO_RETRY')
    finally:
        for job in jobs:
            stop(job)
        (R / 'REVIEW_PENDING').write_bytes(guard)
        result.update(closed=True, closed_unix=time.time(), source_unchanged=sources(), review_pending_restored=(R / 'REVIEW_PENDING').read_bytes() == guard)
        dump(O / 'COMPLETION.json', result)
        pointer = read(R / 'CURRENT_EXPERIMENT.json'); pointer.update(status='REVIEW_PENDING', active_run=None, active_window=None, active_entrypoint=None, next_physical_authorized=False)
        pointer['latest_v1296'] = dict(closed=True, component_passed=result['passed'], original_goal_navigation=False, completed_tasks=len(results), unexecuted=result['unexecuted'], report='docs/RPCCR_RPP_TURN_BRAKE_V1296_REPORT.md'); dump(R / 'CURRENT_EXPERIMENT.json', pointer)
        if (O / 'ACTIVE.json').exists():
            (O / 'ACTIVE.json').rename(O / 'CLOSED_PROCESSES.json')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
