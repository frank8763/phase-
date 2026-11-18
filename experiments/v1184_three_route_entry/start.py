from route_tools import *
import subprocess,fcntl,signal
def validate_authorization(a):
    assert a['authorized']is True and a['version']=='V1184' and a['scope']=='three_known_course_fresh_feedback_development'
    assert type(a['window_seconds'])is int and a['window_seconds']==5400 and a['user_instruction'].strip() and not a['automatic_new24'] and a['stop_on_first_failure']
    return 5400
def main():
    assert not(O/'ROUND_WINDOW.json').exists() and not(O/'LAUNCH_RECEIPT.json').exists()
    duration=validate_authorization(read(O/'AUTHORIZATION.json'));assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
    assert not any(Path(t['output']).exists()for t in read(C/'TASKS.json'))
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    assert read(R/'CURRENT_EXPERIMENT.json')['active_run']is None
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard);now=time.time();mono=time.monotonic();inherited=read(O/'INHERITED_WINDOW.json');deadline=inherited['absolute_deadline_unix'];assert remaining(inherited)>1900 and read(R/'runs/v1183_three_route_feedback/COMPLETION.json')['physical_counts']['new_actual_native']==0
    dump(O/'ROUND_WINDOW.json',dict(inherited,version='V1184',continuation_started_unix=now,parent_window='runs/v1183_three_route_feedback/ROUND_WINDOW.json',deadline_not_reset=True))
    tasks=read(C/'TASKS.json');dump(O/'APPROVAL.json',dict(models_authorized=True,version='V1184',absolute_deadline_unix=deadline,allowed_task_ids=[t['task_id']for t in tasks]))
    j=read(R/'CURRENT_EXPERIMENT.json');j.update(status='RUNNING_V1184_THREE_ROUTE',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),next_physical_authorized=True,automatic_additional_simulation=False);dump(R/'CURRENT_EXPERIMENT.json',j)
    child=None
    try:
        with(O/'campaign.console').open('x')as f:child=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        receipt=dict(pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],absolute_deadline_unix=deadline,offline_capable=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
        with(O/'watchdog.console').open('x')as f:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        dump(O/'WATCHDOG_LAUNCH.json',dict(pid=w.pid,proc_start=Path('/proc',str(w.pid),'stat').read_text().split()[21]));print(json.dumps(receipt))
    except BaseException as exc:
        if child and child.poll()is None:os.killpg(child.pid,signal.SIGTERM)
        (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'START_ERROR.json',dict(error=repr(exc),counts_unknown=child is not None));raise
if __name__=='__main__':main()
