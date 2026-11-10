"""Frozen order, one native task at a time, automatic fail-closed cleanup."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v985_rear_yaw_components'
sys.path.insert(0,str(C))
from authority import read,digest,root_authorized
def dump(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temporary.replace(path)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    auth=root_authorized();assert not(O/'CAMPAIGN_CLAIM.json').exists()
    dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),at=time.time(),deadline_unix=auth['deadline_unix']))
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    rows=[];child=None;error=None;status='NOT_PASSED';tasks=read(C/'TASKS.json')
    current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='V985_FIXED_COMPONENTS_RUNNING',active_entrypoint=str(C.relative_to(R)/'campaign.py'),active_run=str(O.relative_to(R)),active_window=auth,execution_window_closed=False,next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',current)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('ROOT_STOP')))
    try:
        for task in tasks:
            root_authorized();assert time.time()<auth['deadline_unix']-350,'INSUFFICIENT_TASK_TIME'
            tp=O/(task['task_id']+'.TASK.json');ap=O/(task['task_id']+'.AUTHORIZATION.json')
            dump(tp,task);dump(ap,dict(auth,run_id=task['run_id'],task_sha256=digest(task)))
            dump(O/'ACTIVE.json',dict(task_id=task['task_id'],slot=task['slot'],at=time.time(),deadline_unix=auth['deadline_unix']))
            with(O/(task['task_id']+'.console')).open('x')as stream:
                child=subprocess.Popen([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],cwd=R,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                dump(O/'WORKER.json',dict(task_id=task['task_id'],pid=child.pid))
                rc=child.wait(timeout=min(310,auth['deadline_unix']-time.time()-20));child=None
            out=Path(task['output']);result=read(out/'RESULT.json')if(out/'RESULT.json').exists()else{};audit=read(out/'INDEPENDENT_AUDIT.json')if(out/'INDEPENDENT_AUDIT.json').exists()else{}
            row=dict(task_id=task['task_id'],stage=task['stage'],passed=rc==0 and audit.get('passed')is True,
                     historical_restore_native=result.get('historical_prefix_replay_native')if not result.get('prefix_failure')else result['prefix_failure'].get('historical_restore_native'),
                     new_branch_native=result.get('new_branch_native'),own_full_trace_replay_native=result.get('replay_native'),private_native=0 if result.get('status')is not None else None,
                     output=task['output'],goal_m=result.get('goal_distance_m'),audit_error=audit.get('error'))
            rows.append(row);dump(O/'RESULTS.json',rows)
            assert row['passed'],'FIRST_FUNCTION_SAFETY_SOURCE_STATE_CONTROL_OR_EVIDENCE_FAILURE '+task['task_id']
        status='TWO_FIXED_COMPONENTS_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=max(.01,min(50.,auth['deadline_unix']-time.time()-1.)))
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        (O/'AUTHORIZATION.before_close.json').write_bytes((O/'AUTHORIZATION.json').read_bytes())
        dump(O/'AUTHORIZATION.json',dict(auth,models_authorized=False,closed_unix=time.time()))
        done=dict(closed=True,status=status,error=error,rows=rows,unexecuted_tasks=[t['task_id']for t in tasks[len(rows):]],
                  models_authorized=False,deadline_unix=auth['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,
                  new24=0,automatic_followup=False)
        dump(O/'COMPLETION.json',done);current.update(status='REVIEW_PENDING',source_revision='V985_CLOSED_'+status,active_entrypoint=None,active_run=None,active_window=None,execution_window_closed=True,next_physical_authorized=False,v985_physical_gate=done);dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'finalize.console').open('x')as stream:
            try:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=420)
            except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),models=0,no_model_restart=True))
    return 0 if status=='TWO_FIXED_COMPONENTS_PASSED'else 1
if __name__=='__main__':sys.exit(main())
