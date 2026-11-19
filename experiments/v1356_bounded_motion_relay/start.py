"""One complete readiness check and bounded background physical launch."""
import ast
import fcntl
import importlib.util
import subprocess
import sys
from component_context import *
from campaign import native_environment,ros_environment,storage_bytes


def main():
    assert not (O/'LAUNCH.json').exists() and not (O/'ROUND_WINDOW.json').exists(),'ROOT_ALREADY_CLAIMED'
    assert read(O/'software/COMPLETION.json')['passed'] and read(O/'CHANGED_BOUNDARY_QUALIFICATION.json')['passed']
    assert read(O/'INDEPENDENT_PREDICTION_COVERAGE.json')['passed'] and read(O/'ACTUAL_WORKER_QUALIFICATION.json')['passed']
    assert read(O/'OUTPUT_SCOPE_QUALIFICATION.json')['passed'] and read(O/'REUSED_QUALIFICATIONS.json')['passed']
    assert sources() and storage_bytes()<614*1024**2
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    # Readiness is performed before first model; root is locked once and never extended.
    now,mono=time.time(),time.monotonic();hard=read(C/'CAMPAIGN_CONFIG.json')['hard_stop_unix'];assert hard-now>1700,'AFTERNOON_TOO_LATE'
    window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=hard,hard_stop_monotonic=mono+hard-now,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',window);tasks=read(C/'TASKS.json')
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in tasks],
        absolute_deadline_unix=window['absolute_deadline_unix'],maximum_navigations=6,
        user_authority='检查，然后准备到下午五点的实验；多思考分析，合理安排; newfixed17oclock threefixedmotionpriorvariants dynamic mains and successrepeats',
        old_windows_unchanged=True,automatic_fixed24=False))
    try:
        spec=importlib.util.spec_from_file_location('phase_isolation',R/'tools/isolate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        env=native_environment();result=subprocess.run(module.command(C/'backend_check.py',writable=True),cwd=R,env=env,capture_output=True,text=True,timeout=30)
        (O/'backend.console').write_text(result.stdout+result.stderr);assert result.returncode==0,'CPU_BACKEND_REJECTED'
        dump(O/'BACKEND_QUALIFICATION.json',json.loads(result.stdout.strip().splitlines()[-1]));entries=[]
        for branch in read(C/'CAMPAIGN_CONFIG.json')['branches']:
            taskfile=C/('ENTRY_'+branch+'.json')
            if not entries:
                result=subprocess.run([sys.executable,'-B',str(C/'native_component.py'),str(taskfile),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=45)
                (O/'native_entry.console').write_text(result.stdout+result.stderr);assert result.returncode==0,'NATIVE_ENTRY_REJECTED'
                entries.append(dict(kind='native',proof=json.loads(result.stdout.strip().splitlines()[-1])))
            ros,renv=ros_environment(O,branch)
            result=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(taskfile),'--entry-check']),cwd=R,env=renv,capture_output=True,text=True,timeout=30)
            (O/(branch+'_entry.console')).write_text(result.stdout+result.stderr);assert result.returncode==0,'ROS_ENTRY_REJECTED'
            entries.append(dict(kind='ros',branch=branch,proof=json.loads(result.stdout.strip().splitlines()[-1])))
        dump(O/'FULL_ENTRY_QUALIFICATION.json',dict(passed=True,entries=entries,all_tasks_frozen=True,models=0,physical_native=0))
        assert sources() and remaining(window)>1700
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_BOUNDED_MOTION_AFTERNOON',active_run=str(O.relative_to(R)),
              active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
        with (O/'campaign.console').open('x') as log:
            job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        dump(O/'LAUNCH.json',dict(pid=job.pid,started_once=True,offline=True,absolute_deadline_unix=window['absolute_deadline_unix'],maximum_navigations=6))
        dump(O/'HANDOFF.json',dict(started=True,owned_campaign_pid=job.pid,window=window,branches=read(C/'CAMPAIGN_CONFIG.json')['branches'],
             compact_status_files=['ACTIVE.json','PARTIAL_RESULTS.json','COMPLETION.json','FINALIZED.json'],protocol=str((C/'PROTOCOL.md').relative_to(R))))
        print(json.dumps(dict(started=True,pid=job.pid,absolute_deadline_unix=window['absolute_deadline_unix'],maximum_navigations=6,storage_GiB=2)))
    except BaseException as exc:
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'COMPLETION.json',dict(closed=True,passed=False,
             stop_reason='PRE_MODEL_ENTRY_REJECTED',error=repr(exc),models=0,physical_native=0))
        raise


if __name__=='__main__':main()
