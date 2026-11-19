"""Freeze-checked offline launch once, all models remain behind run_phase."""
import ast
import fcntl
import importlib.util
import subprocess
import sys
from component_context import *
from campaign import native_environment,ros_environment,storage_bytes


def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'LAUNCH.json').exists(),'ONE_OVERNIGHT_ROOT'
    config=read(C/'CAMPAIGN_CONFIG.json')
    assert read(O/'software/COMPLETION.json')['passed'] and read(O/'INSTALLED_PLUGIN_QUALIFICATION.json')['passed']
    assert read(O/'CAUSAL_ROUTE_QUALIFICATION.json')['passed']
    assert read(R/'runs/v1342_dynamic_relay_preparation/CAUSAL_OCCUPANCY_QUALIFICATION.json')['passed']
    assert read(O/'RELAY_POLICY_QUALIFICATION.json')['passed'] and read(R/'runs/v1340_overnight_preparation/MONITOR_QUALIFICATION.json')['passed']
    assert read(O/'OUTPUT_SCOPE_QUALIFICATION.json')['passed'] and read(O/'FINALIZER_QUALIFICATION.json')['passed'] and sources()
    assert read(O/'IO_QUALIFICATION.json')['passed'] and read(O/'ASYNC_REAL_PLANNER_QUALIFICATION.json')['passed'] and read(O/'LIVE_RESULT_QUALIFICATION.json')['passed']
    assert storage_bytes()<config['storage_limit_bytes'],'STORAGE_LIMIT'
    for name in ['native_component.py','ros_component.py','campaign.py','worker_monitor.py','relay_policy.py','finalize.py','audit.py']:
        assert str((C/name).relative_to(R)) in read(C/'SOURCE_FREEZE.json')['files'];ast.parse((C/name).read_text())
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    now,mono=time.time(),time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    config['hard_stop_unix']=window['absolute_deadline_unix']
    dump(O/'ROUND_WINDOW.json',window)
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in read(C/'TASKS.json')],absolute_deadline_unix=config['hard_stop_unix'],user_authority='2026-11-19 下一步开始; newbounded90min sourcequalified nonblocking I/O static main/repeat thenconditionaloriginalWEdynamicmain/repeat; expirednightunchanged',maximum_navigations=4,old_windows_unchanged=True,automatic_fixed24=False))
    try:
        spec=importlib.util.spec_from_file_location('phase_cpu_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
        env=native_environment()
        result=subprocess.run(isolation.command(C/'backend_check.py',writable=True),cwd=R,env=env,capture_output=True,text=True,timeout=30)
        (O/'backend.console').write_text(result.stdout+result.stderr);assert result.returncode==0,'CPU_BACKEND_REJECTED';dump(O/'BACKEND_QUALIFICATION.json',json.loads(result.stdout.strip().splitlines()[-1]))
        entries=[]
        # Same native binder for all presets; one complete actual native CLI,
        # and one real ROS CLI per distinct plugin/config before first model.
        taskfile=C/'ENTRY_rpp_async_default.json'
        result=subprocess.run([sys.executable,'-B',str(C/'native_component.py'),str(taskfile),'--entry-check'],cwd=R,env=env,capture_output=True,text=True,timeout=60)
        (O/'native_entry.console').write_text(result.stdout+result.stderr);assert result.returncode==0,'NATIVE_ENTRY_REJECTED'
        entries.append(dict(kind='native',proof=json.loads(result.stdout.strip().splitlines()[-1])))
        for branch in config['branches']:
            taskfile=C/('ENTRY_'+branch+'.json');ros,renv=ros_environment(O,branch)
            result=subprocess.run(ros.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(taskfile),'--entry-check']),cwd=R,env=renv,capture_output=True,text=True,timeout=30)
            (O/(branch+'_entry.console')).write_text(result.stdout+result.stderr);assert result.returncode==0,'ROS_ENTRY_REJECTED '+branch
            entries.append(dict(kind='ros',branch=branch,proof=json.loads(result.stdout.strip().splitlines()[-1])))
        dump(O/'FULL_ENTRY_QUALIFICATION.json',dict(passed=True,entries=entries,all_tasks_frozen_and_validated=True,models=0,physical_native=0))
        assert sources() and remaining(window)>1700
        pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_FROZEN_OVERNIGHT_BASELINE_RELAY',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
        log=(O/'campaign.console').open('x');job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close()
        dump(O/'LAUNCH.json',dict(pid=job.pid,started_once=True,hard_stop_unix=config['hard_stop_unix'],offline=True,maximum_tasks=4))
        print(json.dumps(dict(started=True,pid=job.pid,offline=True,absolute_deadline_unix=window['absolute_deadline_unix'],temporary_limit_GiB=2,branches=config['branches'],maximum_navigations=4)))
    except BaseException as error:
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'COMPLETION.json',dict(closed=True,passed=False,stop_reason='PRE_MODEL_ENTRY_REJECTED',error=repr(error),models=0,physical_native=0))
        raise


if __name__=='__main__':main()
