"""Offline overnight matrix; one physics owner, isolated concurrent pure math."""
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import time
import traceback
from component_context import *
from relay_policy import classify,eligible
from worker_monitor import monitor,terminate

def native_environment():
    env=dict(os.environ);mesa=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH']=str(mesa)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.pop('LD_PRELOAD',None);env.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return env

def ros_environment(out,kind):
    spec=importlib.util.spec_from_file_location('phase_overnight_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py');ros=importlib.util.module_from_spec(spec);spec.loader.exec_module(ros)
    env=ros.environment();installs=[R/'runs/v1340_overnight_preparation/install',R/'runs/v931_deadband_consistent_mppi/install']
    env['AMENT_PREFIX_PATH']=':'.join(map(str,installs))+':'+env['AMENT_PREFIX_PATH'];env['LD_LIBRARY_PATH']=':'.join(str(p/'lib') for p in installs)+':'+env['LD_LIBRARY_PATH']
    env.update(ROS_DOMAIN_ID='225',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if kind=='mppi':env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
    else:env.pop('LD_PRELOAD',None);env.pop('PHASE_COHERENT_NOISE',None)
    return ros,env

def storage_bytes():
    seen=set();size=0
    for root in [C,O,RAW]:
        for p in root.rglob('*'):
            if p.is_file() and not p.is_symlink():
                s=p.stat();key=(s.st_dev,s.st_ino)
                if key not in seen:seen.add(key);size+=s.st_size
    return size

_storage_cache=[0.,0]
def monitored_storage():
    if time.monotonic()-_storage_cache[0]>=5.:_storage_cache[:]=[time.monotonic(),storage_bytes()]
    return _storage_cache[1]

def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    config=read(C/'CAMPAIGN_CONFIG.json');window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes()
    tasks=read(C/'TASKS.json');completed={'REUSED_V1368_RPP_MAIN':'PASSED'};results=[];jobs=[];logs=[]
    summary=dict(passed=False,results=results,unexecuted=[t['task_id'] for t in tasks],skipped_dependencies=[],ordinary_safe_failures=[],scope='controller recovery pairs then static pairs then original WE8 exposed development matrix',offline=True,reused_samples_not_new=['V1368_RPP_recovery_main'])
    def stop(*_):raise TimeoutError('OVERNIGHT_ROOT_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            if not eligible(task,completed):summary['skipped_dependencies'].append(task['task_id']);continue
            reserve=800 if task['stage']=='component' else 1700
            if remaining(window)<reserve:summary['stop_reason']='NO_TIME_FOR_COMPLETE_BOUNDED_TASK_AND_REPLAY';break
            if storage_bytes()>=config['raw_running_limit_bytes']-180*1024**2:summary['stop_reason']='STORAGE_RESERVE_FOR_COMPLETE_EVIDENCE_AND_ARCHIVE';break
            authorize(task,window);out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
            row=dict(task=task['task_id'],branch=task['branch'],stage=task['stage'],role=task['role'],candidate=task.get('candidate'),slot=task.get('slot'),attempted=True,passed=False,native=None,ros=None,audit=None)
            results.append(row);summary['unexecuted'].remove(task['task_id']);dump(O/'PARTIAL_RESULTS.json',results)
            component=task['stage']=='component';native_script='recovery_native.py' if component else 'route_native.py';ros_script='recovery_ros.py' if component else 'route_ros.py'
            jobs=[];logs=[];(R/'REVIEW_PENDING').unlink()
            try:
                log=(out/'native.console').open('x');logs.append(log)
                native=subprocess.Popen(['taskset','-c','2',str(R/'run_phase.sh'),str((C/native_script).relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native)
                dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='PREFIX_OR_TRUE_T0',pids=[native.pid]))
                if component:
                    end=min(time.monotonic()+600,window['hard_stop_monotonic']-300)
                    while not (out/'PREFIX_RESTORE.json').exists() and native.poll() is None:
                        assert time.monotonic()<end and storage_bytes()<config['raw_running_limit_bytes'],'PREFIX_TIME_STORAGE_LIMIT';time.sleep(.15)
                    if native.poll() is not None:raise RuntimeError('NATIVE_EXIT_BEFORE_COMPONENT_ORIGIN')
                ros,env=ros_environment(out,task['controller_kind']);log=(out/'ros.console').open('x');logs.append(log)
                peer=subprocess.Popen(['taskset','-c','3',*ros.command(['/usr/bin/python3.12','-B',str(C/ros_script),str(out/'TASK.json')])],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(peer)
                dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='LIVE_'+task['stage'].upper(),pids=[p.pid for p in jobs],cpus=dict(native=[2],ros=[3],planner=[4],audit=[5])))
                row['monitor']=monitor([peer,native],out,remaining=lambda:remaining(window),task_seconds=600 if component else 1600,drain_seconds=90,storage_check=lambda:monitored_storage()<config['raw_running_limit_bytes'])
            finally:
                for job in jobs:terminate(job)
                for log in logs:log.close()
                (R/'REVIEW_PENDING').write_bytes(guard)
            row.update(worker_returncodes=[p.returncode for p in jobs],native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None,ros=read(out/'ROS_RESULT.json') if (out/'ROS_RESULT.json').exists() else None);jobs=[]
            if (row['native'] or {}).get('evidence_saved') and (row['native'] or {}).get('replay',{}).get('passed'):
                # Exact producer Python/NumPy, no tolerance relaxation and no models.
                ros,env=ros_environment(out,'rpp')
                audited=subprocess.run(['taskset','-c','5',*ros.command(['/usr/bin/python3.12','-B',str(C/'audit_entry.py'),str(out/'TASK.json')])],cwd=R,env=env,capture_output=True,text=True,timeout=min(150,max(1,remaining(window)-20)))
                (out/'audit.console').write_text(audited.stdout+audited.stderr)
                if audited.returncode==0:row['audit']=json.loads(audited.stdout);dump(out/'FINAL_INDEPENDENT_AUDIT.json',row['audit'])
            row['classification']=classify(row);row['passed']=row['classification']=='PASSED';completed[task['task_id']]=row['classification']
            dump(O/'PARTIAL_RESULTS.json',results);dump(O/'COMPLETED.json',completed)
            if row['classification']=='FUNCTIONAL_FAILURE_SAFE_COMPLETE':summary['ordinary_safe_failures'].append(task['task_id'])
            elif row['classification']!='PASSED':summary['stop_reason']=row['classification'];break
        else:summary['stop_reason']='ALL_FROZEN_DEPENDENCIES_CLOSED'
        summary['passed']=any(row['stage']=='dynamic' and row['role']=='repeat' and row['passed'] for row in results)
    except BaseException as exc:summary.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='OPERATION_SOURCE_STORAGE_OR_DEADLINE_STOP')
    finally:
        for job in jobs:terminate(job)
        for log in logs:
            if not log.closed:log.close()
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard,storage_bytes=storage_bytes(),hard_stop_unix=window['absolute_deadline_unix'])
        dump(O/'COMPLETION.json',summary)
        if (O/'ACTIVE.json').exists():(O/'ACTIVE.json').unlink()
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False)
        pointer['latest_v1370']=dict(closed=True,any_dynamic_development_pair_passed=summary['passed'],attempted=len(results),unexecuted=len(summary['unexecuted']),stop_reason=summary.get('stop_reason'),report='docs/OVERNIGHT_CONTROLLER_MATRIX_V1370_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'finalize.console').open('x') as log:closed=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=closed.returncode,models=0))
    return 0 if summary['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
