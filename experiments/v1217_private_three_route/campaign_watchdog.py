"""Recorded Phase PIDs only; never restart or inspect unrelated processes."""
import fcntl
import os
import signal
import time
from worker_context import *


def alive(pid,start):
    try:
        row=Path('/proc',str(pid),'stat').read_text().split();return row[21]==str(start)and row[2]!='Z'
    except FileNotFoundError:return False


def terminate(row,group=False):
    pid=row['pid'];start=row['proc_start']
    if not alive(pid,start):return
    try:
        (os.killpg if group else os.kill)(pid,signal.SIGTERM)
        for _ in range(50):
            if not alive(pid,start):return
            time.sleep(.1)
        if alive(pid,start):(os.killpg if group else os.kill)(pid,signal.SIGKILL)
    except ProcessLookupError:pass


def main():
    receipt=read(O/'LAUNCH_RECEIPT.json')
    while alive(receipt['pid'],receipt['proc_start'])and not(O/'COMPLETION.json').exists():
        if remaining()<=0:
            active=read(O/'ACTIVE.json')if(O/'ACTIVE.json').exists()else{}
            if active.get('kind')=='worker'and active.get('pid'):terminate(active,True)
        time.sleep(1)
    if(O/'COMPLETION.json').exists():return
    active=read(O/'ACTIVE.json')if(O/'ACTIVE.json').exists()else{}
    if active.get('pid'):terminate(active,True)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+')
    acquired=False
    for _ in range(50):
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);acquired=True;break
        except BlockingIOError:time.sleep(.1)
    guard=(O/'GUARD.bin').read_bytes();assert __import__('hashlib').sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));(R/'REVIEW_PENDING').write_bytes(guard)
    done=read(O/'RESULTS.json')if(O/'RESULTS.json').exists()else[]
    result=dict(closed=True,passed=False,stop_reason='DRIVER_DISAPPEARED_NO_RESTART',stages=done,models=None,new_actual_native=None,own_replay_native=None,unknown_inflight_counts=True,execution_lock_idle=acquired,new24_executed=False)
    dump(O/'COMPLETION.json',result);dump(O/'LEDGER.json',result)
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_v1217_physical=result);dump(R/'CURRENT_EXPERIMENT.json',current)


if __name__=='__main__':main()
