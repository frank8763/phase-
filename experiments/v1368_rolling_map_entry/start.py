"""One explicitly approved entry continuation; original dual deadline unchanged."""
import fcntl
import subprocess
import sys
from component_context import *
from campaign import native_environment,storage_bytes


def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'LAUNCH.json').exists(),'ALREADY_CLAIMED'
    user=read(O/'USER_WINDOW.json');assert user['approved_single_entry_continuation'] is True,'ENTRY_CONTINUATION_NOT_AUTHORIZED'
    assert read(O/'QUALIFICATION.json')['passed'] and read(O/'FULL_ENTRY_QUALIFICATION.json')['passed'] and read(O/'OUTPUT_SCOPE_QUALIFICATION.json')['passed']
    assert read(O/'MAP_QUALIFICATION.json')['passed'] and read(O/'ACTUAL_MAP_SOFTWARE_QUALIFICATION.json')['passed']
    assert sources() and storage_bytes()<614*1024**2
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    window=read(R/'runs/v1367_shared_recovery_component/ROUND_WINDOW.json');assert remaining(window)>300,'ORIGINAL_DEADLINE_EXPIRED'
    dump(O/'ROUND_WINDOW.json',window);tasks=read(C/'TASKS.json')
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in tasks],absolute_deadline_unix=window['absolute_deadline_unix'],maximum_components=4,maximum_navigations=0,user_authority=user))
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_BOUNDED_SHARED_RECOVERY_COMPONENT',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'campaign.console').open('x') as log:job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'LAUNCH.json',dict(pid=job.pid,started_once=True,offline=True,maximum_components=4,maximum_navigations=0,window=window))
    dump(O/'HANDOFF.json',dict(started=True,owned_campaign_pid=job.pid,window=window,scope='RPP main/repeat then MPPI main/repeat safe recovery components,firstfailurestop',protocol=str((C/'PROTOCOL.md').relative_to(R))))
    print(json.dumps(dict(started=True,pid=job.pid,absolute_deadline_unix=window['absolute_deadline_unix'],maximum_components=4,maximum_navigations=0)))


if __name__=='__main__':main()
