"""One immutable registered task; all model integration remains inside run_phase."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import verify_sources,file_sha,require
from authority import authorized
from audit import audit
def stop(p):
 if p and p.poll()is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def main():
 task_path=Path(sys.argv[1]);receipt_path=Path(sys.argv[2]);task=json.loads(task_path.read_text());receipt=json.loads(receipt_path.read_text());deadline=authorized(task,receipt,time.time(),file_sha(C/'SOURCE_FREEZE.json'));verify_sources(R,C/'SOURCE_FREEZE.json');require(deadline-time.time()>=300,'INSUFFICIENT_TASK_TIME')
 config=json.loads(Path(task['nav2_params']).read_text());require(config['controller_server']['ros__parameters']['FollowPath']['plugin']in ['nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController','nav2_mppi_controller::MPPIController'],'CONTROLLER_NOT_REGISTERED')
 out=Path(task['output']);require(out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v874'),'OUTPUT_SCOPE');require(not out.exists(),'ALREADY_ATTEMPTED')
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 out.mkdir(parents=True);(out/'CLAIM.json').write_text(json.dumps(dict(started_unix=time.time(),root_deadline_unix=deadline,run_id=task['run_id']))+'\n')
 for name,value in [('TASK.json',task),('AUTHORIZATION.json',receipt)]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
 guard=(R/'REVIEW_PENDING').read_bytes();(out/'REVIEW_PENDING.before').write_bytes(guard);jobs=[];files=[];status='ENTRY';error=None
 try:
  (R/'REVIEW_PENDING').unlink();sys.path.insert(0,str(R/'experiments/v856_nav2_foundation'));from ros_environment import command,environment
  args=[str(out/'TASK.json'),str(out/'AUTHORIZATION.json')]
  for name,cmd,env in [('ros',command(['/usr/bin/python3.12',str(C/'ros_worker.py'),*args]),environment()),('native',[str(R/'run_phase.sh'),str((C/'native_worker.py').relative_to(R)),*args],None)]:
   f=(out/(name+'.console')).open('w');files.append(f);jobs.append(subprocess.Popen(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True))
  until=min(deadline-3,time.time()+240)
  for p in reversed(jobs):p.wait(timeout=max(.01,until-time.time()))
  require(all(p.returncode==0 for p in jobs),'WORKER_NONZERO');status='WORKERS_CLOSED'
 except BaseException as e:error=dict(error=repr(e),traceback=traceback.format_exc());status='ENTRY_OR_WORKER_EXCEPTION'
 finally:
  for p in reversed(jobs):stop(p)
  for f in files:f.close()
  (R/'REVIEW_PENDING').write_bytes(guard)
  summary=dict(status=status,error=error,closed=True,guard_restored=(R/'REVIEW_PENDING').read_bytes()==guard,closed_unix=time.time(),actual_counts='RESULT_OR_UNKNOWN_NO_ZERO_INFERENCE');(out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n')
 # Audit failed prefixes too; no model/ROS initialization in this saved-evidence phase.
 result=audit(task);summary.update(independent_audit_passed=result['passed'],status='PASSED'if status=='WORKERS_CLOSED'and result['passed']else'NOT_PASSED');(out/'COMPLETION.json').write_text(json.dumps(summary,indent=2)+'\n');return 0 if summary['status']=='PASSED'else 1
if __name__=='__main__':sys.exit(main())
