"""Bounded qualification driver with one launch claim and original guard restoration."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;OUT=R/'runs/v857_assembly_contact';ROOT_END=1794052800.
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    assert json.loads((OUT/'ZERO_QUALIFICATION.json').read_text())['passed'];assert not(OUT/'LAUNCH_CLAIM.json').exists();assert time.time()<ROOT_END-180
    for name,digest in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'FROZEN_INPUT_CHANGED:'+name
    lock=(OUT/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(OUT/'LAUNCH_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time()),f)
    guard=(R/'REVIEW_PENDING').read_bytes();(OUT/'REVIEW_PENDING.before').write_bytes(guard);end=min(ROOT_END,time.time()+900);window=dict(started_unix=time.time(),absolute_deadline_unix=end,root_absolute_deadline_unix=ROOT_END,round_closed=False);dump(OUT/'ROUND_WINDOW.json',window);p=None;status='ENTRY'
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('DRIVER_TERMINATED')))
    try:
        (R/'REVIEW_PENDING').unlink()
        with(OUT/'component.console').open('w')as f:
            p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'component.py').relative_to(R))],cwd=R,env=dict(os.environ,PHASE_MODEL_ABSOLUTE_DEADLINE=str(end-5)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);rc=p.wait(timeout=max(.01,end-time.time()))
        result=json.loads((OUT/'RESULT.json').read_text())if(OUT/'RESULT.json').exists()else{'passed':False,'counts':None,'status':'NO_COMPLETE_RESULT_COUNTS_UNKNOWN'};status=result['status'];dump(OUT/'COMPLETION.json',dict(returncode=rc,result=result,closed=True))
    except BaseException as e:status='DRIVER_EXCEPTION';dump(OUT/'DRIVER_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),model_integrations='UNKNOWN_UNLESS_COMPLETE_RESULT_EXISTS'))
    finally:
        if p and p.poll()is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,closed_unix=time.time(),review_pending_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'ROUND_WINDOW.json',window)
        current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='REVIEW_PENDING',active_pid=None,active_run=None,active_entrypoint=None);current['v857_assembly_contact']=dict(status=status,closed=True,report='docs/ASSEMBLY_CONTACT_V857_REPORT.md',no_automatic_navigation=True);dump(R/'CURRENT_EXPERIMENT.json',current);print(json.dumps(dict(status=status,closed=True)),flush=True)
if __name__=='__main__':main()
