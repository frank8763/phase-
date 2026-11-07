import fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;ROOT=R/'runs/v857_assembly_contact';OUT=ROOT/'interface01'
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    end=json.loads((ROOT/'ROUND_WINDOW.json').read_text())['absolute_deadline_unix'];assert time.time()<end-120,'INSUFFICIENT_ORIGINAL_WINDOW';assert not(OUT/'LAUNCH_CLAIM.json').exists();assert json.loads((ROOT/'SAVED_INTERFACE_AUDIT.json').read_text())['passed']
    for source in [R/'experiments/v857_assembly_contact/SOURCE_FREEZE.json',C/'SOURCE_FREEZE.json']:
        for name,digest in json.loads(source.read_text())['files'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'SOURCE_CHANGED:'+name
    lock=(ROOT/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with(OUT/'LAUNCH_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),inherited_absolute_deadline_unix=end),f)
    guard=(R/'REVIEW_PENDING').read_bytes();(OUT/'REVIEW_PENDING.before').write_bytes(guard);p=None;status='ENTRY';window=dict(started_unix=time.time(),absolute_deadline_unix=end,round_closed=False,original_old_replay_native=1,scientific_changes=0);dump(OUT/'ROUND_WINDOW.json',window)
    try:
        (R/'REVIEW_PENDING').unlink()
        with(OUT/'component.console').open('w')as f:
            p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R))],cwd=R,env=dict(os.environ,PHASE_MODEL_ABSOLUTE_DEADLINE=str(end-5)),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);rc=p.wait(timeout=end-time.time())
        result=json.loads((OUT/'RESULT.json').read_text())if(OUT/'RESULT.json').exists()else dict(passed=False,status='MISSING_RESULT_COUNTS_UNKNOWN',counts=None);status=result['status'];dump(OUT/'COMPLETION.json',dict(result=result,returncode=rc,closed=True))
    except BaseException as e:status='OPERATION_EXCEPTION_NO_FURTHER_CONTINUATION';dump(OUT/'DRIVER_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc()))
    finally:
        if p and p.poll()is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=4)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,closed_unix=time.time(),guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard);dump(OUT/'ROUND_WINDOW.json',window);print(json.dumps(window),flush=True)
if __name__=='__main__':main()
