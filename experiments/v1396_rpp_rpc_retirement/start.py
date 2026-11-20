import fcntl
import os
import subprocess
import sys
from component_context import *
def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'LAUNCH.json').exists(),'ALREADY_LAUNCHED'
    q=read(O/'QUALIFICATION.json');assert q['passed'] and sources()
    assert all(sha(R/p)==h for p,h in q['tested_source_hashes'].items()),'QUALIFICATION_SOURCE_CHANGED'
    d=read(DAY/'LEDGER.json');auth=read(R/'experiments/v1382_weekend_campaign/AUTHORIZATION.json')
    assert d.get('storage_ready') is True and read(DAY/'storage/FINALIZED.json')['passed'],'STORAGE_BACKUP_AND_RESERVE_NOT_READY'
    from campaign import storage_bytes
    assert read(R/'runs/v1393_full9390_preparation/FULL_REMOTE_VERIFIED.json')['passed'] and read(R/'runs/v1393_full9390_preparation/TRANSPORT_CLEANUP.json')['passed'],'PREDICTION_EVIDENCE_REMOTE_RECOVERY_REQUIRED'
    assert storage_bytes()<10*1024**3-512*1024**2,'GLOBAL_TEMPORARY_STORAGE_LIMIT'
    assert d['active_round'] is None and len(d['rounds'])<auth['maximum_rounds'] and d['vehicle_task_starts']+2<=auth['maximum_vehicle_task_starts']
    assert d['scientific_revisions']<=auth['maximum_scientific_revisions'],'SCIENTIFIC_REVISION_LIMIT'
    assert d['absolute_hard_stop_unix']==ROOT_END and d['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    now,mono=time.time(),time.monotonic();assert ROOT_END-now>1800;round_end=min(ROOT_END,now+5400)
    w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=round_end,hard_stop_monotonic=min(d['hard_stop_monotonic'],mono+round_end-now),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',w);(O/'REVIEW_PENDING.before').write_bytes((R/'REVIEW_PENDING').read_bytes())
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in read(C/'TASKS.json')],absolute_deadline_unix=round_end,authority=str(DAY/'LEDGER.json')))
    dump(O/'ROUND_LEDGER.json',dict(task_starts=0,maximum_tasks=2,original_deadline_unix=round_end))
    d.update(active_round=C.name,status='RUNNING_FIXED_ROUND',models_now_authorized=True);d['rounds'].append(dict(id=C.name,source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),started_unix=now,hard_stop_unix=round_end,maximum_tasks=2,status='RUNNING'));dump(DAY/'LEDGER.json',d)
    from campaign import native_environment
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_FROZEN_FULL9390_RPP',active_run=str(O.relative_to(R)),active_window=w,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'campaign.console').open('x') as log:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'LAUNCH.json',dict(pid=p.pid,window=w,offline=True));print(json.dumps(dict(started=True,pid=p.pid,round_deadline_unix=round_end,campaign_hard_stop_local='2026-11-23 09:00 +0800')))
if __name__=='__main__':main()
