"""Single-use 90-minute launch, inaccessible without a new recorded human reply."""
import fcntl
import subprocess
import sys
from component_context import *
from campaign import native_environment,storage_bytes
def main():
    user=read(O/'USER_AUTHORIZATION.json')
    assert user['models_authorized'] is True and user['total_window_seconds']==5400,'NEW_WINDOW_NOT_APPROVED'
    assert user['scope']=='one_sampling_fault_component_only' and user['human_reply']
    assert not (O/'LAUNCH.json').exists() and not (O/'ROUND_WINDOW.json').exists(),'ALREADY_CLAIMED'
    for name in ['QUALIFICATION.json','TRANSPORT_QUALIFICATION.json','FULL_ENTRY_QUALIFICATION.json','OUTPUT_SCOPE_QUALIFICATION.json','AUDIT_QUALIFICATION.json']:
        proof=read(O/name);assert proof['passed'],name
        if name!='OUTPUT_SCOPE_QUALIFICATION.json':
            tested=proof.get('tested_source_hashes',proof.get('source_hashes',{}))
            assert set(tested)=={str(p.relative_to(R)) for p in C.glob('*.py')},'QUALIFICATION_FILE_SET_CHANGED '+name
            assert all(sha(R/p)==h for p,h in tested.items()),'QUALIFICATION_SOURCE_CHANGED '+name
    assert sources() and storage_bytes()<read(C/'CAMPAIGN_CONFIG.json')['raw_running_limit_bytes']-180*1024**2
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    (O/'REVIEW_PENDING.before').write_bytes((R/'REVIEW_PENDING').read_bytes())
    now,mono=time.time(),time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',window);task=read(C/'TASKS.json')[0]
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[task['task_id']],absolute_deadline_unix=window['absolute_deadline_unix']))
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_FROZEN_SAMPLING_COMPONENT',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'campaign.console').open('x') as log:
        job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'LAUNCH.json',dict(started_once=True,pid=job.pid,window=window,offline=True))
    dump(O/'HANDOFF.json',dict(owned_campaign_pid=job.pid,window=window,offline=True,maximum_components=1,maximum_navigation=0,storage_limit_bytes=2*1024**3))
    print(json.dumps(dict(started=True,pid=job.pid,window=window)))
if __name__=='__main__':main()
