"""Offline single-candidate campaign, absolute 90-minute window, no model restarts or tuning."""
import fcntl,hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v901_arm_ack_continuation';REC=R/'records/nav2_v901_20261109'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import SCOPE,digest
from handshake import verify_sources,file_sha
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def stop(p):
    if p is None or p.poll()is not None:return
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def bytes_now():
    total=0
    for base in [O,R/'runs/v858_nav2_verified/v901']:
        for path,dirs,files in os.walk(base,followlinks=False):
            dirs[:]=[d for d in dirs if not(Path(path)/d).is_symlink()]
            total+=sum((Path(path)/n).lstat().st_size for n in files if not(Path(path)/n).is_symlink())
    return total
def main():
    assert '--start-frozen'in sys.argv
    lock=(O/'night.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    auth=json.loads((O/'AUTHORIZATION.json').read_text());assert auth['deadline_unix']-auth['started_unix']==5400. and auth['models_authorized']is True
    assert not(O/'NIGHT_CLAIM.json').exists()and not(O/'COMPLETION.json').exists(),'ALREADY_ATTEMPTED'
    verify_sources(R,C/'SOURCE_FREEZE.json');sha=file_sha(C/'SOURCE_FREEZE.json');assert json.loads((O/'ZERO_MODEL_RELEASE.json').read_text())['passed']
    guard=(O/'REVIEW_PENDING.before').read_bytes();assert (R/'REVIEW_PENDING').read_bytes()==guard
    dump(O/'NIGHT_CLAIM.json',dict(pid=os.getpid(),entrypoint=str(Path(__file__).resolve()),started_unix=time.time(),deadline_unix=auth['deadline_unix'],no_restart=True))
    tasks=json.loads((C/'TASKS.json').read_text());rows=[];preflights=json.loads((O/'PREFLIGHTS.json').read_text());child=None;inhibitor=None;status='NOT_PASSED';error=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('NIGHT_STOP_NO_RESTART')))
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='V901_TERMINAL_SET_RUNNING',active_run=str(O.relative_to(R)),active_window=auth,execution_window_closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
    try:
        # OS sleep inhibition wraps a separate fail-closed registered-process watchdog.
        f=(O/'watchdog.console').open('w')
        inhibitor=subprocess.Popen(['systemd-inhibit','--what=sleep:idle:handle-lid-switch','--mode=block','--who=Phase','--why=Frozen bounded offline Phase navigation',sys.executable,'-B',str(C/'watchdog.py'),'--owner',str(os.getpid())],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        time.sleep(.4);assert inhibitor.poll()is None,'SLEEP_INHIBITOR_OR_WATCHDOG_FAILED'
        dump(O/'OS_GUARD.json',dict(pid=inhibitor.pid,owner_pid=os.getpid(),fixed_deadline_unix=auth['deadline_unix'],offline=True))
        for task in [*[t for t in tasks if t['role']=='dynamic_t0'],*[t for t in tasks if t['role']!='dynamic_t0']]:
            assert auth['deadline_unix']-time.time()>300,'INSUFFICIENT_REMAINING_WINDOW'
            assert bytes_now()<auth['raw_cache_limit_bytes']-200*1024**2,'BOUNDED_CACHE_RESERVE_STOP'
            verify_sources(R,C/'SOURCE_FREEZE.json');receipt=dict(auth,scope=SCOPE,run_id=task['run_id'],task_sha256=digest(task),source_freeze_sha256=sha)
            tp=O/(task['task_id']+'.task.json');ap=O/(task['task_id']+'.authorization.json');dump(tp,task);dump(ap,receipt)
            dump(O/'ACTIVE.json',dict(task=task,started_unix=time.time(),deadline_unix=auth['deadline_unix']))
            with(O/(task['task_id']+'.console')).open('w')as log:
                if task['role']=='dynamic_t0':
                    (R/'REVIEW_PENDING').unlink();cmd=[str(R/'run_phase.sh'),str((C/'preflight_worker.py').relative_to(R)),str(tp),str(ap)];limit=95
                else:cmd=[sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)];limit=250
                child=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                dump(O/'ACTIVE_LAUNCHER.json',dict(pid=child.pid,task_id=task['task_id'],command=cmd))
                child.wait(timeout=min(limit,auth['deadline_unix']-5-time.time()));rc=child.returncode;child=None
            (R/'REVIEW_PENDING').write_bytes(guard)
            out=Path(task['output'])
            if task['role']=='dynamic_t0':
                proof=json.loads((out/'PREFLIGHT_RESULT.json').read_text());preflights[task['case_id']]=proof;dump(O/'PREFLIGHTS.json',preflights);assert rc==0 and proof['passed'],'FIRST_T0_FAILURE'
            else:
                n=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else{}
                a=json.loads((out/'INDEPENDENT_AUDIT.json').read_text())if(out/'INDEPENDENT_AUDIT.json').exists()else{}
                rows.append(dict(task_id=task['task_id'],passed=rc==0 and a.get('passed')is True,returncode=rc,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'),output=task['output']));dump(O/'RESULTS.json',rows)
                assert rows[-1]['passed'],'FIRST_FUNCTIONAL_SAFETY_SOURCE_OR_EVIDENCE_FAILURE'
                if task['role']=='dynamic_repeat':
                    from repeat_contract import repeat_check
                    comparison=repeat_check(out.parent/('main_'+task['route']),out);dump(O/('REPEAT_'+task['route']+'.json'),comparison);assert comparison['passed'],'COMPLETE_REPEAT_FAILED'
        status='THREE_ROUTE_DYNAMIC_DEVELOPMENT_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        stop(child);(R/'REVIEW_PENDING').write_bytes(guard)
        for task in tasks:
            out=Path(task['output'])
            if task['role']=='dynamic_t0'or not out.exists()or any(x['task_id']==task['task_id']for x in rows):continue
            n=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else{}
            rows.append(dict(task_id=task['task_id'],passed=False,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),output=task['output']))
        done=dict(closed=True,status=status,models_authorized=False,deadline_unix=auth['deadline_unix'],closed_unix=time.time(),rows=rows,attempted_navigation=len(rows),unexecuted_navigation=6-len(rows),preflight_cases=list(preflights),new24=0,error=error,source_freeze_sha256=sha,guard_restored=True)
        dump(O/'COMPLETION.json',done);current.update(status='REVIEW_PENDING',active_run=None,active_window=None,execution_window_closed=True,v901_terminal_set=done);dump(R/'CURRENT_EXPERIMENT.json',current)
        # Zero-model finalization after the model group has stopped, bounded to180s.
        with(O/'finalize.console').open('w')as f:
            try:subprocess.run([sys.executable,'-B',str(C/'finalize_night.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
            except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),models=0,no_model_restart=True))
        stop(inhibitor)
    return 0 if status=='THREE_ROUTE_DYNAMIC_DEVELOPMENT_PASSED'else 1
if __name__=='__main__':sys.exit(main())
