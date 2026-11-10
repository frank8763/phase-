"""Two fixed components, finally restores guard and closes dependencies on failure."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1003_causal_recovery_execution';ROOT=R/'runs/input_consistent_overnight_20261110'
sys.path.insert(0,str(C))
from authority import authorize,read
from audit import audit
def dump(p,x):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);end=authorize()
    with(O/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time()),f)
    guard=(ROOT/'REVIEW_PENDING.before').read_bytes();assert(R/'REVIEW_PENDING').read_bytes()==guard
    rows=[];error=None;child=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('ROOT_STOP')))
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='V1003_TWO_PLANNED_INPUT_COMPONENTS_RUNNING',active_run=str(O.relative_to(R)),active_window=read(ROOT/'ROUND_WINDOW.json'),next_physical_authorized=True)
    dump(R/'CURRENT_EXPERIMENT.json',state)
    try:
        for task in read(C/'TASKS.json'):
            authorize(task);path=O/(task['run_id']+'.TASK.json');dump(path,task);dump(O/'ACTIVE.json',dict(slot=task['slot'],name=task['name'],at=time.time()))
            with(O/(task['run_id']+'.console')).open('x')as stream:
                (R/'REVIEW_PENDING').unlink();child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(path)],cwd=R,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                rc=child.wait(timeout=min(430,end-time.time()-5));child=None
            (R/'REVIEW_PENDING').write_bytes(guard)
            lines=[x[len('PHASE_RECOVERY_COMPONENT_RESULT '):]for x in(O/(task['run_id']+'.console')).read_text().splitlines()if x.startswith('PHASE_RECOVERY_COMPONENT_RESULT ')]
            assert len(lines)==1,'WORKER_RESULT_MISSING_COUNTS_UNKNOWN'
            n=json.loads(lines[0]);proof=audit(task)if rc==0 else dict(passed=False,error=n.get('error'))
            row=dict(slot=task['slot'],name=task['name'],output=task['output'],passed=rc==0 and proof['passed'],result=n,audit=proof)
            rows.append(row);dump(O/'RESULTS_PHYSICAL.json',rows)
            assert row['passed'],'FIRST_FUNCTION_SAFETY_STATE_CONTROL_OR_EVIDENCE_FAILURE'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=max(.01,min(15,end-time.time()-1)))
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        passed=error is None and len(rows)==2 and all(x['passed']for x in rows)
        done=dict(closed=True,passed=passed,rows=rows,error=error,closed_unix=time.time(),unexecuted_slots=list(range(len(rows),2)),navigation_passed=False,model_authority=False)
        dump(O/'COMPLETION.json',done)
        if not passed:dump(ROOT/'MODEL_STOP.json',dict(reason='FIRST_COMPONENT_FAILURE',at=time.time(),error=error))
        dump(ROOT/'LEDGER.json',dict(status='TWO_COMPONENTS_PASSED_NAVIGATOR_GATE_REQUIRED'if passed else'STOPPED_COMPONENT_FAILURE',root_window=read(ROOT/'ROUND_WINDOW.json'),components_passed=passed,confirmation_started=False))
        state.update(status='REVIEW_PENDING',active_run=None,active_window=None,next_physical_authorized=False,source_revision='V1003_COMPONENT_STAGE_CLOSED',v1003_summary=dict(passed=passed,rows=len(rows),error=error,navigation_executed=0))
        dump(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
