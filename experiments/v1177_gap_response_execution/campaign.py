from gap_tools import *
import subprocess,signal,fcntl,traceback,gzip
def repeat_check(a,b):
    a,b=Path(a),Path(b);maximum=0.;same=True
    with np.load(a/'physics/NATIVE_TRACE.npz')as x,np.load(b/'physics/NATIVE_TRACE.npz')as y:
        for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:
            if x[k].shape!=y[k].shape:same=False;continue
            if x[k].size:maximum=max(maximum,float(abs(x[k]-y[k]).max()))
    with np.load(a/'physics/INITIAL_STATE.npz')as x,np.load(b/'physics/INITIAL_STATE.npz')as y:initial=x['state'].shape==y['state'].shape and float(abs(x['state']-y['state']).max())<=1e-8
    identical=True
    for file in ['CONTACTS.json.gz','SENSORS.json.gz']:
        with gzip.open(a/'physics'/file,'rt')as x,gzip.open(b/'physics'/file,'rt')as y:identical&=json.load(x)==json.load(y)
    model=sha(a/'physics/scene_model.mjb')==sha(b/'physics/scene_model.mjb');ra,rb=read(a/'RESULT.json'),read(b/'RESULT.json')
    return dict(passed=bool(same and maximum<=1e-8 and initial and identical and model and ra['passed']and rb['passed']),maximum_complete_state_ctrl_error=maximum,same_lengths=same,initial_same=bool(initial),model_same=model,sensors_contacts_same=identical)
def main():
    assert not(O/'DRIVER_STARTED.json').exists()and not(O/'COMPLETION.json').exists()and read(O/'APPROVAL.json')['models_authorized']and source_ok()
    guard=(O/'GUARD.bin').read_bytes();assert hashlib.sha256(guard).hexdigest()==GUARD
    lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dump(O/'DRIVER_STARTED.json',dict(pid=os.getpid(),proc_start=Path('/proc/self/stat').read_text().split()[21]))
    tasks=read(C/'TASKS.json');stages=[];pairs=[];child=None;error=None;reason='FIXED_THREE_COMPONENT_QUEUE_COMPLETE';passed=False
    def stop():
        nonlocal child
        if child and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=5)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def halt(*_):raise TimeoutError('V1177_ROOT_ABSOLUTE_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
    def job(name,script,task,seconds,physical):
        nonlocal child
        assert source_ok()and remaining()>seconds+30
        roots=[O,R/'runs/v858_nav2_verified/v1177'];used=sum(p.stat().st_size for root in roots if root.exists()for p in root.rglob('*')if p.is_file()and not p.is_symlink());assert used+128*1024**2<2*1024**3
        assert (R/'REVIEW_PENDING').read_bytes()==guard
        command=[str(R/'run_phase.sh'),str((C/script).relative_to(R)),str(C/('TASK_'+task['task_id']+'.json'))]if physical else[sys.executable,'-B',str(C/script),str(C/('TASK_'+task['task_id']+'.json'))]
        if physical:(R/'REVIEW_PENDING').unlink()
        try:
            with(O/(name+'.console')).open('x')as log:
                child=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True);dump(O/'ACTIVE.json',dict(stage=name,pid=child.pid,proc_start=Path('/proc',str(child.pid),'stat').read_text().split()[21],physical=physical));return child.wait(timeout=min(seconds,remaining()-15))
        finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
    try:
        assert all(read(O/n)['passed']for n in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','LAUNCH_QUALIFICATION.json'])
        for task in tasks:
            if remaining()<1150:reason='INSUFFICIENT_REMAINING_FOR_COMPLETE_WORKER_AND_AUDIT';break
            row=dict(stage=task['task_id'],result=None,audit=None);stages.append(row);dump(O/'RESULTS.json',stages)
            row['returncode']=job(task['task_id'],'worker.py',task,910,True);p=Path(task['output'])/'RESULT.json';row['result']=read(p)if p.exists()else None;dump(O/'RESULTS.json',stages)
            rr=row['result']
            # A functional failed component may still have a complete safe tail
            # and exact replay. Audit its recorded prefix without advancing queue.
            if rr and rr.get('error')is None and rr.get('evidence_saved')and rr.get('replay',{}).get('passed'):
                row['audit_returncode']=job(task['task_id']+'_audit','audit.py',task,190,False);p=Path(task['output'])/'FINAL_INDEPENDENT_AUDIT.json';row['audit']=read(p)if p.exists()else None;dump(O/'RESULTS.json',stages)
            if row['returncode']!=0 or not rr or not rr['passed']:reason='FIRST_COMPONENT_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE';break
            if not row['audit']or not row['audit']['passed']:reason='FIRST_INDEPENDENT_ACTUAL_AUDIT_FAILURE';break
            if task['role']=='repeat':
                first=next(t for t in tasks if t['component']==task['component']and t['role']=='main');pair=repeat_check(first['output'],task['output']);pairs.append(dict(component=task['component'],**pair));dump(O/'COMPLETE_REPEATS.json',pairs)
                if not pair['passed']:reason='COMPLETE_REPEAT_MISMATCH';break
        else:passed=len(pairs)==3 and all(p['passed']for p in pairs)
    except BaseException as exc:error=dict(error=repr(exc),traceback=traceback.format_exc());reason='DRIVER_EXCEPTION_OR_DEADLINE';dump(O/'ERROR.json',error)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);signal.setitimer(signal.ITIMER_REAL,0)
        for row in stages:
            if row['result']is None:
                t=next(t for t in tasks if t['task_id']==row['stage']);p=Path(t['output'])/'RESULT.json'
                if p.exists():row['result']=read(p)
        def total(k):return sum(r['result'][k]for r in stages)if all(r.get('result')and r['result'].get(k)is not None for r in stages)else None
        summary=dict(closed=True,passed=passed,stop_reason=reason,error=error,stages=stages,complete_repeats=pairs,physical_counts={k:total(k)for k in ['models','new_actual_native','own_replay_native','analytical_cpp_native','analytical_python_native']},independent_audit_analytical_cpp_native=sum(r['audit']['analytical_cpp_native']for r in stages if r.get('audit')),unexecuted=[t['task_id']for t in tasks if t['task_id']not in [r['stage']for r in stages]],guard_original=sha(R/'REVIEW_PENDING')==GUARD,source_unchanged=source_ok(),original_goal_passed=False,new24=False,absolute_deadline_unix=read(O/'ROUND_WINDOW.json')['absolute_deadline_unix'])
        dump(O/'ACTIVE.json',dict(closed=True));dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'COMPLETION.json',summary);dump(O/'LEDGER.json',summary)
        # This is zero-model finalization, not a second science task.
        with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finish.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        print(json.dumps({k:v for k,v in summary.items()if k in ['closed','passed','stop_reason','physical_counts','unexecuted']}))
if __name__=='__main__':main()
