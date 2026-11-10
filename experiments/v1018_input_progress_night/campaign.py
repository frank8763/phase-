"""Offline sequential three-route branches, one frozen scientific version."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1018_input_progress_night';ROOT=R/'runs/input_progress_night_20261110'
sys.path.insert(0,str(C))
from authority import root_authorized,authorized,read,sha,digest
from budget import CAMPAIGN_WAIT_S
from branch_policy import skip_repeat,can_confirm,failure_action
def dump(p,x):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def cache_size():
    roots=[R/'runs/v1016_saved_route_diagnosis',R/'runs/v1017_input_validated_progress',R/'runs/v858_nav2_verified/v1015',R/'runs/atomic_handoff_entry_20261110',R/'runs/atomic_handoff_night_20261110',R/'runs/v1014_atomic_handoff_navigation',R/'runs/v858_nav2_verified/v1014',ROOT,R/'runs/v1002_causal_response_predictor',R/'runs/v1003_causal_recovery_execution',O,R/'runs/v858_nav2_verified/v1003',R/'runs/v858_nav2_verified/v1018']
    return sum(p.stat().st_size for root in roots for base,dirs,names in os.walk(root,followlinks=False)for p in [Path(base)/n for n in names]if not p.is_symlink())
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);auth=root_authorized();tasks=read(C/'TASKS.json');guard=(ROOT/'REVIEW_PENDING.before').read_bytes()
    with(O/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time(),absolute_deadline=1794358800.),f)
    rows=[];screens=[];child=None;error=None;status='NOT_PASSED'
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('ROOT_STOP')))
    if not auth['conditional_overnight']:tasks=tasks[:2]
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='V1018_CHECKER_VALID_PATH_RUNNING',active_run=str(O.relative_to(R)),active_window=auth,next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',current)
    def receipt(task):return dict(auth,run_id=task['run_id'],task_sha256=digest(task))
    def preflights(selected):
        nonlocal child
        from preflight_audit import audit
        for task in selected:
            end=authorized(task,receipt(task),time.time(),auth['source_freeze_sha256'],preflight=True);assert time.time()<end-75
            assert cache_size()<2*1024**3-256*1024**2,'CACHE_RESERVE_EXHAUSTED'
            tp=O/(task['task_id']+'.PREFLIGHT_TASK.json');ap=O/(task['task_id']+'.PREFLIGHT_AUTH.json');dump(tp,task);dump(ap,receipt(task))
            with(O/(task['task_id']+'.preflight.console')).open('x')as log:
                (R/'REVIEW_PENDING').unlink();child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'t0_worker.py').relative_to(R)),str(tp),str(ap)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                code=child.wait(timeout=min(70.,end-time.time()-5));child=None
            (R/'REVIEW_PENDING').write_bytes(guard);assert code==0,'TRUE_T0_PREFLIGHT_FAILURE_COUNTS_SEE_OUTPUT'
            screens.append(audit([task]));dump(O/'PREFLIGHTS.json',screens)
    try:
        all_tasks=read(C/'TASKS.json')
        from preflight_audit import audit as audit_reused
        reused=audit_reused([all_tasks[0],all_tasks[2],all_tasks[4]]);assert reused['passed']
        screens.append(dict(reused_original_true_t0=True,new_model_initializations=0,original_saved_audit=reused));dump(O/'PREFLIGHTS.json',screens)
        for task in tasks:
            if skip_repeat(task,rows):
                rows.append(dict(task_id=task['task_id'],slot=task['slot'],stage=task['stage'],route=task['route'],passed=False,executed=False,reason='MAIN_FUNCTION_FAILED_REPEAT_UNEXECUTED',actual_native=0,replay_native=0,private_native=0));dump(O/'RESULTS.json',rows);continue
            if task['slot']==6 and not can_confirm(rows):
                status='THREE_ROUTE_DEVELOPMENT_NOT_PASSED';break
            if task['slot']==6:
                assert all(x['passed']for x in rows[:6])and time.time()<=1794358800.-9000.,'NO_FULL_CONFIRMATION_WINDOW'
                preflights(tasks[6:30])
            if task['slot']==30:
                main=rows[6:30];assert len(main)==24 and sum(x['passed']for x in main)>=23
                for route in ['we','ns','ew']:assert sum(x['passed']for x in main if x['route']==route)>=7
                for direction in [-1,1]:assert sum(x['passed']for x in main if x['initial_axis_direction']==direction)>=11
                assert all(rows[i]['passed']for i in [6,14,22]),'FIXED_REPEAT_BASELINE_FAILED'
            end=authorized(task,receipt(task),time.time(),auth['source_freeze_sha256']);assert time.time()<end-365
            assert cache_size()<2*1024**3-256*1024**2,'CACHE_RESERVE_EXHAUSTED'
            tp=O/(task['task_id']+'.TASK.json');ap=O/(task['task_id']+'.AUTH.json');dump(tp,task);dump(ap,receipt(task))
            dump(O/'ACTIVE.json',dict(task_id=task['task_id'],slot=task['slot'],at=time.time(),deadline=end));dump(ROOT/'LEDGER.json',dict(status='NAVIGATING',task_id=task['task_id'],completed=len(rows),deadline=end))
            with(O/(task['task_id']+'.console')).open('x')as log:
                child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                code=child.wait(timeout=min(CAMPAIGN_WAIT_S,end-time.time()-5));child=None
            out=Path(task['output']);a=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{};n=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{}
            passed=code==0 and a.get('passed')is True
            if passed and task['role']=='dynamic_repeat':
                from repeat_contract import repeat_check
                repeat=repeat_check(task['baseline_output'],task['output']);dump(out/'REPEAT_AUDIT.json',repeat);passed=repeat['passed']
                if not passed:a['evidence_passed']=False  # repeat model/initial-state contract failure stops all
            row=dict(task_id=task['task_id'],slot=task['slot'],stage=task['stage'],route=task['route'],initial_axis_direction=task.get('initial_axis_direction'),passed=passed,executed=True,
                evidence_passed=a.get('evidence_passed')is True and code in (0,1) and (not a.get('passed')or code==0),output=task['output'],actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),
                goal_m=n.get('goal_distance_m'),minimum_clearance_m=a.get('minimum_clearance_m'),error=a.get('error')or n.get('error'))
            rows.append(row);dump(O/'RESULTS.json',rows)
            action=failure_action(task,row,rows)
            if action.startswith('STOP_'):raise AssertionError(action)
        else:status='FIXED24_AND_THREE_REPEATS_PASSED'if auth['conditional_overnight']else'WEST_EAST_MAIN_AND_REPEAT_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=max(.01,min(45.,1794358800.-time.time()-1.)))
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        approval=read(ROOT/'APPROVAL.json');approval.update(models_authorized=False,closed_unix=time.time());dump(ROOT/'APPROVAL.json',approval)
        done=dict(closed=True,status=status,error=error,rows=rows,preflight_summaries=screens,unexecuted_tasks=[x['task_id']for x in tasks if not any(row['task_id']==x['task_id']and row.get('executed',True)for row in rows)],
            models_authorized=False,closed_unix=time.time(),absolute_deadline_unix=1794358800.,prerequisite_deadline_unchanged=auth['precondition_deadline_unix'],new24_executed=sum(x['stage']=='confirmation'for x in rows))
        dump(O/'COMPLETION.json',done);dump(ROOT/'COMPLETION.json',dict(done,model_authority=False));dump(ROOT/'LEDGER.json',dict(status='CLOSED_'+status,models_authorized=False,stop_reason=error or status))
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,next_physical_authorized=False,source_revision='V1018_CLOSED',v1018_summary=done);dump(R/'CURRENT_EXPERIMENT.json',current)
        with(ROOT/'finalize.console').open('x')as log:
            try:subprocess.run([sys.executable,'-B',str(C/'close.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
            except BaseException as e:dump(ROOT/'FINALIZE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True,no_model_restart=True))
    return 0 if status in ['FIXED24_AND_THREE_REPEATS_PASSED','WEST_EAST_MAIN_AND_REPEAT_PASSED']else 1
if __name__=='__main__':sys.exit(main())
