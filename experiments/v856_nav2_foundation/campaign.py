"""One bounded Phase-only Nav2 qualification/development campaign; no automatic revisions."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
from ros_environment import environment,command
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v856_nav2_foundation';END=1794052800.
def dump(p,v):
    p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');t.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unchanged():
    frozen=json.loads((C/'SOURCE_FREEZE.json').read_text())
    for path,digest in frozen['files'].items():assert sha(R/path)==digest,'FROZEN_INPUT_CHANGED:'+path
    assert time.time()<END,'ROOT_DEADLINE'
def stop(p):
    if p and p.poll()is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=4)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def main():
    claim=OUT/'LAUNCH_CLAIM.json'
    with claim.open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),absolute_deadline_unix=END),f)
    lock=(OUT/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert json.loads((OUT/'smoke05/RESULT.json').read_text())['passed'];assert json.loads((OUT/'ZERO_ADAPTER_QUALIFICATION.json').read_text())['passed'];unchanged()
    guard=(R/'REVIEW_PENDING').read_bytes();(OUT/'REVIEW_PENDING.before').write_bytes(guard)
    window=dict(started_unix=time.time(),absolute_deadline_unix=END,round_closed=False,models_started=False,status='STARTING_NATIVE_QUALIFICATION');dump(OUT/'ROUND_WINDOW.json',window)
    ledger=dict(status=window['status'],tasks=[],qualification=None,new24=0,training=0,old_windows_reopened=False);children=[]
    def interrupted(sig,frame):raise InterruptedError('CAMPAIGN_SIGNAL_'+str(sig))
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    def run_one(script,log,timeout):
        unchanged()
        with log.open('w')as f:
            p=subprocess.Popen([str(R/'run_phase.sh'),str(script.relative_to(R))],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append(p)
            try:return p.wait(timeout=min(timeout,max(.01,END-time.time()-10)))
            except BaseException:stop(p);raise
    try:
        assert time.time()<END-900,'INSUFFICIENT_ROOT_TIME';(R/'REVIEW_PENDING').unlink();window['models_started']=True;dump(OUT/'ROUND_WINDOW.json',window)
        rc=run_one(C/'qualify_vehicle.py',OUT/'vehicle_qualification01.console',180)
        qp=OUT/'vehicle_qualification01/RESULT.json';qualification=json.loads(qp.read_text())if qp.exists()else json.loads((OUT/'QUALIFICATION_ENTRY_ERROR.json').read_text());ledger['qualification']=qualification;dump(OUT/'LEDGER.json',ledger)
        if rc!=0 or not qualification['passed']:raise RuntimeError('EXECUTOR_QUALIFICATION_NOT_PASSED')
        ledger['status']='RUNNING_FIXED_THREE_ROUTE_STATIC_BASELINES';dump(OUT/'LEDGER.json',ledger)
        tasks=json.loads((C/'TASK_LIST.json').read_text())
        for task in tasks:
            if time.time()>END-850:raise TimeoutError('INSUFFICIENT_TIME_FOR_FULL_NEXT_TASK_AND_REPLAY')
            unchanged();dump(OUT/'ACTIVE.json',dict(task=task['id'],started_unix=time.time()));dump(OUT/'LEDGER.json',ledger)
            out=Path(task['output']);assert not out.exists(),'TASK_ALREADY_EXISTS';taskfile=OUT/(task['id']+'.task.json');assert json.loads(taskfile.read_text())==task,'TASK_DERIVATION_CHANGED'
            with (OUT/(task['id']+'.ros.console')).open('w')as rf,(OUT/(task['id']+'.physics.console')).open('w')as pf:
                ros=subprocess.Popen(command(['/usr/bin/python3.12','-B',str(C/'native_ros.py'),str(taskfile)]),cwd=R,env=environment(),stdout=rf,stderr=subprocess.STDOUT,start_new_session=True);children.append(ros)
                native=subprocess.Popen([str(R/'run_phase.sh'),str((C/'native_worker.py').relative_to(R)),str(taskfile)],cwd=R,stdout=pf,stderr=subprocess.STDOUT,start_new_session=True);children.append(native)
                task_end=min(time.monotonic()+780,time.monotonic()+END-time.time()-10)
                try:
                    while (ros.poll()is None or native.poll()is None)and time.monotonic()<task_end:time.sleep(.2)
                    if ros.poll()is None or native.poll()is None:raise TimeoutError('TASK_OUTER_780S_DEADLINE')
                finally:stop(ros);stop(native)
            resultpath=out/'RESULT.json';result=json.loads(resultpath.read_text())if resultpath.exists()else{'passed':False,'actual_native':None,'replay_native':None,'reason':'PROCESS_EXIT_WITHOUT_COMPLETE_RESULT'}
            ledger['tasks'].append(dict(id=task['id'],returncode_ros=ros.returncode,returncode_native=native.returncode,result=result));dump(OUT/'LEDGER.json',ledger)
            if not result['passed']or ros.returncode!=0 or native.returncode!=0:raise RuntimeError('FIRST_FUNCTIONAL_OR_EVIDENCE_FAILURE:'+task['id'])
        ledger['status']='ALL_NINE_NAV2_DEVELOPMENT_NAVIGATIONS_PASSED';ledger['passed']=True
    except BaseException as e:
        ledger.update(status='STOPPED_FIRST_FAILURE_OR_DEADLINE',passed=False,error=repr(e),traceback=traceback.format_exc());dump(OUT/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc()))
    finally:
        for p in children:stop(p)
        (R/'REVIEW_PENDING').write_bytes(guard);ledger.update(closed=True,closed_unix=time.time(),review_pending_original_bytes_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'LEDGER.json',ledger)
        window.update(round_closed=True,status=ledger['status'],closed_unix=time.time());dump(OUT/'ROUND_WINDOW.json',window);dump(OUT/'ACTIVE.json',dict(completed=True,status=ledger['status']))
        current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_pid=None,active_run=None,active_entrypoint=None,execution_window_closed=True);current['v856_nav2_foundation']=dict(status=ledger['status'],closed=True,model_deadline=END,new24=0,report='docs/NAV2_FOUNDATION_V856_REPORT.md');dump(R/'CURRENT_EXPERIMENT.json',current)
        print(json.dumps(dict(status=ledger['status'],closed=True,tasks=len(ledger['tasks']),qualification_passed=bool((ledger['qualification']or{}).get('passed')))),flush=True)
    return 0 if ledger.get('passed')else 1
if __name__=='__main__':sys.exit(main())
