import fcntl
import os
import subprocess
import sys
from component_context import *
def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not (O/'LAUNCH.json').exists(),'ALREADY_LAUNCHED'
    q=read(O/'QUALIFICATION.json');assert q['passed'] and sources()
    assert all(sha(R/p)==h for p,h in q['tested_source_hashes'].items()),'QUALIFICATION_SOURCE_CHANGED'
    d=read(DAY/'DAY_LEDGER.json');assert d['physical_scope_authorized_conditionally'] and d['component_tasks_started']==3
    assert not d.get('safety_or_evidence_fault_stops_today_physics',False),'DAY_SAFETY_OR_EVIDENCE_STOP_PRESERVED'
    with (R/'runs/v648_static_unknown/execution.lock').open('a+') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    now,mono=time.time(),time.monotonic();assert 1795165200-now>1800
    w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=1795165200,hard_stop_monotonic=mono+1795165200-now,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    dump(O/'ROUND_WINDOW.json',w);(O/'REVIEW_PENDING.before').write_bytes((R/'REVIEW_PENDING').read_bytes())
    dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=[t['task_id'] for t in read(C/'TASKS.json')],absolute_deadline_unix=1795165200,authority=str(DAY/'DAY_LEDGER.json')))
    from campaign import native_environment
    pointer=read(R/'CURRENT_EXPERIMENT.json');pointer.update(status='RUNNING_FROZEN_CAPTURE_COMPONENT',active_run=str(O.relative_to(R)),active_window=w,active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',pointer)
    with (O/'campaign.console').open('x') as log:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,env=native_environment(),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    dump(O/'LAUNCH.json',dict(pid=p.pid,window=w,offline=True));print(json.dumps(dict(started=True,pid=p.pid,hard_stop_local='2026-11-20 17:00 +0800')))
if __name__=='__main__':main()
