"""Offline fixed-deadline chain. No runtime repair, fallback candidate or model retry."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v971_night_entry_continuation'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import root_authorized,read,sha,digest
from handshake import verify_sources
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');q.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    a=root_authorized();assert not(O/'CAMPAIGN_CLAIM.json').exists(),'NO_RESTART'
    dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),at=time.time(),deadline_unix=a['deadline_unix']))
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    child=None;rows=[];error=None;status='NOT_PASSED';current=read(R/'CURRENT_EXPERIMENT.json');tasks=read(C/'TASKS.json')
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('NIGHT_STOP_NO_RESTART')))
    def launch(cmd,label,limit,model=False):
        nonlocal child
        assert time.time()+limit+30<a['deadline_unix'],'HARD_DEADLINE_NO_CHILD_TIME'
        size=sum(p.stat().st_size for folder in [O,R/'runs/v858_nav2_verified/v968']for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
        assert size<2*1024**3-200*1024**2,'BOUNDED_2GIB_CACHE_STOP'
        verify_sources(R,C/'SOURCE_FREEZE.json');dump(O/'ACTIVE.json',dict(stage=label,at=time.time(),deadline_unix=a['deadline_unix']))
        current.update(status='V971_REMAINING_NIGHT_RUNNING',active_stage=label,active_run=str(O.relative_to(R)),active_window=a,execution_window_closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
        if model:(R/'REVIEW_PENDING').unlink()
        try:
            with(O/(label+'.console')).open('x')as f:
                child=subprocess.Popen(cmd,cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
                dump(O/'WORKER.json',dict(pid=child.pid,stage=label));rc=child.wait(timeout=limit);child=None
        finally:
            if child is not None and child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
                child=None
            (R/'REVIEW_PENDING').write_bytes(guard)
        return rc
    def receipt(t):
        tp=O/(t['run_id']+'.task.json');ap=O/(t['run_id']+'.authorization.json');dump(tp,t);dump(ap,dict(a,run_id=t['run_id'],task_sha256=digest(t)));return tp,ap
    def navigation(t,strict=True):
        tp,ap=receipt(t);rc=launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],t['run_id'],290)
        p=Path(t['output']);n=read(p/'RESULT.json')if(p/'RESULT.json').exists()else{};aud=read(p/'INDEPENDENT_AUDIT.json')if(p/'INDEPENDENT_AUDIT.json').exists()else{}
        row=dict(task_id=t['task_id'],run_id=t['run_id'],stage=t['stage'],slot=t.get('slot'),route=t['route'],direction=t.get('initial_axis_direction'),output=t['output'],
            passed=bool(rc==0 and aud.get('passed')),evidence_passed=aud.get('evidence_passed'),functional_passed=aud.get('functional_passed'),
            actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'))
        rows.append(row);dump(O/'RESULTS.json',rows)
        assert aud.get('evidence_passed')is True and n.get('status')=='NATIVE_COMPLETE','FIRST_SAFETY_SOURCE_STATE_CONTROL_COVERAGE_OR_EVIDENCE_FAILURE '+t['run_id']
        if strict:assert row['passed'],'FIRST_FUNCTIONAL_FAILURE '+t['run_id']
        if t['role']=='dynamic_repeat':
            from repeat_contract import repeat_check
            check=repeat_check(t['baseline_output'],t['output']);dump(O/(t['run_id']+'.REPEAT.json'),check);assert check['passed'],'REPEAT_CONTRACT_FAILED'
        return row
    def preflight(group,items):
        unique={t['preflight_output']:t for t in items if t['role']!='dynamic_repeat'}
        for t in unique.values():
            tp,ap=receipt(t);rc=launch([str(R/'run_phase.sh'),str((C/'t0_worker.py').relative_to(R)),str(tp),str(ap)],t['run_id']+'-t0',70,model=True);assert rc==0,'TRUE_T0_FAILED'
        from preflight_audit import audit
        check=audit(list(unique.values()));dump(O/(group+'_PREFLIGHT_AUDIT.json'),check);assert check['passed']
    try:
        assert read(O/'SAVED_HANDOFF_ANCHOR.json')['saved_second_stage_passed']
        dump(O/'COMPONENT_GATE.json',dict(passed=True,scope='User-approved route development from saved second-stage evidence, original whole component NOT_PASSED; not a regrading',new_component_models=0))
        we=[]
        for t in[t for t in tasks if t['stage']=='we_development']:we.append(navigation(t))
        dump(O/'WE_GATE.json',dict(passed=True,rows=we))
        reg=[t for t in tasks if t['stage']=='regression'];preflight('REGRESSION',reg);regrows=[]
        for t in reg:regrows.append(navigation(t))
        dump(O/'REGRESSION_GATE.json',dict(passed=True,current_WE=we,NS_EW=regrows,same_frozen_science=True))
        assert a['deadline_unix']-time.time()>=9000,'INSUFFICIENT_FULL_CONFIRMATION_WINDOW_NO_START'
        confirm=[t for t in tasks if t['stage']=='confirmation'];preflight('CONFIRMATION',confirm);mainrows=[];failed=0
        for t in confirm:
            row=navigation(t,strict=False);mainrows.append(row);failed+=not row['passed'];assert failed<2,'SECOND_CONFIRMATION_FUNCTIONAL_FAILURE'
        gates=dict(all24=len(mainrows)==24,overall=sum(t['passed']for t in mainrows)>=23,
            routes=all(sum(t['passed']for t in mainrows if t['route']==r)>=7 for r in ['we','ns','ew']),
            directions=all(sum(t['passed']for t in mainrows if t['direction']==d)>=11 for d in [-1,1]))
        dump(O/'CONFIRMATION_MAIN_GATE.json',dict(passed=all(gates.values()),checks=gates,rows=mainrows));assert all(gates.values())
        for t in[t for t in tasks if t['stage']=='confirmation_repeat']:navigation(t)
        status='FINITE_FIXED24_DYNAMIC_AND_REPEATS_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        (R/'REVIEW_PENDING').write_bytes(guard);(O/'AUTHORIZATION.before_close.json').write_bytes((O/'AUTHORIZATION.json').read_bytes());dump(O/'AUTHORIZATION.json',dict(a,models_authorized=False,closed_unix=time.time()))
        d=dict(closed=True,status=status,error=error,rows=rows,models_authorized=False,started_unix=a['started_unix'],deadline_unix=a['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,
            confirmation_executed=sum(r['stage']=='confirmation'for r in rows),confirmation_unexecuted=24-sum(r['stage']=='confirmation'for r in rows),unexecuted_tasks=len(tasks)-len(rows))
        dump(O/'COMPLETION.json',d);current.update(status='REVIEW_PENDING',active_stage=None,active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True,next_physical_authorized=False,v971_entry=d);dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'close.console').open('x')as f:
            try:subprocess.run([sys.executable,'-B',str(C/'close.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=480,check=True)
            except BaseException as e:dump(O/'CLOSE_ERROR.json',dict(error=repr(e),models=0))
    return 0 if status=='FINITE_FIXED24_DYNAMIC_AND_REPEATS_PASSED'else 1
if __name__=='__main__':sys.exit(main())
