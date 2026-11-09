"""Immutable bounded chain; runs without network, never repairs or retries models."""
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v963_continuous_dynamic'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import root_authorized,sha,digest,read
from handshake import verify_sources
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');t.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    auth=root_authorized();assert not(O/'CAMPAIGN_CLAIM.json').exists()
    dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),at=time.time(),deadline_unix=auth['deadline_unix']))
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    current=read(R/'CURRENT_EXPERIMENT.json');child=None;rows=[];night_rows=[];error=None;night_error=None;status='NOT_PASSED';night_status='NOT_STARTED'
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('CAMPAIGN_TERMINATED_NO_RESTART')))
    def set_active(stage):
        dump(O/'ACTIVE.json',dict(stage=stage,at=time.time(),deadline_unix=auth['deadline_unix']))
        current.update(status='V963_BOUNDED_CHAIN_RUNNING',active_run=str(O.relative_to(R)),active_window=auth,execution_window_closed=False,active_stage=stage)
        dump(R/'CURRENT_EXPERIMENT.json',current)
    def launch(cmd,label,limit,model=False):
        nonlocal child
        assert time.time()+limit+30<auth['deadline_unix'],'INSUFFICIENT_BOUNDED_CHILD_TIME'
        folders=[O,*[R/'runs/v858_nav2_verified'/x for x in ['v962','v963','v965','v966']]]
        size=sum(p.stat().st_size for folder in folders for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
        assert size<2*1024**3-200*1024**2,'TEMP_CACHE_2GIB_BUDGET_STOP'
        verify_sources(R,C/'SOURCE_FREEZE.json');set_active(label)
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
    def receipt(task):
        tp=O/(task['run_id']+'.task.json');ap=O/(task['run_id']+'.authorization.json')
        dump(tp,task);dump(ap,dict(auth,run_id=task['run_id'],task_sha256=digest(task)));return tp,ap
    def navigation(task,destination):
        tp,ap=receipt(task)
        rc=launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['run_id'],290)
        out=Path(task['output']);n=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{}
        a=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{}
        row=dict(task_id=task['task_id'],run_id=task['run_id'],stage=task['stage'],slot=task.get('slot'),route=task['route'],direction=task.get('initial_axis_direction'),
            passed=bool(rc==0 and a.get('passed')),functional_passed=a.get('functional_passed'),evidence_passed=a.get('evidence_passed'),
            actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m'),output=task['output'])
        destination.append(row);dump(O/('NIGHT_RESULTS.json'if task.get('campaign')=='night'else'RESULTS.json'),destination)
        # A failed prefix is never treated as a functional-only failed arrival.
        assert a.get('evidence_passed')is True and n.get('status')=='NATIVE_COMPLETE','FIRST_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE '+task['run_id']
        return row
    def repeat(task,row):
        assert row['passed'],'FIRST_FUNCTIONAL_FAILURE '+task['run_id']
        from repeat_contract import repeat_check
        out=Path(task['output']);baseline=Path(task.get('baseline_output',str(out.parent/'main_we')))
        comparison=repeat_check(baseline,out);dump(O/(task['run_id']+'.REPEAT.json'),comparison);assert comparison['passed'],'REPEAT_FAILED'
    def preflights(tasks,group):
        unique={t['preflight_output']:t for t in tasks if t['role']!='dynamic_repeat'}
        for t in unique.values():
            tp,ap=receipt(t);rc=launch([str(R/'run_phase.sh'),str((C/'t0_worker.py').relative_to(R)),str(tp),str(ap)],t['run_id']+'-t0',70,model=True)
            assert rc==0,'TRUE_T0_PREFLIGHT_FAILED '+t['run_id']
        from preflight_audit import audit
        proof=audit(list(unique.values()));dump(O/(group+'_PREFLIGHT_AUDIT.json'),proof);assert proof['passed']
    def close_current():
        dump(O/'COMPLETION.json',dict(closed=True,status=status,rows=rows,error=error,unexecuted_navigation=2-len(rows),
            models_authorized=False,started_unix=auth_current['started_unix'],deadline_unix=auth_current['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,new24=0))
        (O/'AUTHORIZATION.before_close.json').write_bytes((O/'AUTHORIZATION.json').read_bytes())
        dump(O/'AUTHORIZATION.json',dict(auth_current,models_authorized=False,closed_unix=time.time()))
    auth_current=auth.copy()
    try:
        rc=launch([str(R/'run_phase.sh'),'experiments/v962_continuous_handoff/worker.py'],'handoff',110,model=True)
        sys.path.insert(0,str(R/'experiments/v953_stop_align_components'));from result_contract import read_parent
        component=read_parent(O/'handoff.console',R/'runs/v858_nav2_verified/v962/handoff_left');dump(O/'HANDOFF_RESULT.json',component)
        # Always independently examine the saved physical component, including failure.
        audit_rc=launch([sys.executable,'-B',str(R/'experiments/v962_continuous_handoff/audit.py')],'handoff-audit',40)
        assert rc==audit_rc==0 and read(O/'HANDOFF_AUDIT.json')['passed'],'FIRST_HANDOFF_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE'
        sys.path.insert(0,str(C))
        for task in read(C/'TASKS.json'):
            row=navigation(task,rows);assert row['passed'],'FIRST_FUNCTIONAL_FAILURE '+task['run_id']
            if task['role']=='dynamic_repeat':repeat(task,row)
        status='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED';close_current()
        plan=read(C/'NIGHT_PLAN.json');assert 300<plan['deadline_unix']-time.time()<=43200.,'NO_NIGHT_TIME_LEFT'
        start=time.time();auth=dict(auth_current,scope=auth_current['scope']+'_NIGHT',started_unix=start,deadline_unix=plan['deadline_unix'],
            models_authorized=True,interpretation='User approved same-version three-route regression then fixed24; absolute08:00 stop; no repair/retry.',max_navigation=31)
        with(O/'NIGHT_AUTHORIZATION.json').open('x')as f:json.dump(auth,f,indent=2)
        dump(O/'NIGHT_ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=plan['deadline_unix']))
        night_status='NOT_PASSED';alltasks=read(C/'NIGHT_TASKS.json');reg=[t for t in alltasks if t['stage']=='regression']
        preflights(reg,'REGRESSION')
        for task in reg:
            row=navigation(task,night_rows);assert row['passed'],'FIRST_REGRESSION_FUNCTIONAL_FAILURE'
            if task['role']=='dynamic_repeat':repeat(task,row)
        dump(O/'NIGHT_REGRESSION_GATE.json',dict(passed=True,current_WE_main_repeat=rows,new_NS_EW_main_repeat=night_rows.copy(),same_science=True))
        assert auth['deadline_unix']-time.time()>=plan['minimum_confirmation_remaining_s'],'INSUFFICIENT_FULL_CONFIRMATION_TIME_NO_START'
        main=[t for t in alltasks if t['stage']=='confirmation'];preflights(main,'CONFIRMATION');failed=0;mainrows=[]
        for task in main:
            row=navigation(task,night_rows);mainrows.append(row);failed+=not row['passed']
            assert failed<2,'SECOND_CONFIRMATION_FUNCTIONAL_FAILURE'
        checks=dict(all24_executed=len(mainrows)==24,overall=sum(r['passed']for r in mainrows)>=23,
            routes=all(sum(r['passed']for r in mainrows if r['route']==route)>=7 for route in ['we','ns','ew']),
            directions=all(sum(r['passed']for r in mainrows if r['direction']==direction)>=11 for direction in [-1,1]))
        dump(O/'CONFIRMATION_MAIN_GATE.json',dict(passed=all(checks.values()),checks=checks,rows=mainrows));assert all(checks.values())
        for task in [t for t in alltasks if t['stage']=='confirmation_repeat']:
            row=navigation(task,night_rows);repeat(task,row)
        night_status='FIXED24_DYNAMIC_CONFIRMATION_AND_THREE_REPEATS_PASSED'
    except BaseException as e:
        detail=dict(error=repr(e),traceback=traceback.format_exc())
        if status=='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED':night_error=detail
        else:error=detail
    finally:
        (R/'REVIEW_PENDING').write_bytes(guard)
        if not(O/'COMPLETION.json').exists():close_current()
        if(O/'NIGHT_AUTHORIZATION.json').exists():
            original=read(O/'NIGHT_AUTHORIZATION.json');(O/'NIGHT_AUTHORIZATION.before_close.json').write_bytes((O/'NIGHT_AUTHORIZATION.json').read_bytes())
            dump(O/'NIGHT_AUTHORIZATION.json',dict(original,models_authorized=False,closed_unix=time.time()))
        dump(O/'NIGHT_COMPLETION.json',dict(closed=True,status=night_status,error=night_error,rows=night_rows,models_authorized=False,
            deadline_unix=read(C/'NIGHT_PLAN.json')['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,
            confirmation_executed=sum(r['stage']=='confirmation'for r in night_rows),confirmation_unexecuted=24-sum(r['stage']=='confirmation'for r in night_rows)))
        current.update(status='REVIEW_PENDING',active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True,
            next_physical_authorized=False,v963_result=read(O/'COMPLETION.json'),v963_night_result=read(O/'NIGHT_COMPLETION.json'))
        dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'close.console').open('x')as f:
            try:subprocess.run([sys.executable,'-B',str(R/'experiments/v964_continuous_closure/close.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=480,check=True)
            except BaseException as e:dump(O/'CLOSE_ERROR.json',dict(error=repr(e),models=0))
    return 0 if night_status=='FIXED24_DYNAMIC_CONFIRMATION_AND_THREE_REPEATS_PASSED'else 1
if __name__=='__main__':sys.exit(main())
