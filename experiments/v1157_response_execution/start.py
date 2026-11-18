"""Starts only after explicit new window authorization; no implicit renewal."""
from response_tools import *
import fcntl
import signal
import subprocess
import traceback


def validate_authorization(auth):
    assert auth.get('authorized')is True,'NEW_WINDOW_NOT_AUTHORIZED'
    assert auth.get('version')=='V1157'and auth.get('scope')=='fixed_response_main_and_complete_repeat','WRONG_AUTHORIZATION_SCOPE'
    assert auth.get('window_seconds')==5400 and type(auth['window_seconds'])is int,'WRONG_WINDOW'
    assert isinstance(auth.get('user_instruction'),str)and auth['user_instruction'].strip(),'MISSING_USER_INSTRUCTION'
    return auth['window_seconds']


def main():
    assert not (O/'ROUND_WINDOW.json').exists() and not(O/'LAUNCH_RECEIPT.json').exists(),'NO_RESET_OR_SECOND_INSTANCE'
    duration=validate_authorization(read(O/'AUTHORIZATION.json'))
    assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD_SHA
    assert all(read(O/p)['passed']for p in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json'])
    assert not any(Path(t['output']).exists()for t in read(C/'TASKS.json')),'PRIOR_PHYSICAL_OUTPUT_EXISTS'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    assert used()+128*1024**2<2*1024**3
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard)
    child=None
    try:
        now=time.time();mono=time.monotonic()
        dump(O/'ROUND_WINDOW.json',dict(version='V1157',started_unix=now,started_monotonic=mono,
            absolute_deadline_unix=now+duration,hard_stop_monotonic=mono+duration,
            boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),window_seconds=duration,
            previous_windows_unchanged=True,scope='fixed static response component main then conditional complete repeat'))
        dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1157',scope='fixed_response_main_and_complete_repeat'))
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING_V1157_RESPONSE_COMPONENT',
            active_run=str(O.relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),
            active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True)
        dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'campaign.console').open('x')as log:
            child=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        launch=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],
            absolute_deadline_unix=now+duration,offline_capable=True,detached=True)
        dump(O/'LAUNCH_RECEIPT.json',launch)
        with(O/'watchdog.console').open('x')as log:
            watcher=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        dump(O/'WATCHDOG_LAUNCH.json',dict(pid=watcher.pid,proc_start=Path('/proc',str(watcher.pid),'stat').read_text().split()[21]))
        print(encode(launch))
    except BaseException as error:
        if child is not None and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        (R/'REVIEW_PENDING').write_bytes(guard)
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        failure=dict(closed=True,passed=False,stop_reason='STARTUP_EXCEPTION_NO_RESTART',error=repr(error),
            traceback=traceback.format_exc(),models=0 if child is None else None,
            new_actual_native=0 if child is None else None,unknown_inflight_counts=child is not None)
        dump(O/'START_ERROR.json',failure)
        if not (O/'COMPLETION.json').exists():dump(O/'COMPLETION.json',failure)
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,
            active_entrypoint=None,next_physical_authorized=False,latest_v1157_start_failure=failure)
        dump(R/'CURRENT_EXPERIMENT.json',current)
        raise


if __name__=='__main__':main()
