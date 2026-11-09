"""Remaining registered work only, same scientific source and original absolute end."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
OPS=Path(__file__).resolve().parent;R=OPS.parents[1];BASE=R/'experiments/v909_timed_command_contract';O=R/'runs/v909_output_continuation';OLD=R/'runs/v909_timed_command_contract';WRITABLE=R/'runs/v858_nav2_verified/v909/continuation_status'
sys.path.insert(0,str(OPS));from entry import root_authorized,install
install()
from authority import digest
from handshake import file_sha
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    lock=(O/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    auth=root_authorized(time.time(),file_sha(BASE/'SOURCE_FREEZE.json'));assert not(O/'CLAIM.json').exists()
    dump(O/'CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),original_deadline_unix=auth['deadline_unix']))
    guard=(R/'REVIEW_PENDING').read_bytes();(O/'REVIEW_PENDING.before').write_bytes(guard);WRITABLE.mkdir(parents=True,exist_ok=False)
    child=None;status='NOT_PASSED';error=None;rows=[]
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('CONTINUATION_STOP')))
    current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='V909_OUTPUT_CONTINUATION_RUNNING',active_run=str(O.relative_to(R)),active_window=auth,execution_window_closed=False);dump(R/'CURRENT_EXPERIMENT.json',current)
    def launch(cmd,label,limit):
        nonlocal child
        assert time.time()+limit+30<auth['deadline_unix']
        assert sum(p.stat().st_size for p in (R/'runs/v858_nav2_verified/v909').rglob('*')if p.is_file()and not p.is_symlink())<1800*1024**2
        dump(O/'ACTIVE.json',dict(stage=label,at=time.time()))
        with(O/(label+'.console')).open('x')as f:
            child=subprocess.Popen(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'WORKER.json',dict(pid=child.pid,stage=label));rc=child.wait(timeout=limit);child=None
        assert rc==0,'CONTINUATION_FIRST_FAILURE '+label
    try:
        start=time.monotonic()
        for i in range(1,18):
            assert time.monotonic()-start<540.,'PLATFORM_TOTAL_RESERVE'
            (R/'REVIEW_PENDING').unlink(missing_ok=True)
            launch([str(R/'run_phase.sh'),str((OPS/'entry.py').relative_to(R)),'response',str(i)],'response_%02d'%i,65)
            assert json.loads((WRITABLE/('RESPONSE_%02d_RESULT.json'%i)).read_text())['passed']
            dump(O/'PLATFORM_PROGRESS.json',dict(completed_including_reused_first=i+1,total=18))
        (R/'REVIEW_PENDING').write_bytes(guard)
        items=[json.loads((WRITABLE/('RESPONSE_%02d_RESULT.json'%i)).read_text())for i in range(1,18)]
        dump(O/'PLATFORM_RESULT.json',dict(passed=True,reused_first_case=0,cases=items,actual_native=420+sum(x['actual_native']for x in items),replay_native=420+sum(x['replay_native']for x in items),private_native=0))
        for task in json.loads((BASE/'TASKS.json').read_text()):
            tp=O/(task['task_id']+'.task.json');ap=O/(task['task_id']+'.authorization.json');dump(tp,task);dump(ap,dict(auth,run_id=task['run_id'],task_sha256=digest(task)))
            launch([sys.executable,'-B',str(OPS/'entry.py'),'launch',str(tp),str(ap)],task['task_id'],260)
            out=Path(task['output']);d=json.loads((out/'RESULT.json').read_text());a=json.loads((out/'INDEPENDENT_AUDIT.json').read_text());rows.append(dict(task_id=task['task_id'],passed=a['passed'],actual_native=d['actual_native'],replay_native=d['replay_native'],private_native=d['private_native'],goal_m=d['goal_distance_m']));dump(O/'RESULTS.json',rows);assert a['passed']
            if task['role']=='dynamic_repeat':
                from repeat_contract import repeat_check
                d=repeat_check(out.parent/'main_we',out);dump(O/'REPEAT.json',d);assert d['passed']
        status='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        if child is not None and child.poll()is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        (R/'REVIEW_PENDING').write_bytes(guard)
        cases=[json.loads(p.read_text())for p in sorted(WRITABLE.glob('RESPONSE_*_RESULT.json'))];claimed=len(list(WRITABLE.glob('RESPONSE_*_CLAIM.json')))
        count=lambda k:420+sum(x[k]for x in cases)if len(cases)==claimed and all(x.get(k)is not None for x in cases)else None
        for task in json.loads((BASE/'TASKS.json').read_text()):
            out=Path(task['output'])
            if out.exists()and not any(x['task_id']==task['task_id']for x in rows):
                n=json.loads((out/'RESULT.json').read_text())if(out/'RESULT.json').exists()else{}
                rows.append(dict(task_id=task['task_id'],passed=False,actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),goal_m=n.get('goal_distance_m')))
        d=dict(closed=True,status=status,original_operation_failed=True,original_case00_actual_native=420,original_case00_replay_native=420,platform_total_actual_native=count('actual_native'),platform_total_replay_native=count('replay_native'),remaining_platform_unexecuted=17-claimed,rows=rows,unexecuted_navigation=2-len(rows),new24=0,error=error,models_authorized=False,deadline_unix=auth['deadline_unix'],closed_unix=time.time(),guard_restored=True)
        dump(O/'COMPLETION.json',d);current.update(status='REVIEW_PENDING',active_run=None,active_window=None,execution_window_closed=True,v909_output_continuation=d);dump(R/'CURRENT_EXPERIMENT.json',current)
        with(O/'finalize.console').open('w')as log:
            try:subprocess.run([sys.executable,'-B',str(OPS/'finalize.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
            except BaseException as e:dump(O/'FINALIZE_ERROR.json',dict(error=repr(e),models=0,no_more_models=True))
    return 0 if status=='ORIGINAL_WE_DEVELOPMENT_AND_REPEAT_PASSED'else 1
if __name__=='__main__':sys.exit(main())
