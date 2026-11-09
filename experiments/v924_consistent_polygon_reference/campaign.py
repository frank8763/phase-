"""One bounded qualification -> original WE main -> conditional repeat; no tuning."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v924_consistent_polygon_reference'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import root_authorized,digest
from handshake import verify_sources,file_sha
def dump(p,d):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(d,indent=2)+'\n');t.replace(p)
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    sha=file_sha(C/'SOURCE_FREEZE.json');auth=root_authorized(time.time(),sha);verify_sources(R,C/'SOURCE_FREEZE.json')
    assert not(O/'CAMPAIGN_CLAIM.json').exists(),'NO_RESTART'
    dump(O/'CAMPAIGN_CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),deadline_unix=auth['deadline_unix']))
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard)
    child=None;rows=[];status='NOT_PASSED';error=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('CAMPAIGN_STOP')))
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='V924_QUALIFICATION_RUNNING',active_run=str(O.relative_to(R)),active_window=auth,execution_window_closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
    def launch(cmd,label,limit):
        nonlocal child
        assert auth['deadline_unix']-time.time()>limit+30
        size=sum(p.stat().st_size for p in O.rglob('*')if p.is_file() and not p.is_symlink())
        raw=R/'runs/v858_nav2_verified/v924'
        size+=sum(p.stat().st_size for p in raw.rglob('*')if p.is_file() and not p.is_symlink())
        assert size<2*1024**3-200*1024**2,'CACHE_BUDGET'
        verify_sources(R,C/'SOURCE_FREEZE.json');dump(O/'ACTIVE.json',dict(stage=label,at=time.time()))
        with (O/(label+'.console')).open('x')as f:
            child=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            dump(O/'WORKER.json',dict(pid=child.pid,stage=label));rc=child.wait(timeout=limit);child=None
        assert rc==0,'FIRST_QUALIFICATION_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE '+label
    try:
        # Same unchanged vehicle adapter and finite body tube: reuse the archived18
        # physical response qualification, counted as old evidence only.
        prior=json.loads((O/'PRIOR_RESPONSE_QUALIFICATION.json').read_text());assert prior['all18_qualified']
        dump(O/'PLATFORM_RESULT.json',dict(passed=True,reused_old_v909_cases=18,actual_native=0,replay_native=0,private_native=0,scope='No new response models; all body/actuator and tube constants unchanged'))
        for task in json.loads((C/'TASKS.json').read_text()):
            tp=O/(task['task_id']+'.task.json');ap=O/(task['task_id']+'.authorization.json')
            dump(tp,task);dump(ap,dict(auth,run_id=task['run_id'],task_sha256=digest(task)))
            launch([sys.executable,'-B',str(C/'launch_one.py'),str(tp),str(ap)],task['task_id'],260)
            out=Path(task['output']);n=json.loads((out/'RESULT.json').read_text());a=json.loads((out/'INDEPENDENT_AUDIT.json').read_text())
            rows.append(dict(task_id=task['task_id'],passed=a['passed'],actual_native=n['actual_native'],replay_native=n['replay_native'],private_native=n['private_native'],goal_m=n['goal_distance_m']))
            dump(O/'RESULTS.json',rows);assert a['passed']
            if task['role']=='dynamic_repeat':
                from repeat_contract import repeat_check
                comparison=repeat_check(out.parent/'main_we',out);dump(O/'REPEAT.json',comparison);assert comparison['passed']
        status='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        if not(O/'PLATFORM_RESULT.json').exists():
            cases=[json.loads(p.read_text())for p in sorted(O.glob('RESPONSE_*_RESULT.json'))]
            claimed=len(list(O.glob('RESPONSE_*_CLAIM.json')))
            exact=lambda key:None if len(cases)!=claimed or any(x.get(key)is None for x in cases)else sum(x[key]for x in cases)
            dump(O/'PLATFORM_RESULT.json',dict(passed=False,cases=cases,actual_native=exact('actual_native'),replay_native=exact('replay_native'),private_native=0,attempted_cases=claimed,unexecuted_cases=18-claimed))
        for task in json.loads((C/'TASKS.json').read_text()):
            out=Path(task['output'])
            if not out.exists()or any(x['task_id']==task['task_id']for x in rows):continue
            n=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else{}
            rows.append(dict(task_id=task['task_id'],passed=False,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m')))
        d=dict(closed=True,status=status,rows=rows,unexecuted_navigation=2-len(rows),new24=0,error=error,models_authorized=False,deadline_unix=auth['deadline_unix'],closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard)
        dump(O/'RESULTS.json',rows);dump(O/'COMPLETION.json',d)
        current.update(status='REVIEW_PENDING',active_run=None,active_window=None,execution_window_closed=True,v924_consistent_polygon_reference=d);dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'finalize.console').open('w')as f:
            try:subprocess.run([sys.executable,'-B',str(C/'finalize.py')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180,check=True)
            except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),models=0))
    return 0 if status=='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED'else 1
if __name__=='__main__':sys.exit(main())
