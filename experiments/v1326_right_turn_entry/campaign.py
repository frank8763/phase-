"""One physical owner, complete attempted accounting, first failure stops."""
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
    env.pop('LD_PRELOAD', None)
    env.update(CUDA_VISIBLE_DEVICES='', MUJOCO_GL='osmesa', PYOPENGL_PLATFORM='osmesa', LIBGL_ALWAYS_SOFTWARE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env


def stop(job):
    if job.poll() is None:
        os.killpg(job.pid, signal.SIGTERM)
        try: job.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(job.pid, signal.SIGKILL); job.wait(timeout=2)


def main():
    os.sched_setaffinity(0, {2,3,4,5}); os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    window = read(O/'ROUND_WINDOW.json'); guard = (O/'REVIEW_PENDING.before').read_bytes()
    tasks = read(C/'TASKS.json'); results = []; jobs = []
    summary = dict(passed=False, results=results, unexecuted=[t['task_id'] for t in tasks], scope='coherent_mppi_right_mechanical_turn_component_at_registered_EW', original_WE_right_geometry_rejection_preserved=True)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('CAMPAIGN_STOP')))
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('ROOT_DEADLINE')))
    signal.setitimer(signal.ITIMER_REAL,max(.01,remaining(window)-5))
    try:
        for task in tasks:
            authorize(task,window)
            out=Path(task['output']); out.mkdir(parents=True,exist_ok=False); dump(out/'TASK.json',task)
            row=dict(task=task['task_id'],attempted=True,passed=False,native=None,ros=None,audit=None)
            results.append(row); summary['unexecuted'].remove(task['task_id']); dump(O/'PARTIAL_RESULTS.json',results)
            (R/'REVIEW_PENDING').unlink(); logs=[]
            try:
                spec=importlib.util.spec_from_file_location('phase_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py')
                ros=importlib.util.module_from_spec(spec); spec.loader.exec_module(ros)
                env=ros.environment(); install=R/'runs/v931_deadband_consistent_mppi/install'
                env['AMENT_PREFIX_PATH']=str(install)+':'+env['AMENT_PREFIX_PATH']
                env['LD_LIBRARY_PATH']=str(install/'lib')+':'+env['LD_LIBRARY_PATH']
                env.update(ROS_DOMAIN_ID='223',ROS_LOG_DIR=str(out/'ros_logs'),CUDA_VISIBLE_DEVICES='',LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
                definitions=[('ros',ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(out/'TASK.json')]),env),
                             ('native',[str(R/'run_phase.sh'),str((C/'native_component.py').relative_to(R)),str(out/'TASK.json')],native_environment())]
                for name,cmd,environment in definitions:
                    log=(out/(name+'.console')).open('x'); logs.append(log)
                    jobs.append(subprocess.Popen(cmd,cwd=R,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
                dump(O/'ACTIVE.json',dict(task=task['task_id'],pids=[p.pid for p in jobs],physics_single_instance=True))
                end=min(time.monotonic()+360,window['hard_stop_monotonic']-5)
                while any(p.poll() is None for p in jobs):
                    if any(p.poll() not in (None,0) for p in jobs):
                        for job in jobs: stop(job)
                        break
                    assert time.monotonic()<end and remaining(window)>5,'TASK_DEADLINE'
                    assert sum(p.stat().st_size for root in [O,RAW] for p in root.rglob('*') if p.is_file() and not p.is_symlink())<2*1024**3,'STORAGE_LIMIT'
                    time.sleep(.25)
            finally:
                for job in jobs: stop(job)
                for log in logs: log.close()
                (R/'REVIEW_PENDING').write_bytes(guard)
            row.update(worker_returncodes=[p.returncode for p in jobs],native=read(out/'RESULT.json') if (out/'RESULT.json').exists() else None,
                       ros=read(out/'ROS_RESULT.json') if (out/'ROS_RESULT.json').exists() else None)
            jobs=[]; dump(O/'PARTIAL_RESULTS.json',results)
            native=row['native'] or {}
            if native.get('evidence_saved') and native.get('replay',{}).get('passed'):
                code='import sys,json;sys.path.insert(0,sys.argv[1]);from audit import audit;print(json.dumps(audit(json.load(open(sys.argv[2])))))'
                run=subprocess.run([sys.executable,'-B','-c',code,str(C),str(out/'TASK.json')],cwd=R,capture_output=True,text=True,timeout=min(40,max(1,remaining(window)-10)))
                (out/'audit.console').write_text(run.stdout+run.stderr)
                if run.returncode==0:
                    row['audit']=json.loads(run.stdout); dump(out/'FINAL_INDEPENDENT_AUDIT.json',row['audit'])
            row['passed']=bool(native.get('passed') and (row['ros'] or {}).get('passed') and (row['audit'] or {}).get('passed'))
            dump(O/'PARTIAL_RESULTS.json',results)
            if not row['passed']:
                summary['stop_reason']='FIRST_COMPONENT_SAFETY_OR_EVIDENCE_FAILURE'; break
        else: summary.update(passed=True,stop_reason='RIGHT_COMPONENT_MAIN_REPEAT_COMPLETE')
    except BaseException as error:
        summary.update(error=repr(error),traceback=traceback.format_exc(),stop_reason='OPERATION_OR_DEADLINE_STOP')
    finally:
        for job in jobs: stop(job)
        (R/'REVIEW_PENDING').write_bytes(guard); signal.setitimer(signal.ITIMER_REAL,0)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        summary.update(closed=True,closed_unix=time.time(),source_unchanged=sources(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'COMPLETION.json',summary); dump(O/'CLOSED_PROCESSES.json',dict(closed=True,results=len(results)))
        if (O/'ACTIVE.json').exists(): (O/'ACTIVE.json').unlink()
        pointer=read(R/'CURRENT_EXPERIMENT.json'); pointer.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False)
        pointer['latest_v1326']=dict(closed=True,component_passed=summary['passed'],attempted=[r['task'] for r in results],unexecuted=summary['unexecuted'],stop_reason=summary.get('stop_reason'),report='docs/COHERENT_MPPI_TURN_V1326_REPORT.md')
        dump(R/'CURRENT_EXPERIMENT.json',pointer)
    print(json.dumps(dict(closed=True,passed=summary['passed'],stop_reason=summary.get('stop_reason'),attempted=len(results))))
    return 0 if summary['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
