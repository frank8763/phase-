"""Bounded offline single fault component, with complete tail/replay and audit."""
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import traceback
from component_context import *
from worker_monitor import monitor,terminate

def native_environment():
    env=dict(os.environ);mesa=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH']=str(mesa)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.pop('LD_PRELOAD',None);env.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return env
def peer_environment():
    spec=importlib.util.spec_from_file_location('phase_sampling_runtime',R/'experiments/v856_nav2_foundation/ros_environment.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    env=module.environment();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',ROS_LOG_DIR=str(O/'ros_logs'))
    return module,env
def storage_bytes():
    seen=set();size=0
    for root in [C,O,RAW]:
        for p in root.rglob('*'):
            if p.is_file() and not p.is_symlink():
                s=p.stat();key=(s.st_dev,s.st_ino)
                if key not in seen:seen.add(key);size+=s.st_size
    return size

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    window=read(O/'ROUND_WINDOW.json');task=read(C/'TASKS.json')[0];guard=(O/'REVIEW_PENDING.before').read_bytes()
    summary=dict(passed=False,closed=False,scope='one sampling fault component',new_navigation=0,results=[])
    jobs=[];logs=[];out=Path(task['output']);config=read(C/'CAMPAIGN_CONFIG.json')
    def stop(*_):raise TimeoutError('SAMPLING_ROOT_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        authorize(task,window);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
        assert storage_bytes()<config['raw_running_limit_bytes']-180*1024**2,'RAW_STORAGE_RESERVE'
        (R/'REVIEW_PENDING').unlink()
        log=(out/'native.console').open('x');logs.append(log)
        native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/'native_component.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native)
        dump(O/'ACTIVE.json',dict(phase='EXACT_HISTORICAL_PREFIX',pids=[native.pid]))
        prefix_end=min(time.monotonic()+600,window['hard_stop_monotonic']-300)
        while not (out/'PREFIX_RESTORE.json').exists() and native.poll() is None:
            assert time.monotonic()<prefix_end and storage_bytes()<config['raw_running_limit_bytes'],'PREFIX_TIME_STORAGE_LIMIT';time.sleep(.2)
        assert native.poll() is None,'NATIVE_EXIT_BEFORE_COMPONENT_ORIGIN'
        ros,env=peer_environment();log=(out/'peer.console').open('x');logs.append(log)
        peer=subprocess.Popen(['taskset','-c','3',*ros.command(['/usr/bin/python3.12','-B',str(C/'fault_peer.py'),str(out/'TASK.json')])],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(peer)
        dump(O/'ACTIVE.json',dict(phase='SAMPLING_FAULT_COMPONENT',pids=[native.pid,peer.pid]))
        summary['monitor']=monitor([peer,native],out,remaining=lambda:remaining(window),task_seconds=600,drain_seconds=90,storage_check=lambda:storage_bytes()<config['raw_running_limit_bytes'])
        summary['native']=read(out/'RESULT.json');summary['peer']=read(out/'ROS_RESULT.json')
        assert summary['native']['evidence_saved'] and summary['native'].get('replay',{}).get('passed'),'NATIVE_EVIDENCE_OR_REPLAY_FAILED'
        audit=subprocess.run(['taskset','-c','5',*ros.command(['/usr/bin/python3.12','-B',str(C/'audit_entry.py'),str(out/'TASK.json')])],cwd=R,env=env,capture_output=True,text=True,timeout=min(150,max(1,remaining(window)-20)))
        (out/'audit.console').write_text(audit.stdout+audit.stderr)
        assert audit.returncode==0,'INDEPENDENT_AUDIT_FAILED'
        proof=json.loads(audit.stdout.strip().splitlines()[-1]);dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof)
        summary.update(passed=bool(proof['passed'] and summary['native']['passed'] and summary['peer']['passed']),audit=proof,stop_reason='SINGLE_COMPONENT_CLOSED')
    except BaseException as exc:summary.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='FIRST_FAILURE_OR_EXCEPTION')
    finally:
        for job in jobs:terminate(job)
        for log in logs:log.close()
        if (out/'RESULT.json').exists():summary['native']=read(out/'RESULT.json')
        if (out/'ROS_RESULT.json').exists():summary['peer']=read(out/'ROS_RESULT.json')
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'COMPLETION.json',summary)
        (O/'ACTIVE.json').unlink(missing_ok=True)
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False)
        pointer['latest_v1372']=dict(closed=True,passed=summary['passed'],new_navigation=0,report='docs/COHERENT_SAMPLING_V1372_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'finalize.console').open('x') as log:
        final=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=final.returncode,models=0))
    return 0 if summary['passed'] and final.returncode==0 else 1
if __name__=='__main__':raise SystemExit(main())
