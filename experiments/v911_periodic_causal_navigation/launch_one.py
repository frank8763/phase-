"""One approved immutable task; no model import in this parent process."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import file_sha,verify_sources,require
from authority import authorized
from audit import audit
def stop(p):
    if p is None or p.poll()is not None:return
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def main():
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());deadline=authorized(task,receipt,time.time(),file_sha(C/'SOURCE_FREEZE.json'));verify_sources(R,C/'SOURCE_FREEZE.json');require(deadline-time.time()>=300,'INSUFFICIENT_TASK_TIME')
    out=Path(task['output']);require(out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v911')and not out.exists(),'ALREADY_ATTEMPTED_OR_WRONG_OUTPUT')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();out.mkdir(parents=True)
    for name,data in [('TASK.json',task),('AUTHORIZATION.json',receipt)]:(out/name).write_text(json.dumps(data,indent=2)+'\n')
    (out/'REVIEW_PENDING.before').write_bytes(guard);jobs=[];files=[];error=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('OUTER_STOP')))
    try:
        (R/'REVIEW_PENDING').unlink();sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
        args=[str(out/'TASK.json'),str(out/'AUTHORIZATION.json')]
        rosenv=environment();rosenv['AMENT_PREFIX_PATH']=str(R/'runs/v884_feasible_rpp/install')+':'+rosenv['AMENT_PREFIX_PATH']
        for name,cmd,env in [('ros',command(['/usr/bin/python3.12',str(C/'ros_worker.py'),*args]),rosenv),('native',[str(R/'run_phase.sh'),str((C/'native_worker.py').relative_to(R)),*args],None)]:
            f=(out/(name+'.console')).open('w');files.append(f);jobs.append(subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True));(R/'runs/v911_periodic_causal_navigation/WORKER_PROCESSES.json').write_text(json.dumps(dict(jobs=[dict(pid=x.pid)for x in jobs]))+'\n')
        until=min(deadline-5,time.time()+240)
        for p in reversed(jobs):p.wait(timeout=max(.01,until-time.time()))
        require(all(p.returncode==0 for p in jobs),'WORKER_NONZERO')
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        for p in reversed(jobs):stop(p)
        for f in files:f.close()
        (R/'REVIEW_PENDING').write_bytes(guard)
        summary=dict(closed=True,error=error,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time())
        (out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n')
    checked=audit(task);summary.update(passed=error is None and checked['passed'],independent_audit=checked)
    (out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if summary['passed']else 1
if __name__=='__main__':sys.exit(main())
