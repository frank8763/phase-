"""Qualified entry-only continuation, original V1325 deadline unchanged."""
import fcntl
import importlib.util
import os
import subprocess
import sys
from component_context import *


def main():
    assert not (O/'LAUNCH.json').exists(),'ONE_CONTINUATION'
    old=R/'runs/v1325_right_turn_qualification'
    prior=read(old/'COMPLETION.json'); assert prior['closed'] and not prior['passed']
    assert 'ros_component.py' in (R/'runs/v858_nav2_verified/v1325/right_main/ros.console').read_text()
    assert not (R/'experiments/v1325_right_turn_qualification/ros_component.py').exists()
    window=read(old/'ROUND_WINDOW.json'); assert remaining(window)>500 and sources()
    assert read(O/'OUTPUT_SCOPE_QUALIFICATION.json')['passed']
    assert read(old/'software/COMPLETION.json')['passed'] and read(old/'ROTATION_METRIC_QUALIFICATION.json')['passed']
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes(); assert guard==(old/'REVIEW_PENDING.before').read_bytes()
    (O/'REVIEW_PENDING.before').write_bytes(guard); dump(O/'ROUND_WINDOW.json',window)
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in read(C/'TASKS.json')],absolute_deadline_unix=window['absolute_deadline_unix'],entry_only=True,prior_error_preserved=True,user_authority='User explicitly requests supervision, self-repair and continuation, and now 下一步继续推进',no_deadline_reset=True))
    # Every actual subprocess script must exist, parse, and be present in freeze.
    frozen=read(C/'SOURCE_FREEZE.json')['files']
    import ast
    for name in ['ros_component.py','native_component.py','audit.py','campaign.py','backend_check.py']:
        path=C/name; assert str(path.relative_to(R)) in frozen; ast.parse(path.read_text())
    from campaign import native_environment
    environment=native_environment()
    native=subprocess.run([sys.executable,'-B',str(C/'native_component.py'),str(C/'TASKS_entry.json'),'--entry-check'],cwd=R,env=environment,capture_output=True,text=True,timeout=60)
    (O/'native_entry.console').write_text(native.stdout+native.stderr); assert native.returncode==0,'NATIVE_ENTRY_REJECTED'
    spec=importlib.util.spec_from_file_location('actual_ros_entry_environment',R/'experiments/v856_nav2_foundation/ros_environment.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    env=mod.environment(); install=R/'runs/v931_deadband_consistent_mppi/install'
    env['AMENT_PREFIX_PATH']=str(install)+':'+env['AMENT_PREFIX_PATH']; env['LD_LIBRARY_PATH']=str(install/'lib')+':'+env['LD_LIBRARY_PATH']
    env.update(LD_PRELOAD=str(R/'runs/v1319_mppi_coherent_sampling/libcoherent.so'),PHASE_COHERENT_NOISE='1')
    entry=subprocess.run(mod.command(['/usr/bin/python3.12','-B',str(C/'ros_component.py'),str(C/'TASKS_entry.json'),'--entry-check']),cwd=R,env=env,capture_output=True,text=True,timeout=30)
    (O/'ros_entry.console').write_text(entry.stdout+entry.stderr); assert entry.returncode==0,'ROS_ENTRY_REJECTED'
    dump(O/'FULL_CLI_ENTRY_QUALIFICATION.json',dict(passed=True,actual_native_entry=json.loads(native.stdout.strip().splitlines()[-1]),actual_ros_entry=json.loads(entry.stdout.strip().splitlines()[-1]),all_child_scripts_frozen=True,models=0,physical_native=0))
    pointer=read(R/'CURRENT_EXPERIMENT.json'); pointer.update(status='RUNNING_BOUNDED_COMPONENT',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True); dump(R/'CURRENT_EXPERIMENT.json',pointer)
    log=(O/'campaign.console').open('x'); job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True); log.close()
    dump(O/'LAUNCH.json',dict(pid=job.pid,launched_once=True,original_deadline_unix=window['absolute_deadline_unix'],no_deadline_reset=True)); print(json.dumps(dict(started=True,pid=job.pid,original_deadline_unix=window['absolute_deadline_unix'])))


if __name__=='__main__': main()
