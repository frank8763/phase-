"""Four fixed diagnostic branches, one model at a time, hard20:00 stop."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v993_steering_transient_diagnosis';ROOT=R/'runs/daytime_20261110_until20'
sys.path.insert(0,str(C));from authority import authorized,END
from audit import audit
def dump(p,x):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);authorized()
    with(O/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time(),absolute_deadline_unix=END),f)
    guard=(R/'REVIEW_PENDING').read_bytes();rows=[];child=None;error=None
    dump(ROOT/'LEDGER.json',dict(status='FIXED_DIAGNOSTICS_RUNNING',absolute_deadline_unix=END,diagnostic_started=True,candidate_started=False))
    state=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());state.update(status='V993_DIAGNOSTIC_RUNNING',active_run=str(O.relative_to(R)),active_window=dict(deadline_unix=END),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',state)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('ROOT_STOP')))
    try:
        for task in json.loads((C/'TASKS.json').read_text()):
            authorized(task);assert time.time()<END-320,'INSUFFICIENT_TASK_TIME'
            path=O/(task['run_id']+'.TASK.json');dump(path,task)
            dump(O/'ACTIVE.json',dict(slot=task['slot'],name=task['name'],at=time.time()))
            log=O/(task['run_id']+'.console')
            with log.open('x')as stream:
                (R/'REVIEW_PENDING').unlink()
                child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(path)],cwd=R,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                rc=child.wait(timeout=min(310,END-time.time()-5));child=None
            (R/'REVIEW_PENDING').write_bytes(guard)
            out=Path(task['output'])
            lines=[s[len('PHASE_DIAGNOSTIC_RESULT '):]for s in log.read_text().splitlines()if s.startswith('PHASE_DIAGNOSTIC_RESULT ')]
            assert len(lines)==1,'WORKER_RESULT_MISSING_COUNTS_UNKNOWN'
            result=json.loads(lines[0]);proof=audit(task)if rc==0 else dict(passed=False,error=result.get('error'))
            row=dict(slot=task['slot'],name=task['name'],output=task['output'],passed=rc==0 and proof['passed'],
                result=result,audit=proof);rows.append(row);dump(O/'RESULTS.json',rows)
            assert row['passed'],'FIRST_DIAGNOSTIC_SAFETY_STATE_CONTROL_EVIDENCE_FAILURE'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=max(.01,min(20,END-time.time()-1)))
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        passed=error is None and len(rows)==4 and all(x['passed']for x in rows)
        done=dict(closed=True,diagnostic_evidence_passed=passed,navigation_passed=False,rows=rows,error=error,
            closed_unix=time.time(),absolute_deadline_unix=END,models_authorized=False,unexecuted_slots=list(range(len(rows),4)))
        dump(O/'COMPLETION.json',done)
        dump(ROOT/'LEDGER.json',dict(status='DIAGNOSTICS_COMPLETE_CANDIDATE_NOT_STARTED'if passed else'STOPPED_DIAGNOSTIC_FAILURE',
            absolute_deadline_unix=END,diagnostic_started=True,candidate_started=False,model_authority_for_unprepared_source=False))
        state.update(status='REVIEW_PENDING',source_revision='V993_DIAGNOSTIC_CLOSED',active_run=None,active_window=None,next_physical_authorized=False,
            v993_diagnostic_summary=dict(passed=passed,rows=len(rows),error=error,deadline_unix=END));dump(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
