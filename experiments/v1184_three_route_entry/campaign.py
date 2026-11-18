from route_tools import *
import subprocess,signal,fcntl,traceback
repeat_check=load('v1184_original_repeat_audit',R/'experiments/v1180_fresh_recovery_chain/campaign.py').repeat_check
def main():
    assert not(O/'DRIVER_STARTED.json').exists() and not(O/'COMPLETION.json').exists() and read(O/'APPROVAL.json')['models_authorized'] and source_ok()
    assert read(O/'QUALIFICATION.json')['passed'] and read(O/'ISOLATED_QUALIFICATION.json')['passed']
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD
    lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    tasks=read(C/'TASKS.json');stages=[];pairs={};child=None;error=None;reason='SIX_FRESH_NAVIGATIONS_COMPLETE';passed=False
    def stop():
        nonlocal child
        if child and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def halt(*_):raise TimeoutError('V1184_ROOT_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
    def job(name,script,task,seconds,physical):
        nonlocal child
        assert source_ok() and remaining()>seconds+30
        roots=[O,R/'runs/v858_nav2_verified/v1184'];used=sum(p.stat().st_size for root in roots if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink());assert used+256*1024**2<2*1024**3
        assert (R/'REVIEW_PENDING').read_bytes()==guard
        command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json'))]if physical else[sys.executable,'-B',str(C/script),str(C/('TASK_'+task['task_id']+'.json'))]
        if physical:(R/'REVIEW_PENDING').unlink()
        try:
            with(O/(name+'.console')).open('x')as log:
                child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
                dump(O/'ACTIVE.json',dict(stage=name,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=physical));return child.wait(timeout=min(seconds,remaining()-15))
        finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
    try:
        for task in tasks:
            if remaining()<1900:reason='INSUFFICIENT_REMAINING_FOR_COMPLETE_WORKER_AUDIT';break
            row=dict(stage=task['task_id'],case_id=task['case_id'],result=None,audit=None);stages.append(row);dump(O/'RESULTS.json',stages)
            row['returncode']=job(task['task_id'],'worker.py',task,1510,True);p=Path(task['output'])/'RESULT.json';row['result']=read(p)if p.exists()else None;dump(O/'RESULTS.json',stages)
            if row['returncode']!=0 or not row['result'] or not row['result']['passed']:reason='FIRST_NATIVE_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';break
            row['audit_returncode']=job(task['task_id']+'_audit','audit.py',task,310,False);p=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=read(p)if p.exists()else None;dump(O/'RESULTS.json',stages)
            if row['audit_returncode']!=0 or not row['audit']or not row['audit']['passed']:reason='FIRST_INDEPENDENT_ACTUAL_AUDIT_FAILURE';break
            if task['role']=='repeat':
                main=next(t for t in tasks if t['case_id']==task['case_id']and t['role']=='main');pairs[task['case_id']]=repeat_check(main['output'],task['output']);dump(O/'COMPLETE_REPEATS.json',pairs)
                if not pairs[task['case_id']]['passed']:reason='COMPLETE_REPEAT_MISMATCH';break
        else:passed=len(pairs)==3 and all(p['passed']for p in pairs.values())
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());reason='DRIVER_EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        for row in stages:
            if row['result']is None:
                t=next(t for t in tasks if t['task_id']==row['stage']);p=Path(t['output'])/'RESULT.json'
                if p.exists():row['result']=read(p)
        def total(k):return sum(s['result'][k]for s in stages)if all(s.get('result')and s['result'].get(k)is not None for s in stages)else None
        summary=dict(closed=True,passed=passed,same_version_three_routes_passed=passed,stop_reason=reason,error=error,stages=stages,complete_repeats=pairs,physical_counts={k:total(k)for k in ['models','historical_reconstruction_native','new_actual_native','total_actual_model_native','own_replay_native','analytical_cpp_native','analytical_python_native']},unexecuted=[t['task_id']for t in tasks if t['task_id']not in[s['stage']for s in stages]],guard_original=sha(R/'REVIEW_PENDING')==GUARD,source_unchanged=source_ok(),new24=False,formal_retained_commit=False,closed_unix=time.time())
        dump(O/'ACTIVE.json',dict(closed=True));dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
        with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        print(json.dumps({k:v for k,v in summary.items()if k in ['closed','passed','stop_reason','physical_counts','unexecuted']}))
if __name__=='__main__':main()
