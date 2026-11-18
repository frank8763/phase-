"""Four-task bounded campaign. Explicit user authorization is absent by default."""
import fcntl
import gzip
import os
import signal
import subprocess
import sys
import time
import traceback
from worker_context import *
from sequence import decision


def validate_authorization(a):
    assert a.get('authorized')is True,'NEW_USER_WINDOW_REQUIRED'
    assert a.get('scope')=='two_exposed_slots_main_repeat_only' and a.get('automatic_new24')is False and a.get('stop_on_first_failure')is True,'USER_SCOPE'
    assert type(a.get('window_seconds'))is int and 1800<=a['window_seconds']<=43200,'EXPLICIT_BOUNDED_WINDOW_REQUIRED'
    return a['window_seconds']


def frozen_ok():
    return all(sha(R/p)==h for name in ['WORKER_FREEZE.json','CAMPAIGN_FREEZE.json']for p,h in read(C/name)['files'].items())


def compare_paths(main,repeat):
    old=science();np=old.np
    main=Path(main);repeat=Path(repeat);maximum=0.
    assert sha(main/'physics/scene_model.mjb')==sha(repeat/'physics/scene_model.mjb')
    with np.load(main/'physics/NATIVE_TRACE.npz')as a,np.load(repeat/'physics/NATIVE_TRACE.npz')as b:
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:
            assert a[key].shape==b[key].shape
            if a[key].size:maximum=max(maximum,float(abs(a[key]-b[key]).max()))
    assert maximum<=1e-8,'FULL_REPEAT_STATE_CONTROL_MOCAP'
    a=read(main/'CANONICAL_INITIAL_PACKET.json');b=read(repeat/'CANONICAL_INITIAL_PACKET.json')
    for key in ['state','last_ctrl']:assert abs(np.asarray(old.q.initial(a)[key])-old.q.initial(b)[key]).max()<=1e-8
    assert abs(old.q.initial(a)['integral']-old.q.initial(b)['integral'])<=1e-8
    for directory in [main,repeat]:assert read(directory/'RESULT.json')['physical']['bad_contacts']==0
    with gzip.open(main/'physics/CONTACTS.json.gz','rt')as f:a=json.load(f)
    with gzip.open(repeat/'physics/CONTACTS.json.gz','rt')as f:b=json.load(f)
    assert len(a)==len(b)
    for one,two in zip(a,b):
        assert len(one)==len(two)
        for c,d in zip(one,two):assert c[:3]==d[:3] and abs(c[3]-d[3])<=1e-8
    assert read(main/'RESULT.json')['physical']['first_actor_detection']==read(repeat/'RESULT.json')['physical']['first_actor_detection']
    return dict(passed=True,maximum_state_control_mocap_error=maximum,model_initial_contact_discovery_equal=True)


def compare_repeat(task):
    return compare_paths(RAW/('main_slot'+str(task['slot']).zfill(2)),task['output'])


def terminate(process):
    if process.poll()is not None:return
    try:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
    except ProcessLookupError:pass


def main():
    try:
        auth=read(O/'USER_AUTHORIZATION.json');seconds=validate_authorization(auth)
        assert read(O/'READY_FOR_REVIEW.json')['preparation_gates_passed'] and frozen_ok()
        assert not (O/'ROUND_WINDOW.json').exists() and not (O/'COMPLETION.json').exists(),'OLD_WINDOW_CANNOT_REOPEN'
        guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    except BaseException as exc:
        print(json.dumps(dict(started=False,models=0,reason=str(exc))));return 2
    launch=(O/'launch.lock').open('a+');fcntl.flock(launch,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    tasks=read(C/'TASKS.json')
    window=read(R/'runs/v1204_goal_audit_worker/ROUND_WINDOW.json')
    assert seconds==5400 and abs(window['absolute_deadline_unix']-window['started_unix']-seconds)<=1e-5
    assert remaining(window)>1700,'ORIGINAL_DEADLINE_INSUFFICIENT_NO_EXTENSION'
    dump(O/'ROUND_WINDOW.json',window);(O/'GUARD.bin').write_bytes(guard)
    dump(O/'APPROVAL.json',dict(models_authorized=True,window_seconds=seconds,absolute_deadline_unix=window['absolute_deadline_unix'],allowed_task_ids=[t['task_id']for t in tasks],stop_on_first_failure=True,automatic_new24=False))
    dump(O/'LAUNCH_RECEIPT.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    finished=[];repeats={};active=None;stop_reason='UNEXPECTED_DRIVER_EXIT';error=None
    def halt(*_):raise TimeoutError('CAMPAIGN_SIGNAL_STOP')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGINT,halt)
    try:
        (R/'REVIEW_PENDING').unlink()
        with (O/'watchdog.console').open('x')as f:subprocess.Popen([sys.executable,'-B',str(C/'campaign_watchdog.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='RUNNING',active_run=str(O),active_window=window,active_entrypoint=str(C/'campaign.py'));dump(R/'CURRENT_EXPERIMENT.json',current)
        while True:
            action=decision(tasks,finished,repeats,remaining(window),source_ok=frozen_ok())
            if action['action']!='RUN':stop_reason=action.get('reason',action['action']);break
            task=next(t for t in tasks if t['task_id']==action['task_id']);entry=dict(task_id=task['task_id'])
            finished.append(entry);dump(O/'RESULTS.json',finished)
            def child(kind,script,cap):
                nonlocal active
                log=O/(task['task_id']+'_'+kind+'.console')
                with log.open('x')as f:
                    active=subprocess.Popen([str(R/'run_phase.sh'),str(C/script),str(C/('TASK_'+task['task_id']+'.json'))],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
                    dump(O/'ACTIVE.json',dict(pid=active.pid,proc_start=Path('/proc',str(active.pid),'stat').read_text().split()[21],kind=kind,task_id=task['task_id']))
                    try:return active.wait(timeout=cap)
                    except subprocess.TimeoutExpired:terminate(active);raise TimeoutError(kind+'_WALL_CAP')
                    finally:
                        if active.poll()is None:terminate(active)
                        active=None;dump(O/'ACTIVE.json',dict(closed=True))
            entry['worker_returncode']=child('worker','worker.py',min(1505,max(1,remaining(window)-5)))
            output=Path(task['output'])
            entry['result']=read(output/'RESULT.json')if(output/'RESULT.json').exists()else dict(passed=False,models=None,new_actual_native=None,own_replay_native=None,error='MISSING_RESULT_COUNTS_UNKNOWN')
            if entry['worker_returncode']==0:
                entry['audit_returncode']=child('audit','native_audit_cli.py',180)
                entry['audit']=read(output/'FINAL_INDEPENDENT_AUDIT.json')if(output/'FINAL_INDEPENDENT_AUDIT.json').exists()else dict(passed=False,error='MISSING_INDEPENDENT_AUDIT')
            if entry.get('audit',{}).get('passed')and task['role']=='repeat':
                repeats[str(task['slot'])]=compare_repeat(task);dump(O/('REPEAT_slot'+str(task['slot']).zfill(2)+'.json'),repeats[str(task['slot'])])
            dump(O/'RESULTS.json',finished)
    except BaseException as exc:
        error=dict(error=repr(exc),traceback=traceback.format_exc());stop_reason='FIRST_DRIVER_OR_EVIDENCE_FAILURE'
        if active is not None:terminate(active)
    finally:
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True))
        (R/'REVIEW_PENDING').write_bytes(guard)
        def count(key):
            values=[r.get('result',{}).get(key)for r in finished]
            return sum(values)if all(type(v)is int for v in values)and error is None else None
        complete=dict(closed=True,passed=stop_reason=='TWO_EXPOSED_SLOTS_MAIN_REPEAT_AUDITED',stop_reason=stop_reason,error=error,stages=finished,repeats=repeats,
            unexecuted=[t['task_id']for t in tasks if t['task_id']not in [r['task_id']for r in finished]],
            models=count('models'),new_actual_native=count('new_actual_native'),own_replay_native=count('own_replay_native'),
            new24_executed=False,same_version_three_routes_passed=False,guard_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66')
        dump(O/'COMPLETION.json',complete);dump(O/'LEDGER.json',complete)
        current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_v1204_physical=complete);dump(R/'CURRENT_EXPERIMENT.json',current)
    return 0 if complete['passed']else 1


if __name__=='__main__':sys.exit(main())
