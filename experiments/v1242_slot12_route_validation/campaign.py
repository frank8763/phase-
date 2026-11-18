from campaign_context import *
from gates import main_gate,final_gate
import subprocess,signal,fcntl,traceback
repeat_check=load('v1242_original_repeat',R/'experiments/v1180_fresh_recovery_chain/campaign.py').repeat_check
def main():
    assert not(O/'DRIVER_STARTED.json').exists()and read(O/'APPROVAL.json')['models_authorized']and source_ok()
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD
    lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    tasks=read(C/'TASKS.json');stages=[];pairs={};devpairs={};child=None;error=None;reason='SLOT12_MAIN_REPEAT_DEVELOPMENT_COMPLETE';passed=False;functional_failures=0
    def stop():
        nonlocal child
        if child and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def halt(*_):raise TimeoutError('V1242_ROOT_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
    def job(name,script,task,seconds,physical):
        nonlocal child
        assert source_ok()and remaining()>seconds+30
        used_bytes=used();assert used_bytes+256*1024**2<2*1024**3,'TEMPORARY_2GIB_CAP'
        assert(R/'REVIEW_PENDING').read_bytes()==guard
        command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json'))]if physical else[sys.executable,'-B',str(C/script),str(C/('TASK_'+task['task_id']+'.json'))]
        if physical:(R/'REVIEW_PENDING').unlink()
        try:
            with(O/(name+'.console')).open('x')as log:
                child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True);dump(O/'ACTIVE.json',dict(stage=name,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=physical));return child.wait(timeout=min(seconds,remaining()-15))
        finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
    try:
        for task in tasks:
            if task['role']=='t0' and not (len([r for r in stages if r['role'].startswith('development_')])==4 and len(devpairs)==2 and all(p['passed']for p in devpairs.values()) and all(r['functional_passed'] and r['safety_evidence_passed'] for r in stages if r['role'].startswith('development_'))):reason='DEVELOPMENT_GATE_NOT_PASSED';break
            if task['role']=='repeat'and not main_gate(stages)['passed']:reason='MAIN_24_GATE_NOT_PASSED_NO_REPEATS';break
            if task['role']=='repeat' and not any(r['role']=='main' and r['slot']==task['slot'] and r['functional_passed'] and r['safety_evidence_passed'] for r in stages):reason='FIXED_REPEAT_BASELINE_FAILED_NO_SUBSTITUTE';break
            if task['role']=='main' and sum(r['role']=='t0' and r['functional_passed'] and r['safety_evidence_passed'] for r in stages)!=24:reason='ALL24_T0_REQUIRED';break
            required=200 if task['role']=='t0'else 1900
            if remaining()<required:reason='INSUFFICIENT_REMAINING_FOR_COMPLETE_TASK_AUDIT';break
            row=dict(stage=task['task_id'],role=task['role'],slot=task['slot'],case_id=task['case_id'],direction=task['initial_axis_motion_direction'],result=None,audit=None,functional_passed=False,safety_evidence_passed=False);stages.append(row);dump(O/'RESULTS.json',stages)
            row['returncode']=job(task['task_id'],'t0.py'if task['role']=='t0'else'worker.py',task,125 if task['role']=='t0'else 1510,True)
            p=Path(task['output'])/'RESULT.json';row['result']=read(p)if p.exists()else None;rr=row['result'];dump(O/'RESULTS.json',stages)
            refusal=bool(rr and rr.get('functional_failure')and rr.get('error')is None and rr.get('replay',{}).get('passed'))
            if not rr or rr.get('error')or(row['returncode']!=0 and not refusal):reason='FIRST_SAFETY_EVIDENCE_OR_OPERATION_EXCEPTION';break
            if not rr['passed']and not refusal:reason='FIRST_UNCLASSIFIED_FUNCTIONAL_OR_SAFETY_FAILURE';break
            script='t0_audit.py'if task['role']=='t0'else'audit_refusal.py'if refusal else'audit.py'
            row['audit_returncode']=job(task['task_id']+'_audit',script,task,30 if task['role']=='t0'else 310,False);p=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=read(p)if p.exists()else None
            row['safety_evidence_passed']=bool(row['audit_returncode']==0 and row['audit']and row['audit']['passed']);row['functional_passed']=bool(rr['passed']);dump(O/'RESULTS.json',stages);dump(O/'PROGRESS.json',dict(active_stage=task['task_id'],main=main_gate(stages),t0_passed=sum(r['role']=='t0'and r['safety_evidence_passed']for r in stages),complete_repeats=pairs))
            if not row['safety_evidence_passed']:reason='FIRST_INDEPENDENT_AUDIT_FAILURE';break
            if (rr.get('functional_failure')or{}).get('reason')=='OBSERVER_CERTIFIED_STOP_COMPLETED':reason='CERTIFIED_BACKUP_STOP_NOT_GOAL';break
            if task['role'].startswith('development_') and not row['functional_passed']:reason='FIRST_DEVELOPMENT_FUNCTIONAL_FAILURE';break
            if task['role']=='development_repeat':
                baseline=next(t for t in tasks if t['task_id']==task['baseline_id']);pair=repeat_check(baseline['output'],task['output']);devpairs[task['pair_key']]=pair;dump(O/(task['pair_key']+'_REPEAT.json'),pair)
                if not pair['passed']:reason='DEVELOPMENT_REPEAT_FAILED';break
            if task['role']=='main'and not row['functional_passed']:
                functional_failures+=1
                if functional_failures>=2:reason='SECOND_FUNCTIONAL_FAILURE_FIXED_POOL_STOP';break
            if task['role']=='repeat':
                main=next(t for t in tasks if t['role']=='main'and t['slot']==task['slot']);pairs[str(task['slot'])]=repeat_check(main['output'],task['output']);dump(O/'COMPLETE_REPEATS.json',pairs)
                if not pairs[str(task['slot'])]['passed']or not row['functional_passed']:reason='FIXED_REPEAT_FAILED_NO_SUBSTITUTE';break
        else:passed=bool(len(stages)==2 and all(s['functional_passed']and s['safety_evidence_passed']for s in stages)and len(devpairs)==1 and all(p['passed']for p in devpairs.values()))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());reason='DRIVER_EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
        for row in stages:
            if row['result']is None:
                task=next(t for t in tasks if t['task_id']==row['stage']);p=Path(task['output'])/'RESULT.json'
                if p.exists():row['result']=read(p)
        def total(k):return sum(s['result'][k]for s in stages)if all(s.get('result')and s['result'].get(k)is not None for s in stages)else None
        summary=dict(closed=True,passed=passed,fixed24_confirmation_passed=False,slot12_main_repeat_development_passed=passed,main_gate=main_gate(stages),stop_reason=reason,error=error,stages=stages,development_repeats=devpairs,complete_repeats=pairs,physical_counts={k:total(k)for k in['models','historical_reconstruction_native','new_actual_native','total_actual_model_native','own_replay_native','analytical_cpp_native','analytical_python_native']},unexecuted=[t['task_id']for t in tasks if t['task_id']not in[s['stage']for s in stages]],guard_original=sha(R/'REVIEW_PENDING')==GUARD,source_unchanged=source_ok(),old_pool_exposed=True,formal_retained_commit=False,closed_unix=time.time())
        dump(O/'ACTIVE.json',dict(closed=True));dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
        with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        print(json.dumps({k:v for k,v in summary.items()if k in['closed','passed','stop_reason','main_gate','physical_counts','unexecuted']}))
if __name__=='__main__':main()
