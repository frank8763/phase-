"""Bounded offline diagnostic engine, physical calls only via run_phase.sh."""
import fcntl,json,os,signal,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
from authority import authorize
from execution import execute
from schedule import controls
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')

def main():
    task=json.loads(Path(sys.argv[1]).read_text());end=authorize(task);out=Path(task['output'])
    assert out.is_relative_to(R/'runs/v858_nav2_verified/v995')and not out.exists()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));assert len(cpus)>=4;os.sched_setaffinity(0,{cpus[3]})
    wall=time.time();begun=time.monotonic();hard=min(end-10,wall+300);restore_end=min(hard-100,wall+180)
    v=None;holder={};loop=None;replay_started=False;replay_done=False
    result=dict(passed=False,status='INITIALIZING',vehicle_tasks_initialized=None,historical_native=None,new_actual_native=0,replay_native=0,private_native=0,
        stage_deadline_unix=end,task_hard_deadline_unix=hard,diagnostic_only=True,execution_mode=task['execution_mode'],real_time_qualified=False)
    def stop(*_):raise InterruptedError('ROOT_OR_TASK_STOP')
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,max(.001,hard-time.time()-5))
    def guard():assert time.time()<restore_end and time.monotonic()<begun+180,'RESTORE_OR_ROOT_DEADLINE'
    def progress(v,phase):dump(out/'STARTUP_PROGRESS.json',dict(phase=phase,native_tick=v.count,at=time.time()))
    try:
        result['environment_initialization_attempted']=True
        from physical import create_vehicle,replay
        v=create_vehicle(out/'physics',task,guard,progress,lambda vehicle:holder.update(vehicle=vehicle));result['vehicle_tasks_initialized']=1
        result['historical_native']=v.count;result['status']='RUNNING_FIXED_STIMULUS'
        loop=execute(v,task,controls,out/'execution',hard);result['execution']=loop
        assert loop['passed'],'OFFLINE_EXECUTION_FAILURE '+str(loop.get('error')or loop.get('timing_save_error'))
        result.update(native=v.finish(),new_actual_native=v.count-task['origin_native_tick'])
        replay_started=True;proof=replay(v,hard,out/'physics');replay_done=True
        result.update(replay=proof,replay_native=proof['replay_native'],status='FIXED_RESPONSE_RECORDED',passed=proof['passed'])
    except BaseException as e:
        result.update(error=repr(e),traceback=traceback.format_exc(),status='FAILED')
        if v is None:v=holder.get('vehicle')
        if v is not None:
            result['vehicle_tasks_initialized']=1;result['historical_native']=min(v.count,task['origin_native_tick'])
            interrupted=getattr(v,'_in_history_step',False)or(loop is not None and loop['new_native_count']is None)
            result['new_actual_native']=None if interrupted else max(0,v.count-task['origin_native_tick']);result['actual_native_completed_lower_bound']=v.count
            try:result['partial_native']=v.finish()
            except BaseException as e:result['save_error']=repr(e)
        else:result['initialization_or_history_count_unknown']=True;result['historical_native']=None;result['new_actual_native']=None
        if replay_started and not replay_done:
            result['replay_native']=None
            p=out/'physics/REPLAY_PROGRESS.json'
            if p.exists():result['replay_native_completed_lower_bound']=json.loads(p.read_text())['executed_replay_native']
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time(),wall_s=time.monotonic()-begun)
        if out.exists():dump(out/'RESULT.json',result)
        print('PHASE_DIAGNOSTIC_RESULT '+json.dumps(result,separators=(',',':')),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
