"""Prepared future launcher. The checked-in receipt explicitly forbids execution."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments/v862_ready_static'))
from handshake import authorized,file_sha,require,verify_sources
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def stop(process):
    if process and process.poll()is None:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=3.)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
def main():
    task=json.loads((C/'TASK_TEMPLATE.json').read_text())
    receipt_path=Path(sys.argv[1])if len(sys.argv)>1 else C/'AUTHORIZATION_TEMPLATE.json'
    receipt=json.loads(receipt_path.read_text());deadline=authorized(task,receipt,time.time(),file_sha(C/'SOURCE_FREEZE.json'))
    # No runtime restore, model construction, sockets or subprocesses before this point.
    verify_sources(R,C/'SOURCE_FREEZE.json');require(deadline-time.time()>=300,'INSUFFICIENT_SINGLE_TASK_WINDOW')
    config=json.loads(Path(task['nav2_params']).read_text());require(config['lifecycle_manager_navigation']['ros__parameters']['autostart']is False,'AUTOSTART_MUST_BE_GATED')
    require(config['controller_server']['ros__parameters']['FollowPath']['plugin']=='nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController','FROZEN_RPP_PLUGIN_CHANGED')
    runtime=R/'runs/v856_nav2_foundation/rootfs/opt/ros/jazzy';require(runtime.is_dir(),'RESTORE_VERIFIED_ROS_RUNTIME_FIRST')
    out=Path(task['output']);require(out.resolve().is_relative_to(R/'runs/v858_nav2_verified'),'OUTPUT_SCOPE')
    require(task['socket_dir']==str(out.relative_to(R)),'SOCKET_SCOPE');require(not out.exists(),'TASK_ALREADY_ATTEMPTED')
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fcntl.flock(lock,fcntl.LOCK_UN);out.mkdir(parents=True);claim=(out/'CLAIM.json').open('x');json.dump(dict(started_unix=time.time(),root_deadline_unix=deadline,run_id=task['run_id']),claim);claim.close()
    (out/'TASK.json').write_text(json.dumps(task,indent=2)+'\n');(out/'AUTHORIZATION.json').write_text(json.dumps(receipt,indent=2)+'\n')
    guard=(R/'REVIEW_PENDING').read_bytes();(out/'REVIEW_PENDING.before').write_bytes(guard);jobs=[];files=[];status='ENTRY';error=None
    until=min(deadline-3,time.time()+240.)
    try:
        (R/'REVIEW_PENDING').unlink();sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
        args=[str(out/'TASK.json'),str(out/'AUTHORIZATION.json')]
        rf=(out/'ros.console').open('w');files.append(rf);ros=subprocess.Popen(command(['/usr/bin/python3.12',str(C/'ros_bridge.py'),*args]),cwd=R,env=environment(),stdout=rf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(ros)
        nf=(out/'native.console').open('w');files.append(nf);native=subprocess.Popen([str(R/'run_phase.sh'),str((C/'native_backend.py').relative_to(R)),*args],cwd=R,stdout=nf,stderr=subprocess.STDOUT,start_new_session=True);jobs.append(native)
        native.wait(timeout=max(.01,until-time.time()));ros.wait(timeout=max(.01,until-time.time()));status='WORKERS_CLOSED'
    except BaseException as e:status='ENTRY_OR_WORKER_EXCEPTION';error=dict(error=repr(e),traceback=traceback.format_exc())
    finally:
        for process in reversed(jobs):stop(process)
        for f in files:f.close()
        (R/'REVIEW_PENDING').write_bytes(guard)
        summary=dict(status=status,error=error,closed=True,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time(),source_frozen_readback_required=True,actual_counts='USE_RESULT_OR_UNKNOWN_NO_ZERO_INFERENCE')
        (out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n')
    if status=='WORKERS_CLOSED':
        verify_sources(R,C/'SOURCE_FREEZE.json')
        from audit_result import audit
        result=audit(task);summary.update(status='PASSED'if result['passed']else'FUNCTIONAL_OR_EVIDENCE_NOT_PASSED',independent_audit_passed=result['passed'])
        (out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if result['passed']else 1
    return 1
if __name__=='__main__':sys.exit(main())
