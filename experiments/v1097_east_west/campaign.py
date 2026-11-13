"""Single EW preflight, main, conditional repeat; bounded offline ownership."""
import sys,os,json,time,signal,subprocess,hashlib,fcntl,traceback,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];CORE=R/'experiments/rpccr_execution_core'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));from fresh_campaign import same_complete
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def used():
    seen=set();total=0
    for base,dirs,names in os.walk(R/'runs',followlinks=False):
        dirs[:]=[d for d in dirs if not Path(base,d).is_symlink()]
        for n in names:
            p=Path(base,n)
            if p.is_symlink():continue
            st=p.stat();key=st.st_dev,st.st_ino
            if key not in seen:seen.add(key);total+=st.st_size
    return total
def main():
    cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);w=json.loads((O/'ROUND_WINDOW.json').read_text());tasks=json.loads(Path(cfg['task_table']).read_text());guard=(O/'GUARD.bin').read_bytes()
    assert sha(R/'REVIEW_PENDING')==hashlib.sha256(guard).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    assert len(tasks)==3 and [t['kind']for t in tasks]==['t0','main','repeat'];assert json.loads((O/'QUALIFICATION.json').read_text())['passed']and json.loads((O/'REGRESSION.json').read_text())['passed']
    freeze=json.loads(Path(cfg['source_freeze']).read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());lock=(O/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=[];attempted=[];error=None;child=None;repeat=None
    def remaining():
        assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id'],'BOOT_CHANGED'
        return min(w['absolute_deadline_unix']-time.time(),w['hard_stop_monotonic']-time.monotonic())
    def halt(*_):raise TimeoutError('ROOT_HARD_STOP')
    def stop():
        nonlocal child
        if child is not None and child.poll()is None:
            try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
            except BaseException:
                try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
                except ProcessLookupError:pass
        child=None
    def active(task,stage):
        dump(O/'ACTIVE.json',dict(pid=child.pid,starttime=Path('/proc',str(child.pid),'stat').read_text().split()[21],task_id=task['task_id'],stage=stage))
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt);signal.setitimer(signal.ITIMER_REAL,max(.001,remaining()))
    try:
        for task in tasks:
            assert remaining()>(130 if task['kind']=='t0'else 1850),'INSUFFICIENT_TASK_AND_AUDIT_RESERVE'
            assert used()+128*1024**2<=cfg['temporary_limit_bytes'],'TEMPORARY2GIB_STOP';assert all(sha(R/p)==h for p,h in freeze.items())
            assert(R/'REVIEW_PENDING').read_bytes()==guard;assert not Path(task['output']).exists();path=O/(task['task_id']+'.json');dump(path,task);attempted.append(task['task_id']);dump(O/'ATTEMPTS.json',attempted)
            (R/'REVIEW_PENDING').unlink()
            try:
                with(O/(task['task_id']+'.console')).open('x')as log:child=subprocess.Popen([str(R/'run_phase.sh'),str((C/('t0.py'if task['kind']=='t0'else'worker.py')).relative_to(R)),str(path)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);active(task,'t0'if task['kind']=='t0'else'navigation');code=child.wait(timeout=min(100 if task['kind']=='t0'else 905,remaining()-10))
            finally:stop();(R/'REVIEW_PENDING').write_bytes(guard)
            out=Path(task['output']);p=out/'RESULT.json';p=p if p.exists()else out/'physics/paired/ENTRY_FAILURE_RESULT.json';result=json.loads(p.read_text())if p.exists()else dict(passed=False,missing_result=True)
            row=dict(task=task,result=result,returncode=code);rows.append(row);dump(O/'RESULTS.json',rows);assert code==0 and result['passed'],'FIRST_FUNCTIONAL_SAFETY_OR_EVIDENCE_FAILURE'
            if task['kind']=='t0':continue
            try:
                with(O/(task['task_id']+'.audit.console')).open('x')as log:child=subprocess.Popen([sys.executable,'-B',str(C/'audit.py'),str(path)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);active(task,'zero_model_audit');code=child.wait(timeout=min(900,remaining()-10))
            finally:stop()
            assert code==0,'INDEPENDENT_AUDIT_FAILURE';row['audit']=json.loads((out/'FINAL_INDEPENDENT_AUDIT.json').read_text());assert row['audit']['passed'];dump(O/'RESULTS.json',rows)
        repeat=same_complete(tasks[1],tasks[2]);assert repeat['passed'];assert all(sha(R/p)==h for p,h in freeze.items())
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());dump(O/'ERROR.json',error)
    finally:
        stop();(R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True));signal.setitimer(signal.ITIMER_REAL,0)
    keys=['vehicle_initializations','historical_replay_native','new_actual_native','own_replay_native','replay_state_initializations','private_mujoco_native','training_updates','analytical_prediction_native']
    counts={k:sum(z['result'][k]for z in rows)if all(z['result'].get(k)is not None for z in rows)else None for k in keys}
    passed=bool(error is None and len(rows)==3 and repeat and repeat['passed']);summary=dict(closed=True,passed=passed,version='v1097',scope='declared EW t0 plus main and conditional exact repeat only',attempted=attempted,unexecuted=[t['task_id']for t in tasks if t['task_id']not in attempted],counts=counts,error=error,complete_repeat=repeat,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,source_unchanged=all(sha(R/p)==h for p,h in freeze.items()),whole_route_passed=passed,new24_executed=False,science='V1085_entry/V1087 with V1089 route scene contract',west_east_old_failure_preserved=True)
    dump(O/'COMPLETION.json',summary);(R/cfg['report']).write_text('# V1097 declared EAST_WEST route\n\n```json\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n```\n\nOne observed route main and exact repeat, not three-route or24 acceptance. Start[4,-1.9] is the previously declared north-shifted course.\n')
    x=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());x.update(status='REVIEW_PENDING',active_run=None,active_window=None,active_entrypoint=None,next_physical_authorized=False,latest_completed=summary,latest_report=cfg['report']);dump(R/'CURRENT_EXPERIMENT.json',x)
    with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- FINAL V1097 EW: passed='+str(passed)+'; counts='+json.dumps(counts)+'; old WE failure preserved, no24. See '+cfg['report']+'.\n')
    print(json.dumps(summary),flush=True)
    try:
        with(O/'finalize.console').open('x')as log:subprocess.run([sys.executable,'-B',str(C/'finalize.py'),str(O/'CONFIG.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    except BaseException as e:dump(O/'ARCHIVE_ERROR.json',dict(error=repr(e),models=0,raw_retained=True))
if __name__=='__main__':main()
