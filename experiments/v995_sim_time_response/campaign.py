"""Four fixed offline tasks, bridge first; never launches an unfrozen candidate."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v995_sim_time_response';ROOT=R/'runs/sim_time_recovery_20261110'
sys.path.insert(0,str(C))
from authority import authorize,read
from audit import audit
from bridge import compare
def dump(p,x):
    p=Path(p);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');tmp.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);end=authorize()
    with(O/'CAMPAIGN_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time(),stage_deadline_unix=end),f)
    guard=(R/'REVIEW_PENDING').read_bytes();rows=[];error=None;child=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('ROOT_OR_STAGE_STOP')))
    state=read(R/'CURRENT_EXPERIMENT.json');state.update(status='V995_SIMULATION_TIME_DIAGNOSTIC_RUNNING',active_run=str(O.relative_to(R)),active_window=read(ROOT/'ROUND_WINDOW.json'),next_physical_authorized=True)
    dump(R/'CURRENT_EXPERIMENT.json',state);dump(ROOT/'LEDGER.json',dict(status='V995_FIXED_DIAGNOSTICS_RUNNING',root_window=read(ROOT/'ROUND_WINDOW.json'),candidate_started=False))
    try:
        for task in read(C/'TASKS.json'):
            authorize(task);path=O/(task['run_id']+'.TASK.json');dump(path,task);dump(O/'ACTIVE.json',dict(slot=task['slot'],name=task['name'],at=time.time()))
            with(O/(task['run_id']+'.console')).open('x')as stream:
                (R/'REVIEW_PENDING').unlink()
                child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(path)],cwd=R,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                rc=child.wait(timeout=min(310,end-time.time()-5));child=None
            (R/'REVIEW_PENDING').write_bytes(guard)
            lines=[x[len('PHASE_DIAGNOSTIC_RESULT '):]for x in(O/(task['run_id']+'.console')).read_text().splitlines()if x.startswith('PHASE_DIAGNOSTIC_RESULT ')]
            assert len(lines)==1,'WORKER_RESULT_MISSING_ACTUAL_COUNTS_UNKNOWN'
            n=json.loads(lines[0]);proof=audit(task)if rc==0 else dict(passed=False,error=n.get('error'))
            if rc==0 and task['slot']==0:
                proof['bridge']=compare(task['output']);proof['passed']=proof['passed']and proof['bridge']['passed']
                dump(Path(task['output'])/'INDEPENDENT_AUDIT.json',proof)
            row=dict(slot=task['slot'],name=task['name'],output=task['output'],passed=rc==0 and proof['passed'],result=n,audit=proof)
            rows.append(row);dump(O/'RESULTS.json',rows)
            assert row['passed'],'DIAGNOSTIC_SOURCE_PHYSICAL_EVIDENCE_OR_BRIDGE_FAILURE'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=max(.01,min(20,end-time.time()-1)))
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        passed=error is None and len(rows)==4 and all(x['passed']for x in rows)
        done=dict(closed=True,diagnostic_evidence_passed=passed,bridge_equivalence_passed=bool(rows and rows[0]['audit'].get('bridge',{}).get('passed')),
            rows=rows,error=error,closed_unix=time.time(),unexecuted_slots=list(range(len(rows),4)),real_time_qualified=False,navigation_passed=False,models_authorized=False)
        dump(O/'COMPLETION.json',done)
        dump(ROOT/'LEDGER.json',dict(status='DIAGNOSTICS_COMPLETE_CANDIDATE_NOT_YET_PREPARED'if passed else'STOPPED_DIAGNOSTIC_FAILURE',root_window=read(ROOT/'ROUND_WINDOW.json'),candidate_started=False,diagnostic_passed=passed,model_authority_for_unprepared_source=False))
        state.update(status='REVIEW_PENDING',active_run=None,active_window=None,next_physical_authorized=False,source_revision='V995_DIAGNOSTIC_CLOSED',
                     v995_summary=dict(passed=passed,rows=len(rows),error=error,real_time_qualified=False))
        dump(R/'CURRENT_EXPERIMENT.json',state)
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
