"""One bounded isolated six-case software run. Never launches vehicles."""
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import time
import traceback
from common import *


def main():
    guard=(R/'REVIEW_PENDING').read_bytes();pointer=(R/'CURRENT_EXPERIMENT.json').read_bytes()
    begin=time.monotonic();job=None;results=[]
    claim=O/'RUN_CLAIM.json'
    with claim.open('x') as f:json.dump(dict(started_unix=time.time(),root_software_seconds=600,models=0),f)
    summary=dict(passed=False,software_only=True,models=0,physical_native=0,training_updates=0,
                 independent_navigation_trials=0,automatic_physical_continuation=False,results=results)
    try:
        os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
        with (R/'runs/v648_static_unknown/execution.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
        assert hashes_ok(),'FROZEN_DEPENDENCY_CHANGED'
        spec=importlib.util.spec_from_file_location('phase_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for index,task in enumerate(read(C/'SOFTWARE_TASKS.json')):
            assert hashes_ok(),'FROZEN_DEPENDENCY_CHANGED'
            assert time.monotonic()-begin<540,'SOFTWARE_ROOT_DEADLINE'
            env=module.environment();installs=[R/'runs/v1340_overnight_preparation/install',R/'runs/v931_deadband_consistent_mppi/install']
            env['AMENT_PREFIX_PATH']=':'.join(map(str,installs))+':'+env['AMENT_PREFIX_PATH']
            env['LD_LIBRARY_PATH']=':'.join(str(p/'lib') for p in installs)+':'+env['LD_LIBRARY_PATH']
            env.update(ROS_DOMAIN_ID=str(226+index),ROS_LOG_DIR=str(O/'ros_logs'/task['id']),CUDA_VISIBLE_DEVICES='',MKL_NUM_THREADS='1')
            if task['method']=='mppi':env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
            else:env.pop('LD_PRELOAD',None);env.pop('PHASE_COHERENT_NOISE',None)
            command=module.command(['/usr/bin/python3.12','-B',str(C/'probe.py'),str(index)])
            with (O/(task['id']+'.console')).open('x') as log:
                job=subprocess.Popen(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                dump(O/'ACTIVE.json',dict(task=task['id'],owned_pid=job.pid,models=0))
                end=min(begin+590,time.monotonic()+60)
                while job.poll() is None:
                    assert time.monotonic()<end,'SOFTWARE_WORKER_DEADLINE'
                    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<128*1024**2,'SOFTWARE_STORAGE_LIMIT'
                    time.sleep(.1)
            proof=read(O/task['id']/'RESULT.json');results.append(proof);dump(O/'PARTIAL.json',summary)
            if job.returncode!=0 or not proof['interface_qualified']:raise RuntimeError('FIRST_INTERFACE_OR_CONTROL_ANOMALY')
            job=None
        from software_audit import audit
        proof=audit();dump(O/'INDEPENDENT_AUDIT.json',proof)
        summary.update(passed=proof['passed'] and hashes_ok(),source_unchanged=hashes_ok())
    except BaseException as exc:
        summary.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll() is None:
            os.killpg(job.pid,signal.SIGTERM)
            try:job.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=2)
        summary.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-begin,
                       review_pending_unchanged=(R/'REVIEW_PENDING').read_bytes()==guard,
                       current_pointer_unchanged=(R/'CURRENT_EXPERIMENT.json').read_bytes()==pointer)
        summary['passed'] = summary['passed'] and summary['review_pending_unchanged'] and summary['current_pointer_unchanged']
        dump(O/'COMPLETION.json',summary)
        if (O/'ACTIVE.json').exists():(O/'ACTIVE.json').rename(O/'CLOSED_PROCESS.json')
    print(json.dumps(dict(passed=summary['passed'],cases=len(results),wall_s=summary['wall_s'],error=summary.get('error'),models=0)))
    return 0 if summary['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
