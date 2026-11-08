"""One renewed user continuation, same standing90min preference; no old window reuse."""
import argparse,fcntl,hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v892_dynamic_terminal_consistency'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import file_sha,verify_sources,require
from authority import SCOPE,digest,authorized
GUARD_SHA='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
def dump(p,d):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--user-requested-dynamic-stage',action='store_true');args=parser.parse_args()
    require(args.user_requested_dynamic_stage,'DYNAMIC_STAGE_INSTRUCTION_REQUIRED')
    approval=json.loads((O/'USER_APPROVAL.json').read_text());require(approval.get('latest_user_continuation')is True and approval.get('standing_window_choice')=='新独立90分钟：原西向东动态主任务，成功后完整重复，首失败即停','EXPLICIT_CONTINUATION_AND_STANDING_BOUND_REQUIRED')
    freeze=file_sha(C/'SOURCE_FREEZE.json');verify_sources(R,C/'SOURCE_FREEZE.json')
    qualified=json.loads((O/'ZERO_MODEL_RELEASE.json').read_text())
    require(qualified.get('passed')is True and qualified.get('source_freeze_sha256')==freeze,'QUALIFIED_SOURCE_MISMATCH')
    require(json.loads((O/'ENTRY_QUALIFICATION.json').read_text())['passed'],'ZERO_QUALIFICATION_REQUIRED')
    guard=(R/'REVIEW_PENDING').read_bytes();require(hashlib.sha256(guard).hexdigest()==GUARD_SHA,'GUARD_CHANGED')
    lock=(O/'validation.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not(O/'AUTHORIZATION.json').exists()and not(O/'COMPLETION.json').exists(),'ALREADY_ATTEMPTED_NO_RESTART')
    execution=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(execution,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(execution,fcntl.LOCK_UN)
    started=time.time();deadline=started+json.loads((C/'WINDOW_POLICY.json').read_text())['maximum_duration_s'];require(deadline-started==5400,'NEW90MIN_REQUIRED')
    root=dict(models_authorized=True,user_requested_dynamic_stage=True,user_approved_new90min=True,scope=SCOPE,started_unix=started,deadline_unix=deadline,source_freeze_sha256=freeze)
    with(O/'AUTHORIZATION.json').open('x')as f:json.dump(root,f,indent=2)
    dump(O/'ROUND_WINDOW.json',root);rows=[];child=None;error=None;status='NOT_PASSED'
    current_path=R/'CURRENT_EXPERIMENT.json';current=json.loads(current_path.read_text());current.update(status='RUNNING_V892_SINGLE_ACTOR_DYNAMIC',active_run=str(O.relative_to(R)),active_window=root,execution_window_closed=False);dump(current_path,current)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('EXTERNAL_STOP_NO_RESTART')))
    try:
        task=json.loads((C/'TASKS.json').read_text())[0];receipt=dict(root,run_id=task['run_id'],task_sha256=digest(task));authorized(task,receipt,time.time(),freeze)
        tp=O/'t0_we.task.json';ap=O/'t0_we.authorization.json';dump(tp,task);dump(ap,receipt);dump(O/'ACTIVE.json',dict(task=task,started_unix=time.time(),deadline_unix=deadline))
        (R/'REVIEW_PENDING').unlink()
        with(O/'t0_we.console').open('w')as f:
            child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'preflight_worker.py').relative_to(R)),str(tp),str(ap)],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            child.wait(timeout=min(90,deadline-30-time.time()));code=child.returncode;child=None
        (R/'REVIEW_PENDING').write_bytes(guard)
        p=Path(task['output'])/'PREFLIGHT_RESULT.json';preflight=json.loads(p.read_text())if p.exists()else dict(passed=False,environment_initializations_attempted=1,environment_initializations_completed=None,native_integrations=None,reason='MISSING_T0_RESULT_COUNTS_UNKNOWN')
        dump(O/'PREFLIGHTS.json',preflight);require(code==0 and preflight.get('passed')is True,'FIRST_DYNAMIC_T0_FAILURE')
        for task in json.loads((C/'TASKS.json').read_text())[1:]:
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
            if task['task_id'].startswith('repeat_'):
                from repeat_contract import repeat_check;comparison=repeat_check(rows[-2]['output'],rows[-1]['output']);dump(O/'REPEAT_COMPARISON.json',comparison);require(comparison['passed'],'MODEL_INITIAL_STATE_OR_COMPLETE_REPEAT_FAILED')
        status='SINGLE_ACTOR_DYNAMIC_DEVELOPMENT_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=7)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        # Re-read actual evidence even if the launcher was interrupted: no zero inference.
        for task in json.loads((C/'TASKS.json').read_text())[1:]:
            p=Path(task['output'])
            if not p.exists()or any(x['task_id']==task['task_id']for x in rows):continue
            n=json.loads((p/'RESULT.json').read_text())if(p/'RESULT.json').exists()else{}
            rows.append(dict(task_id=task['task_id'],passed=False,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),output=task['output']))
        (R/'REVIEW_PENDING').write_bytes(guard)
        completion=dict(closed=True,status=status,error=error,started_unix=started,deadline_unix=deadline,closed_unix=time.time(),rows=rows,attempted_navigation=len(rows),unexecuted_navigation=2-len(rows),dynamic_navigation=len(rows),new24_executed=0,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,models_authorized=False)
        dump(O/'COMPLETION.json',completion)
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,execution_window_closed=True,v892_dynamic_terminal_consistency=dict(status=status,closed=True,models_authorized=False,deadline_unix=deadline,completion=str((O/'COMPLETION.json').relative_to(R)),rows=rows,dynamic_navigation=len(rows),new24_executed=0));dump(current_path,current)
        with(O/'finalize.console').open('w')as f:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
    return 0 if status=='SINGLE_ACTOR_DYNAMIC_DEVELOPMENT_PASSED'else 1
if __name__=='__main__':sys.exit(main())
