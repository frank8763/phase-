"""True task t0 model/sensor query, authorized before imports; zero native steps."""
import fcntl,json,os,signal,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import authorized
from handshake import file_sha,verify_sources,require

def main():
 task=json.loads(Path(sys.argv[1]).read_text());receipt=json.loads(Path(sys.argv[2]).read_text());deadline=authorized(task,receipt,time.time(),file_sha(C/'SOURCE_FREEZE.json'));verify_sources(R,C/'SOURCE_FREEZE.json')
 out=R/'runs/v858_nav2_verified/v881/preflights'/task['task_id'];require(not out.exists(),'PREFLIGHT_ALREADY_ATTEMPTED');out.mkdir(parents=True);result=dict(passed=False,environment_initialization_attempted=False,native_integrations=0);v=None
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[3]})
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PREFLIGHT_MODEL_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,min(70.,max(.01,deadline-5-time.time())))
 try:
  from physical import create_vehicle
  result['environment_initialization_attempted']=True;v=create_vehicle(out/'physics',task);result['environment_initialization_completed']=True;scan=v.scan();require(v.count==0 and v.d.time==0.,'T0_ADVANCED');require(v.first_detection is None,'INITIAL_ACTOR_VISIBLE');require(len(scan['ranges'])==32,'SENSOR_SCOPE')
  (out/'INITIAL_SCAN.json').write_text(json.dumps(scan,indent=2)+'\n')
  result.update(passed=True,initial_body=v.body(),minimum_clearance_m=v.min_clear,minimum_self_margin_m=v.min_self,bad_contacts=v.bad,model_sha256=json.loads((out/'physics/SETUP.json').read_text())['model_sha256'],actor=None if v.actor is None else v.actor.config)
 except BaseException as e:result.update(error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time());(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
