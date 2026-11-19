"""Four fixed components at most, one native owner, stop on first failure."""
import importlib.util
import os
import signal
import subprocess
import sys
import time
import traceback
from component_context import *
from worker_monitor import monitor,terminate


def native_environment():
    env=dict(os.environ);mesa=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu'
    env['LD_LIBRARY_PATH']=str(mesa)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    env.pop('LD_PRELOAD',None);env.update(CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',PYOPENGL_PLATFORM='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');return env


def ros_environment(out,branch):
    s=importlib.util.spec_from_file_location('phase_component_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    env=m.environment();installs=[R/'runs/v1340_overnight_preparation/install',R/'runs/v931_deadband_consistent_mppi/install']
    env['AMENT_PREFIX_PATH']=':'.join(map(str,installs))+':'+env['AMENT_PREFIX_PATH'];env['LD_LIBRARY_PATH']=':'.join(str(p/'lib') for p in installs)+':'+env['LD_LIBRARY_PATH']
    env.update(ROS_DOMAIN_ID='225',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if branch=='mppi':env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
    else:env.pop('LD_PRELOAD',None);env.pop('PHASE_COHERENT_NOISE',None)
    return m,env


def storage_bytes():return sum(p.stat().st_size for root in [O,RAW] for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def main():
    os.sched_setaffinity(0,{2,3,4,5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    tasks=read(C/'TASKS.json');config=read(C/'CAMPAIGN_CONFIG.json');window=read(O/'ROUND_WINDOW.json');guard=(O/'REVIEW_PENDING.before').read_bytes();jobs=[];logs=[];results=[]
    summary=dict(passed=False,results=results,unexecuted=[t['task_id'] for t in tasks],scope='four shared recovery components at most; no goalnavigation',models_for_supervision=0)
    def stop(*_):raise TimeoutError('ROOT_COMPONENT_WINDOW_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            authorize(task,window);assert storage_bytes()<config['raw_running_limit_bytes']
            out=Path(task['output']);out.mkdir(parents=True,exist_ok=False);dump(out/'TASK.json',task)
            row=dict(task=task['task_id'],branch=task['branch'],role=task['role'],attempted=True,passed=False)
            results.append(row);summary['unexecuted'].remove(task['task_id']);dump(O/'PARTIAL_RESULTS.json',results)
            (R/'REVIEW_PENDING').unlink();logs=[];jobs=[]
            try:
                log=(out/'native.console').open('x');logs.append(log)
                native=subprocess.Popen([str(R/'run_phase.sh'),str((C/'native_component.py').relative_to(R)),str(out/'TASK.json')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native)
                dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='EXACT_PREFIX_RECONSTRUCTION',pids=[native.pid]))
                until=min(time.monotonic()+600,window['hard_stop_monotonic']-300)
                while not (out/'PREFIX_RESTORE.json').exists() and native.poll() is None:
                    assert time.monotonic()<until and storage_bytes()<config['raw_running_limit_bytes'],'PREFIX_TIME_OR_STORAGE_LIMIT'
                    time.sleep(.1)
                if native.poll() is not None:raise RuntimeError('NATIVE_ENDED_BEFORE_EXACT_COMPONENT_ORIGIN')
                ros,env=ros_environment(out,task['branch']);log=(out/'ros.console').open('x');logs.append(log)
                peer=subprocess.Popen(ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(out/'TASK.json')]),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(peer)
                dump(O/'ACTIVE.json',dict(task=task['task_id'],phase='LIVE_SHARED_RECOVERY_COMPONENT',origin_native=15105,pids=[p.pid for p in jobs]))
                # The established monitor's positional contract is ROS first,
                # native second, independent of this campaign's launch order.
                row['monitor']=monitor([peer,native],out,remaining=lambda:remaining(window),task_seconds=600,drain_seconds=90,storage_check=lambda:storage_bytes()<config['raw_running_limit_bytes'])
            finally:
                for p in jobs:terminate(p)
                for log in logs:log.close()
                (R/'REVIEW_PENDING').write_bytes(guard)
            row.update(native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None,ros=read(out/'ROS_RESULT.json') if (out/'ROS_RESULT.json').exists() else None,worker_returncodes=[p.returncode for p in jobs]);jobs=[]
            if (row['native'] or {}).get('evidence_saved') and (row['native'] or {}).get('replay',{}).get('passed'):
                code='import sys,json;sys.path.insert(0,sys.argv[1]);from audit import audit;print(json.dumps(audit(json.load(open(sys.argv[2])))))'
                a=subprocess.run([sys.executable,'-B','-c',code,str(C),str(out/'TASK.json')],cwd=R,capture_output=True,text=True,timeout=min(90,max(1,remaining(window)-10)))
                (out/'audit.console').write_text(a.stdout+a.stderr)
                if a.returncode==0:row['audit']=json.loads(a.stdout);dump(out/'FINAL_INDEPENDENT_AUDIT.json',row['audit'])
            row['passed']=bool((row['native'] or {}).get('passed') and (row['ros'] or {}).get('passed') and (row.get('audit') or {}).get('passed'))
            dump(O/'PARTIAL_RESULTS.json',results)
            if not row['passed']:summary['stop_reason']='FIRST_COMPONENT_FAILURE_OR_EVIDENCE_ANOMALY';break
        else:summary.update(passed=True,stop_reason='ALL_FOUR_COMPONENT_AUDITS_PASSED')
    except BaseException as exc:summary.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='COMPONENT_OPERATION_OR_DEADLINE_STOP')
    finally:
        for p in jobs:terminate(p)
        for log in logs:
            if not log.closed:log.close()
        (R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'COMPLETION.json',summary)
        if (O/'ACTIVE.json').exists():(O/'ACTIVE.json').unlink()
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False)
        pointer['latest_v1368']=dict(closed=True,component_pair_passed=summary['passed'],unexecuted=summary['unexecuted'],stop_reason=summary.get('stop_reason'),report='docs/ROLLING_MAP_ENTRY_V1368_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'finalize.console').open('x') as log:p=subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    dump(O/'FINALIZER_EXIT.json',dict(returncode=p.returncode,models=0))
    return 0 if summary['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
