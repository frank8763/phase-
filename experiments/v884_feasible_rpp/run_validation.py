"""Not invoked during preparation. Explicit new user90min approval is required."""
import argparse,fcntl,hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v884_feasible_rpp'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import file_sha,verify_sources,require
from authority import SCOPE,digest,authorized
GUARD_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
def dump(p,d):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--user-approved-new90min',action='store_true');args=parser.parse_args()
    require(args.user_approved_new90min,'NEW_USER_WINDOW_APPROVAL_REQUIRED')
    freeze=file_sha(C/'SOURCE_FREEZE.json');verify_sources(R,C/'SOURCE_FREEZE.json')
    qualified=json.loads((O/'ZERO_MODEL_RELEASE.json').read_text())
    require(qualified.get('passed')is True and qualified.get('source_freeze_sha256')==freeze,'QUALIFIED_SOURCE_MISMATCH')
    require(json.loads((O/'ZERO_QUALIFICATION.json').read_text())['passed']and json.loads((O/'ENTRY_QUALIFICATION.json').read_text())['passed'],'ZERO_QUALIFICATION_REQUIRED')
    guard=(R/'REVIEW_PENDING').read_bytes();require(hashlib.sha256(guard).hexdigest()==GUARD_SHA,'GUARD_CHANGED')
    lock=(O/'validation.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not(O/'AUTHORIZATION.json').exists()and not(O/'COMPLETION.json').exists(),'ALREADY_ATTEMPTED_NO_RESTART')
    execution=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(execution,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(execution,fcntl.LOCK_UN)
    started=time.time();deadline=started+5400.
    root=dict(models_authorized=True,user_approved_new90min=True,scope=SCOPE,started_unix=started,deadline_unix=deadline,source_freeze_sha256=freeze)
    with(O/'AUTHORIZATION.json').open('x')as f:json.dump(root,f,indent=2)
    dump(O/'ROUND_WINDOW.json',root);rows=[];child=None;error=None;status='NOT_PASSED'
    current_path=R/'CURRENT_EXPERIMENT.json';current=json.loads(current_path.read_text());current.update(status='RUNNING_V884_LIMITED_NS_VALIDATION',active_run=str(O.relative_to(R)),active_window=root,execution_window_closed=False);dump(current_path,current)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('EXTERNAL_STOP_NO_RESTART')))
    try:
        for task in json.loads((C/'TASKS.json').read_text()):
            verify_sources(R,C/'SOURCE_FREEZE.json');require(deadline-time.time()>=300,'INSUFFICIENT_REMAINING_TIME')
            total=0
            for base in [R/'runs/v856_nav2_foundation',R/'runs/v858_nav2_verified',R/'runs/v881_timing_accounting_continuation',O]:
                if base.exists():total+=sum(p.lstat().st_size for p in base.rglob('*')if p.is_file()and not p.is_symlink())
            require(total<1536*1024**2,'2GIB_TEMP_RESERVE_STOP')
            receipt=dict(root,run_id=task['run_id'],task_sha256=digest(task));authorized(task,receipt,time.time(),freeze)
            tp=O/(task['task_id']+'.task.json');ap=O/(task['task_id']+'.authorization.json');dump(tp,task);dump(ap,receipt);dump(O/'ACTIVE.json',dict(task=task,started_unix=time.time(),deadline_unix=deadline))
            with(O/(task['task_id']+'.console')).open('w')as f:
                child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
                child.wait(timeout=min(250,deadline-3-time.time()));code=child.returncode;child=None
            p=Path(task['output']);n=json.loads((p/'RESULT.json').read_text())if(p/'RESULT.json').exists()else{}
            a=json.loads((p/'INDEPENDENT_AUDIT.json').read_text())if(p/'INDEPENDENT_AUDIT.json').exists()else{}
            rows.append(dict(task_id=task['task_id'],returncode=code,passed=bool(a.get('passed')),actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'),output=task['output']));dump(O/'RESULTS.json',rows)
            require(code==0 and a.get('passed')is True,'FIRST_FUNCTIONAL_RUNTIME_OR_EVIDENCE_FAILURE')
        old=R/'experiments/v881_timing_accounting_continuation/audit.py';spec=importlib.util.spec_from_file_location('v884_same_config_repeat',old);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        comparison=m.repeat_check(rows[0]['output'],rows[1]['output']);dump(O/'REPEAT_COMPARISON.json',comparison);require(comparison['passed'],'COMPLETE_REPEAT_FAILED');status='LIMITED_NS_RUNTIME_VALIDATION_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=7)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        # Re-read actual evidence even if the launcher was interrupted: no zero inference.
        for task in json.loads((C/'TASKS.json').read_text()):
            p=Path(task['output'])
            if not p.exists()or any(x['task_id']==task['task_id']for x in rows):continue
            n=json.loads((p/'RESULT.json').read_text())if(p/'RESULT.json').exists()else{}
            rows.append(dict(task_id=task['task_id'],passed=False,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),output=task['output']))
        (R/'REVIEW_PENDING').write_bytes(guard)
        completion=dict(closed=True,status=status,error=error,started_unix=started,deadline_unix=deadline,closed_unix=time.time(),rows=rows,attempted_navigation=len(rows),unexecuted_navigation=2-len(rows),dynamic_navigation=0,new24_executed=0,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,models_authorized=False)
        dump(O/'COMPLETION.json',completion)
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,execution_window_closed=True,v884_feasible_rpp=dict(status=status,closed=True,models_authorized=False,deadline_unix=deadline,completion=str((O/'COMPLETION.json').relative_to(R)),rows=rows,dynamic_navigation=0,new24_executed=0));dump(current_path,current)
        with(O/'finalize.console').open('w')as f:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
    return 0 if status=='LIMITED_NS_RUNTIME_VALIDATION_PASSED'else 1
if __name__=='__main__':sys.exit(main())
