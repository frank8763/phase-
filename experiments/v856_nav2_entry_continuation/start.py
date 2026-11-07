"""Single fixed-source output-directory continuation, no scientific repair or extra task."""
from common import *
import fcntl,os,signal,subprocess,time,traceback
from ros_environment import environment,command
END=1794052800.;HERE=Path(__file__).parent

def dump(p,v):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n');t.replace(p)
def unchanged():
    for manifest in [C/'SOURCE_FREEZE.json',HERE/'SOURCE_FREEZE.json']:
        for path,digest in json.loads(manifest.read_text())['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,'FROZEN_INPUT_CHANGED:'+path
    assert time.time()<END

def stop(p):
    if p.poll()is None:
        os.killpg(p.pid,signal.SIGTERM)
        try:p.wait(timeout=4)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def main():
    unchanged();assert json.loads((ROOT/'ROUND_WINDOW.json').read_text())['round_closed'];assert not(OUT/'LAUNCH_CLAIM.json').exists()
    with (OUT/'LAUNCH_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),deadline_unix=END),f)
    lock=(ROOT/'campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    guard=(R/'REVIEW_PENDING').read_bytes();(OUT/'REVIEW_PENDING.before').write_bytes(guard);jobs=[];ledger=dict(status='FIXED_EXECUTOR_QUALIFICATION',tasks=[],qualification=None,closed=False,old_entry_model_initializations=1,old_entry_integrations=0,new24=0,training=0,deadline_unix=END)
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('TERMINATED')))
    dump(OUT/'ROUND_WINDOW.json',dict(started_unix=time.time(),absolute_deadline_unix=END,round_closed=False));dump(OUT/'LEDGER.json',ledger)
    try:
        assert time.time()<END-900;(R/'REVIEW_PENDING').unlink()
        with (OUT/'qualification.console').open('w')as f:
            p=subprocess.Popen([str(R/'run_phase.sh'),str((HERE/'vehicle.py').relative_to(R))],cwd=R,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(p)
            try:rc=p.wait(timeout=min(180,END-time.time()-20))
            finally:stop(p)
        qp=OUT/'vehicle_qualification01/RESULT.json';qualification=json.loads(qp.read_text())if qp.exists()else{'passed':False,'actual_native':None,'replay_native':None,'reason':'MISSING_COMPLETE_RESULT'};ledger['qualification']=qualification;dump(OUT/'LEDGER.json',ledger)
        if rc!=0 or not qualification['passed']:raise RuntimeError('EXECUTOR_QUALIFICATION_NOT_PASSED')
        for task in json.loads((C/'TASK_LIST.json').read_text()):
            assert time.time()<END-850,'INSUFFICIENT_FULL_TASK_TIME';unchanged();dump(OUT/'ACTIVE.json',dict(task=task['id'],started_unix=time.time()));ledger['status']='RUNNING_'+task['id'];dump(OUT/'LEDGER.json',ledger)
            assert not Path(task['output']).exists();taskfile=ROOT/(task['id']+'.task.json');assert json.loads(taskfile.read_text())==task
            with (OUT/(task['id']+'.ros.console')).open('w')as rf,(OUT/(task['id']+'.physics.console')).open('w')as pf:
                ros=subprocess.Popen(command(['/usr/bin/python3.12','-B',str(C/'native_ros.py'),str(taskfile)]),cwd=R,env=environment(),stdout=rf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(ros)
                native=subprocess.Popen([str(R/'run_phase.sh'),str((HERE/'worker.py').relative_to(R)),str(taskfile)],cwd=R,stdout=pf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native);deadline=min(time.monotonic()+780,time.monotonic()+END-time.time()-10)
                try:
                    while(ros.poll()is None or native.poll()is None)and time.monotonic()<deadline:time.sleep(.2)
                    assert ros.poll()is not None and native.poll()is not None,'TASK_DEADLINE'
                finally:stop(ros);stop(native)
            rp=Path(task['output'])/'RESULT.json';res=json.loads(rp.read_text())if rp.exists()else{'passed':False,'actual_native':None,'replay_native':None,'reason':'MISSING_COMPLETE_RESULT'};ledger['tasks'].append(dict(id=task['id'],result=res,returncode_ros=ros.returncode,returncode_native=native.returncode));dump(OUT/'LEDGER.json',ledger)
            assert res['passed']and ros.returncode==native.returncode==0,'FIRST_FUNCTIONAL_OR_EVIDENCE_FAILURE:'+task['id']
        ledger.update(passed=True,status='ALL_NINE_NAV2_DEVELOPMENT_NAVIGATIONS_PASSED')
    except BaseException as e:ledger.update(passed=False,status='STOPPED_FIRST_FAILURE_OR_DEADLINE',error=repr(e),traceback=traceback.format_exc());dump(OUT/'ERROR.json',dict(error=repr(e),traceback=traceback.format_exc()))
    finally:
        for p in jobs:stop(p)
        (R/'REVIEW_PENDING').write_bytes(guard);ledger.update(closed=True,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'LEDGER.json',ledger);w=json.loads((OUT/'ROUND_WINDOW.json').read_text());w.update(round_closed=True,status=ledger['status'],closed_unix=time.time());dump(OUT/'ROUND_WINDOW.json',w);dump(OUT/'ACTIVE.json',dict(completed=True,status=ledger['status']))
        current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_pid=None,active_run=None,active_entrypoint=None);current['v856_nav2_entry_continuation']=dict(closed=True,status=ledger['status'],model_deadline=END,new24=0);dump(R/'CURRENT_EXPERIMENT.json',current);print(json.dumps(dict(status=ledger['status'],tasks=len(ledger['tasks']))),flush=True)
if __name__=='__main__':main()
