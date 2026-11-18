from gap_tools import *
import subprocess,fcntl,signal
def validate_authorization(a):
    assert a['authorized']is True and a['version']=='V1177'and a['window_seconds']==5400 and type(a['window_seconds'])is int
    assert a['scope']=='fixed_three_static_response_components_and_conditional_repeats'and a['user_instruction'].strip()
    return 5400
def main():
    assert not(O/'ROUND_WINDOW.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
    duration=validate_authorization(read(O/'AUTHORIZATION.json'));assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD
    assert all(read(O/n)['passed']for n in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json'])
    assert not any(Path(t['output']).exists()for t in read(C/'TASKS.json'))
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard);now=time.time();mono=time.monotonic()
    dump(O/'ROUND_WINDOW.json',dict(version='V1177',window_seconds=duration,started_unix=now,absolute_deadline_unix=now+duration,hard_stop_monotonic=mono+duration,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),previous_windows_unchanged=True))
    dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1177'))
    j=read(R/'CURRENT_EXPERIMENT.json');j.update(status='RUNNING_V1177_RESPONSE_COMPONENTS',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',j)
    child=None
    try:
        with(O/'campaign.console').open('x')as f:child=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        receipt=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],absolute_deadline_unix=now+duration,offline_capable=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
        with(O/'watchdog.console').open('x')as f:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        dump(O/'WATCHDOG_LAUNCH.json',dict(pid=w.pid,proc_start=Path('/proc',str(w.pid),'stat').read_text().split()[21]));print(json.dumps(receipt))
    except BaseException as exc:
        if child and child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
        (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'START_ERROR.json',dict(error=repr(exc),counts_unknown=child is not None));raise
if __name__=='__main__':main()
