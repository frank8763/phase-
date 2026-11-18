"""At most two fresh original slot17 navigations, first failure closes."""
from campaign_context import *
import fcntl,signal,subprocess,traceback
repeat_check=load('phase_v1271_original_pair_verifier',R/'experiments/v1180_fresh_recovery_chain/campaign.py').repeat_check
def main():
    assert not(O/'DRIVER_STARTED.json').exists()and read(O/'APPROVAL.json')['models_authorized']and source_ok()
    assert read(O/'QUALIFICATION.json')['passed']and read(O/'ISOLATED_QUALIFICATION.json')['passed']
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD
    lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    tasks=read(C/'TASKS.json');stages=[];pairs={};child=None;error=None;reason='JOINT_PHASE_18_19_MAIN_REPEATS_COMPLETE';passed=False
    def stop():
        nonlocal child
        if child and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def halt(*_):raise TimeoutError('V1271_ROOT_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
    def job(name,script,task,seconds):
        nonlocal child
        assert source_ok()and remaining()>seconds+30 and used()+256*1024**2<LIMIT
        assert(R/'REVIEW_PENDING').read_bytes()==guard
        command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json'))]
        (R/'REVIEW_PENDING').unlink()
        try:
            with(O/(name+'.console')).open('x')as log:
                child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
                dump(O/'ACTIVE.json',dict(stage=name,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=script=='worker.py'))
                return child.wait(timeout=min(seconds,remaining()-15))
        finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
    try:
        for task in tasks:
            assert task['role']in['development_main','development_repeat']
            if task['role']=='development_repeat'and not(stages and stages[-1]['slot']==task['slot']and stages[-1]['functional_passed']and stages[-1]['safety_evidence_passed']):reason='MAIN_GATE_FAILED_NO_REPEAT';break
            if remaining()<1900:reason='INSUFFICIENT_REMAINING_FOR_COMPLETE_TASK_AUDIT';break
            row=dict(stage=task['task_id'],role=task['role'],slot=task['slot'],case_id=task['case_id'],result=None,audit=None,functional_passed=False,safety_evidence_passed=False);stages.append(row);dump(O/'RESULTS.json',stages)
            row['returncode']=job(task['task_id'],'worker.py',task,1510)
            path=Path(task['output'])/'RESULT.json';row['result']=read(path)if path.exists()else None;r=row['result'];dump(O/'RESULTS.json',stages)
            refusal=bool(r and r.get('functional_failure')and r.get('error')is None and r.get('replay',{}).get('passed'))
            if not r or r.get('error')or(row['returncode']!=0 and not refusal):reason='FIRST_SAFETY_EVIDENCE_OR_OPERATION_EXCEPTION';break
            if not r['passed']and not refusal:reason='FIRST_UNCLASSIFIED_FUNCTIONAL_FAILURE';break
            row['audit_returncode']=job(task['task_id']+'_audit','audit.py',task,310)
            path=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=read(path)if path.exists()else None
            row['functional_passed']=bool(r['passed']);row['safety_evidence_passed']=bool(row['audit_returncode']==0 and row['audit']and row['audit']['passed']);dump(O/'RESULTS.json',stages)
            if not row['safety_evidence_passed']:reason='FIRST_INDEPENDENT_AUDIT_FAILURE';break
            if not row['functional_passed']:reason='FIRST_SAFE_STOPPED_FUNCTIONAL_REFUSAL';break
            if task['role']=='development_repeat':
                baseline=next(a for a in tasks if a['task_id']==task['baseline_id']);pair=repeat_check(baseline['output'],task['output']);pairs[task['pair_key']]=pair;dump(O/(task['pair_key']+'_REPEAT.json'),pair)
                if not pair['passed']:reason='COMPLETE_REPEAT_FAILED';break
        else:passed=bool(len(stages)==4 and all(s['functional_passed']and s['safety_evidence_passed']for s in stages)and set(pairs)=={'slot18','slot19'}and all(a['passed']for a in pairs.values()))
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());reason='DRIVER_EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        auth=read(O/'AUTHORIZATION.json');auth.update(authorized=False,closed=True);dump(O/'AUTHORIZATION.json',auth)
        def total(k):return sum(s['result'][k]for s in stages)if all(s.get('result')and s['result'].get(k)is not None for s in stages)else None
        summary=dict(closed=True,passed=passed,joint_phase_main_repeat_development_passed=passed,fixed24_confirmation_passed=False,
            stop_reason=reason,error=error,stages=stages,development_repeats=pairs,
            physical_counts={k:total(k)for k in['models','historical_reconstruction_native','new_actual_native','total_actual_model_native','own_replay_native','analytical_cpp_native','analytical_python_native']},
            unexecuted=[t['task_id']for t in tasks if t['task_id']not in[s['stage']for s in stages]],guard_original=sha(R/'REVIEW_PENDING')==GUARD,
            source_unchanged=source_ok(),old_pool_exposed=True,formal_retained_commit=False,closed_unix=time.time())
        dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
        with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        print(json.dumps({k:summary[k]for k in['closed','passed','stop_reason','physical_counts','unexecuted']}))
if __name__=='__main__':main()
