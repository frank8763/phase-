"""Fixed original-course forward/stop/reverse/stop, no online obstacle truth."""
import fcntl,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v896_overnight_20261108'
def read(p):return json.loads(p.read_text())
def main():
    auth=read(O/'AUTHORIZATION.json');assert auth['models_authorized']is True and auth['deadline_unix']==1794182400. and time.time()<auth['deadline_unix']-180
    assert not(O/'platform/RESULT.json').exists(),'PLATFORM_ALREADY_ATTEMPTED'
    for n,h in read(C/'SOURCE_FREEZE.json')['files'].items():assert hashlib.sha256((R/n).read_bytes()).hexdigest()==h,n
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[min(3,len(cpus)-1)]})
    sys.path[:0]=[str(R/'experiments/v894_wait_map_validation')]
    from physical import create_vehicle,replay
    def stop(*_):raise InterruptedError('BOUNDED_PLATFORM_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,min(80.,auth['deadline_unix']-5-time.time()))
    out=O/'platform';out.mkdir(exist_ok=False);v=None;result=dict(passed=False,actual_native=None,replay_native=None,private_native=0)
    try:
        task=dict(case_id='WEST_EAST',seed=10010001,phase=.6573753567727383,dynamic=True)
        v=create_vehicle(out/'physics',task);rows=[];begun=time.monotonic()
        for i in range(1200):
            assert time.time()<auth['deadline_unix']-15
            target=begun+i*.01;time.sleep(max(0.,target-time.monotonic()))
            velocity=.1 if i<400 else (0. if i<600 else (-.1 if i<1000 else 0.))
            v.step(velocity,0.);rows.append([v.count,*v.body()])
        result.update(v.finish());comparison=replay(v,auth['deadline_unix'],out/'physics');result.update(replay=comparison,replay_native=comparison['replay_native']);a=np.asarray(rows);checks={}
        checks['actual1200_and_full_replay1200']=result['actual_native']==1200 and result['fully_recorded_native']==1200 and comparison['replay_native']==1200 and comparison['passed']
        checks['forward_and_reverse_progress']=a[399,1]-a[0,1]>=.25 and a[599,1]-a[999,1]>=.25
        for start in [400,1000]:
            pose=a[start-1,1:3];movement=np.linalg.norm(a[start:start+200,1:3]-pose,axis=1)
            checks[str(start)+'_brake_displacement_le04']=float(movement.max())<=.04
            checks[str(start)+'_speed_by05_le03']=bool(np.max(abs(a[start+49:start+200,4]))<=.03)
        checks['yaw_straight_bound']=float(np.max(abs(a[:,3])))<=.05
        checks['final_stopped']=result['final_translation_speed_m_s']<=.03
        checks['original_safety']=result['minimum_actual_clearance_m']>=.15 and result['bad_contacts']==0
        result.update(passed=all(checks.values()),checks={k:bool(x)for k,x in checks.items()},scope='Fixed platform response qualification; not a complete dynamics bound or navigation',environment_initializations_completed=1)
        np.savez_compressed(out/'BODY_SAMPLES.npz',rows=a)
    except BaseException as e:
        result.update(error=repr(e),traceback=traceback.format_exc())
        if v is not None:
            result.update(v.finish());result['replay_native']=None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
