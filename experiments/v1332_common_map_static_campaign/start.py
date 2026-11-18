"""Fresh user-authorized static root; both actual subprocess entrypoints checked."""
import ast
import fcntl
import importlib.util
import os
import subprocess
import sys
from component_context import *


def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'LAUNCH.json').exists(),'ONE_NEW_ROOT'
    assert sources() and read(O/'software/COMPLETION.json')['passed']
    assert read(O/'GEOMETRY_QUALIFICATION.json')['passed'] and read(O/'REFERENCE_QUALIFICATION.json')['passed']
    assert read(O/'OUTPUT_SCOPE_QUALIFICATION.json')['passed']
    frozen=read(C/'SOURCE_FREEZE.json')['files']
    for name in ['native_component.py','ros_component.py','audit.py','campaign.py','backend_check.py']:
        path=C/name; assert path.is_file() and str(path.relative_to(R)) in frozen; ast.parse(path.read_text())
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes(); (O/'REVIEW_PENDING.before').write_bytes(guard)
    now,mono=time.time(),time.monotonic()
    window=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',window)
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in read(C/'TASKS.json')],absolute_deadline_unix=window['absolute_deadline_unix'],window_seconds=5400,user_authority='2026-11-18 好，开始下一关的；多跑几关的，将这一步跑出来; four frozen same-map static tasks, new bounded90min',old_windows_unchanged=True,automatic_dynamics_or_fixed24=False))
    try:
        from campaign import native_environment
        env=native_environment()
        spec=importlib.util.spec_from_file_location('actual_cpu_namespace',R/'tools/isolate.py'); isolation=importlib.util.module_from_spec(spec); spec.loader.exec_module(isolation)
        backend=subprocess.run(isolation.command(C/'backend_check.py',writable=True),cwd=R,env=env,capture_output=True,text=True,timeout=30)
        (O/'backend.console').write_text(backend.stdout+backend.stderr); assert backend.returncode==0,'CPU_CONTEXT_FAILED'
        dump(O/'BACKEND_QUALIFICATION.json',json.loads(backend.stdout.strip().splitlines()[-1]))
        native=subprocess.run([sys.executable,'-B',str(C/'native_component.py'),str(C/'TASKS_entry.json'),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
        (O/'native_entry.console').write_text(native.stdout+native.stderr); assert native.returncode==0,'NATIVE_ENTRY_REJECTED'
        spec=importlib.util.spec_from_file_location('actual_ros_environment',R/'experiments/v856_nav2_foundation/ros_environment.py'); ros=importlib.util.module_from_spec(spec); spec.loader.exec_module(ros)
        renv=ros.environment(); install=R/'runs/v931_deadband_consistent_mppi/install'
        renv['AMENT_PREFIX_PATH']=str(install)+':'+renv['AMENT_PREFIX_PATH']; renv['LD_LIBRARY_PATH']=str(install/'lib')+':'+renv['LD_LIBRARY_PATH']
        renv.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
        entries=[]
        for taskfile in ['TASKS_entry.json','TASKS_rpp_entry.json']:
            entry=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(C/taskfile),'--entry-check']),cwd=R,env=renv,capture_output=True,text=True,timeout=30)
            (O/(taskfile+'.console')).write_text(entry.stdout+entry.stderr); assert entry.returncode==0,'ROS_ENTRY_REJECTED'
            entries.append(json.loads(entry.stdout.strip().splitlines()[-1]))
        dump(O/'FULL_CLI_ENTRY_QUALIFICATION.json',dict(passed=True,native=json.loads(native.stdout.strip().splitlines()[-1]),ros=entries,all_child_scripts_frozen=True,models=0,physical_native=0))
        assert remaining(window)>1700 and sources()
        pointer=read(R/'CURRENT_EXPERIMENT.json'); pointer.update(status='RUNNING_BOUNDED_STATIC_ROUTE',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True); dump(R/'CURRENT_EXPERIMENT.json',pointer)
        log=(O/'campaign.console').open('x'); job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); log.close()
        dump(O/'LAUNCH.json',dict(pid=job.pid,launched_once=True,absolute_deadline_unix=window['absolute_deadline_unix']))
        print(json.dumps(dict(started=True,pid=job.pid,scope='same-public-map MPPI main/repeat, independent RPP main/repeat; atmost4 static navigations',absolute_deadline_unix=window['absolute_deadline_unix'])))
    except BaseException as error:
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        dump(O/'COMPLETION.json',dict(closed=True,passed=False,stop_reason='PRE_MODEL_ENTRY_REJECTED',error=repr(error),models=0,new_actual_native=0,old_windows_unchanged=True))
        raise


if __name__=='__main__': main()
