"""One task, native readiness then ROS; no model construction in this parent."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v979_state_recovery_physical'
sys.path.insert(0,str(C))
from authority import authorized,sha
from handshake import verify_sources
from audit import audit
def stop(child):
    if child is None or child.poll()is not None:return
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
def main():
    task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text())
    deadline=authorized(task,receipt,time.time(),sha(C/'SOURCE_FREEZE.json'));verify_sources(R,C/'SOURCE_FREEZE.json')
    assert deadline-time.time()>=350,'INSUFFICIENT_FIXED_TASK_RESERVE'
    out=Path(task['output']);assert out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v979')and not out.exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
    guard=(R/'REVIEW_PENDING').read_bytes();out.mkdir(parents=True)
    for name,value in [('TASK.json',task),('AUTHORIZATION.json',receipt)]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
    (out/'REVIEW_PENDING.before').write_bytes(guard);jobs=[];streams=[];error=None
    signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(InterruptedError('TASK_OUTER_STOP')))
    try:
        (R/'REVIEW_PENDING').unlink()
        native=(out/'native.console').open('x');streams.append(native)
        jobs.append(subprocess.Popen([str(R/'run_phase.sh'),str((C/'native_worker.py').relative_to(R)),str(out/'TASK.json'),str(out/'AUTHORIZATION.json')],cwd=R,stdout=native,stderr=subprocess.STDOUT,start_new_session=True))
        ready_until=min(deadline-100,time.time()+120)
        while not(out/'NATIVE_READY.json').exists():
            assert jobs[0].poll()is None,'NATIVE_FAILED_BEFORE_CANONICAL_READY'
            assert time.time()<ready_until,'CANONICAL_STATE_RESTORE_TIMEOUT'
            time.sleep(.05)
        sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
        env=environment();env['AMENT_PREFIX_PATH']=str(R/'runs/v884_feasible_rpp/install')+':'+env['AMENT_PREFIX_PATH']
        log=(out/'ros.console').open('x');streams.append(log)
        jobs.append(subprocess.Popen(command(['/usr/bin/python3.12',str(C/'ros_worker.py'),str(out/'TASK.json'),str(out/'AUTHORIZATION.json')]),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
        (O/'WORKERS.json').write_text(json.dumps(dict(task_id=task['task_id'],jobs=[dict(pid=p.pid)for p in jobs]),indent=2)+'\n')
        until=min(deadline-15,time.time()+240)
        while any(p.poll()is None for p in jobs):
            failed=[p for p in jobs if p.poll()is not None and p.returncode!=0]
            assert not failed,'FIRST_WORKER_FAILURE'
            assert time.time()<until,'TASK_OUTER_DEADLINE'
            time.sleep(.1)
        assert all(p.returncode==0 for p in jobs),'WORKER_NONZERO'
    except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        for p in reversed(jobs):stop(p)
        for stream in streams:stream.close()
        (R/'REVIEW_PENDING').write_bytes(guard)
        result=dict(closed=True,error=error,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time())
        (out/'COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n')
    proof=audit(task);result.update(passed=error is None and proof['passed'],independent_audit=proof)
    (out/'COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
