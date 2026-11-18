# Derived original recorded-PID watchdog; never scans other jobs.
"""Recorded Phase PIDs only. Deadline/driver death closes, never restarts."""
from campaign_context import *
import fcntl
import signal


def alive(pid,start):
    try:
        row=Path('/proc',str(pid),'stat').read_text().split();return row[21]==str(start)and row[2]!='Z'
    except FileNotFoundError:return False


def terminate(pid,start,group=False):
    if not alive(pid,start):return
    send=(lambda sig:os.killpg(pid,sig))if group else(lambda sig:os.kill(pid,sig))
    try:
        send(signal.SIGTERM)
        for _ in range(50):
            if not alive(pid,start):return
            time.sleep(.1)
        if alive(pid,start):send(signal.SIGKILL)
    except ProcessLookupError:pass


def main():
    launch=read(O/'LAUNCH_RECEIPT.json');pid,start=launch['pid'],launch['proc_start']
    while alive(pid,start)and not(O/'COMPLETION.json').exists():
        if remaining()<=0:terminate(pid,start);break
        time.sleep(2)
    if (O/'COMPLETION.json').exists():return
    active=read(O/'ACTIVE.json')if(O/'ACTIVE.json').exists()else{}
    if active.get('pid'):terminate(active['pid'],active['proc_start'],True)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    for _ in range(50):
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
        except BlockingIOError:time.sleep(.1)
    else:
        dump(O/'WATCHDOG_ERROR.json',dict(error='LOCK_NOT_IDLE_NO_RESTART',models_started=0));return
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD
    (R/'REVIEW_PENDING').write_bytes(guard)
    stages=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    for row in stages:
        task=next(t for t in read(C/'TASKS.json')if t['task_id']==row['stage']);p=Path(task['output'])/'RESULT.json'
        if p.exists():row['result']=read(p)
    summary=dict(closed=True,passed=False,stop_reason='DRIVER_INTERRUPTED_OR_ABSOLUTE_DEADLINE',stages=stages,
        unknown_inflight_counts=True,models=None,new_actual_native=None,own_replay_native=None,
        fresh_known_course_main_repeat_passed=False,same_version_three_routes_passed=False,new24_executed=False,guard_original=True)
    dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
    dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,
        active_entrypoint=None,next_physical_authorized=False,latest_v1225=summary)
    dump(R/'CURRENT_EXPERIMENT.json',current)
    import subprocess
    with(O/'watchdog_finalize.console').open('x')as f:subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=120)


if __name__=='__main__':main()
