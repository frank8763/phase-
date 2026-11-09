"""OS-only owner/known child identity watchdog; never scan unrelated processes."""
import argparse,fcntl,json,os,signal,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v905_reference_execution_separation'
def identity(pid):
    try:
        p=Path('/proc')/str(pid);a=(p/'cmdline').read_bytes().split(b'\0');s=(p/'stat').read_text().rsplit(') ',1)[1].split()
        return dict(start_ticks=s[19],state=s[0],argv=[x.decode()for x in a if x])
    except FileNotFoundError:return None
def main():
    a=argparse.ArgumentParser();a.add_argument('--owner',type=int,required=True);args=a.parse_args();owner=identity(args.owner)
    deadline=json.loads((O/'ROUND_WINDOW.json').read_text())['deadline_unix']
    assert owner and str(R/'experiments/v905_reference_execution_separation/night.py')in owner['argv'],'REGISTERED_PHASE_OWNER_REQUIRED'
    print(json.dumps(dict(owner=args.owner,deadline_unix=deadline,os_only=True)),flush=True)
    while time.time()<deadline:
        current=identity(args.owner)
        if current is None or current['state']=='Z'or current['start_ticks']!=owner['start_ticks']or current['argv']!=owner['argv']:break
        if(O/'COMPLETION.json').exists():return
        time.sleep(2.)
    # Only registered Phase process groups; identity must still match the repo.
    entries=[]
    for path in [O/'ACTIVE_LAUNCHER.json',O/'WORKER_PROCESSES.json']:
        if path.exists():
            d=json.loads(path.read_text());entries+=d.get('jobs',[d])
    for row in entries:
        pid=row.get('pid');proof=identity(pid)if pid else None
        if proof and proof['state']!='Z'and any(str(R)in x for x in proof['argv'])and os.getpgid(pid)==pid:
            try:os.killpg(pid,signal.SIGTERM)
            except ProcessLookupError:pass
    try:
        live=identity(args.owner)
        if live and live['start_ticks']==owner['start_ticks']:os.kill(args.owner,signal.SIGTERM)
    except ProcessLookupError:pass
    # Restore only after the physical execution lock is actually idle.
    guard_restored=False
    until=time.monotonic()+8.
    while time.monotonic()<until:
        try:
            with(R/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                (R/'REVIEW_PENDING').write_bytes((O/'REVIEW_PENDING.before').read_bytes());guard_restored=True
            break
        except BlockingIOError:time.sleep(.1)
    (O/'WATCHDOG_STOP.json').write_text(json.dumps(dict(at=time.time(),owner_missing_or_deadline=True,guard_restored_only_after_lock_idle=guard_restored,models_started_by_watchdog=0))+'\n')
if __name__=='__main__':main()
