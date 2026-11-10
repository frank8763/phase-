"""Bounded fixed-input response worker. Actual physics only through run_phase."""
import fcntl,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(C))
from authority import authorized,END
from schedule import controls

def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    task=json.loads(Path(sys.argv[1]).read_text());root=authorized(task);out=Path(task['output'])
    assert out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v993')and not out.exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));assert len(cpus)>=4;os.sched_setaffinity(0,{cpus[3]})
    start=time.monotonic();wall=time.time();hard=min(root-10,wall+task['task_wall_limit_s'])
    restore_end=min(hard-100,wall+180);vehicle=None;holder={};in_step=False;replay_started=False;replay_complete=False
    result=dict(passed=False,status='INITIALIZING',vehicle_tasks_initialized=None,historical_native=None,new_actual_native=0,
        replay_native=0,private_native=0,root_deadline_unix=root,task_hard_deadline_unix=hard,diagnostic_only=True)
    def halt(*_):raise InterruptedError('ROOT_OR_TASK_STOP')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,max(.001,min(hard-time.time(),task['task_wall_limit_s'])-5))
    def guard():assert time.time()<restore_end and time.monotonic()<start+180,'RESTORE_OR_ROOT_DEADLINE'
    def progress(v,phase):dump(out/'STARTUP_PROGRESS.json',dict(phase=phase,native_tick=v.count,at=time.time(),models_started=True))
    try:
        # All physical imports stay after current-source/root/task validation.
        from physical import create_vehicle,replay
        vehicle=create_vehicle(out/'physics',task,guard,progress,lambda v:holder.update(vehicle=v));result['vehicle_tasks_initialized']=1
        result['historical_native']=vehicle.count;result['status']='RUNNING'
        begun=time.monotonic();maxlag=0.
        for i in range(task['maximum_new_native']):
            assert time.time()<hard-45,'ROOT_OR_TASK_MODEL_RESERVE'
            target=begun+i*.01;time.sleep(max(0,target-time.monotonic()));lag=max(0,time.monotonic()-target);maxlag=max(maxlag,lag)
            assert lag<=.1,'NATIVE_WALL_LAG'
            in_step=True;vehicle.step(*controls(i,task,vehicle.probe_initial_curvature));in_step=False
            body=np.array(vehicle.body())
            assert abs(body[3])<=.13 and abs(body[4])<=.16,'ORIGINAL_BODY_SPEED_OR_YAW_CAP'
            if i%5==0:vehicle.scan()
            if i%100==0:dump(out/'PARTIAL.json',dict(new_actual_native=i+1,body=body.tolist(),maximum_wall_lag_s=maxlag))
        result.update(native=vehicle.finish(),new_actual_native=vehicle.count-task['origin_native_tick'],maximum_wall_lag_s=maxlag)
        replay_started=True;proof=replay(vehicle,hard,out/'physics');replay_complete=True
        result.update(replay=proof,replay_native=proof['replay_native'],status='DIAGNOSTIC_RESPONSE_RECORDED',passed=proof['passed'])
    except BaseException as e:
        result.update(error=repr(e),traceback=traceback.format_exc(),status='FAILED')
        if vehicle is None:vehicle=holder.get('vehicle')
        if vehicle is not None:
            result['vehicle_tasks_initialized']=1;result['historical_native']=task['origin_native_tick']if vehicle.count>=task['origin_native_tick']else vehicle.count
            result['actual_native_completed_lower_bound']=vehicle.count
            interrupted=in_step or getattr(vehicle,'_in_history_step',False)
            result['new_actual_native']=None if interrupted else max(0,vehicle.count-task['origin_native_tick'])
            try:result['partial_native']=vehicle.finish()
            except BaseException as save_error:result['save_error']=repr(save_error)
        else:result['initialization_or_history_count_unknown']=True;result['historical_native']=None
        if replay_started and not replay_complete:result['replay_native']=None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-start)
        if out.exists():dump(out/'RESULT.json',result)
        print('PHASE_DIAGNOSTIC_RESULT '+json.dumps(result,separators=(',',':')),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
