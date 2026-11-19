"""One offline overnight launch, fixed tomorrow09:00 before the first model."""
import fcntl
import subprocess
import sys
from component_context import *
from campaign import native_environment,storage_bytes

def main():
    assert not (O/'LAUNCH.json').exists() and not (O/'ROUND_WINDOW.json').exists(),'ALREADY_CLAIMED'
    user=read(O/'USER_AUTHORIZATION.json');assert user['overnight_approved'] and user['storage_limit_bytes']==10*1024**3
    for name in ['QUALIFICATION.json','SOFTWARE_QUALIFICATION.json','FULL_ENTRY_QUALIFICATION.json','OUTPUT_SCOPE_QUALIFICATION.json','PLANNER_QUALIFICATION.json','HORIZON_AUDIT_QUALIFICATION.json']:assert read(O/name)['passed'],name
    assert sources() and storage_bytes()<read(C/'CAMPAIGN_CONFIG.json')['raw_running_limit_bytes']
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    now,mono=time.time(),time.monotonic();stop=1795136400.;assert 0<stop-now<=16*3600
    window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=stop,hard_stop_monotonic=mono+stop-now,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',window);tasks=read(C/'TASKS.json');dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in tasks],absolute_deadline_unix=stop,maximum_components=7,maximum_navigations=264,user_authority=user))
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_FROZEN_OVERNIGHT_MATRIX',active_run=str(O.relative_to(R)),active_window=window,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'campaign.console').open('x') as log:job=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'LAUNCH.json',dict(started_once=True,pid=job.pid,offline=True,window=window));dump(O/'HANDOFF.json',dict(owned_campaign_pid=job.pid,offline=True,window=window,protocol=str((C/'PROTOCOL.md').relative_to(R)),storage_limit_bytes=10*1024**3,resource_policy=dict(native=[2],ros=[3],planner=[4],audit=[5]),ordinary_failure_advances=True,safety_evidence_fault_stops=True))
    print(json.dumps(dict(started=True,pid=job.pid,hard_stop_unix=stop,hard_stop_local='2026-11-20 09:00 +0800',storage_limit_GiB=10)))

if __name__=='__main__':main()
