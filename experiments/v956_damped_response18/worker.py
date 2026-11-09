"""One fixed response. Shared executable loop is exercised by no-physics fixtures."""
import fcntl
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path
import numpy as np

CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1];OUT=ROOT/'runs/v956_damped_response18'
sys.path.insert(0,str(CODE))
from authority import authorized
from evaluate import evaluate
sys.path.insert(0,str(ROOT/'experiments/v953_stop_align_components'))
from result_contract import save_child


def controls(tick,task):return task['warm']if tick<200 else(task['command']if tick<220 else[0.,0.])


def execute(vehicle,task,deadline,replay_fn,progress,clock=time.time,sleep=time.sleep,monotonic=time.monotonic):
    body=[];steering=[];phases=[];origin=None;begun=monotonic()
    for tick in range(420):
        sleep(max(0.,begun+tick*.01-monotonic()))
        assert clock()<deadline-20,'ABSOLUTE_MODEL_DEADLINE'
        if tick==200:origin=list(vehicle.body())
        progress['in_step']=True;vehicle.step(*controls(tick,task));progress['in_step']=False
        body.append(list(vehicle.body()));steering.append(vehicle.steering_sample());phases.append(vehicle.adapter.mode)
    finished=vehicle.finish();progress.update(actual_native=vehicle.count,fully_recorded_native=len(vehicle.rows))
    progress['replay_started']=True;comparison=replay_fn(vehicle,deadline)
    progress.update(replay_complete=True,replay_native=comparison['replay_native'])
    data=np.asarray(body);servo=np.asarray(steering)
    metrics,expected=evaluate(data,servo,origin,task)
    checks=metrics.pop('checks')
    checks.update(complete_native=finished['actual_native']==420 and finished['fully_recorded_native']==420,
        all_native_safety=finished['minimum_actual_clearance_m']>=.15 and finished['bad_contacts']==0,
        full_control_replay=comparison['passed']and comparison['replay_native']==420)
    result=dict(passed=all(checks.values()),checks=checks,native=finished,replay=comparison,**metrics)
    arrays=dict(body=data,steering=servo,origin=origin,expected=expected,phases=np.asarray(phases))
    return result,arrays


def main():
    auth=authorized();index=int(sys.argv[1]);assert 0<=index<18
    task=json.loads((CODE/'TASKS.json').read_text())[index]
    with(OUT/('CASE_%02d_CLAIM.json'%index)).open('x')as f:json.dump(dict(index=index,pid=os.getpid(),at=time.time()),f)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[min(3,len(cpus)-1)]})
    def halt(*_):raise InterruptedError('COMPONENT_CHILD_OR_ROOT_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,min(60.,auth['deadline_unix']-20-time.time()))
    sys.path[:0]=[str(CODE),str(ROOT/'experiments/v945_rpccr_observation_liveness'),str(ROOT/'experiments/v862_ready_static')]
    from physical import create_vehicle,replay
    out=ROOT/task['output'];assert not out.exists(),'CASE_ALREADY_ATTEMPTED'
    result=dict(passed=False,index=index,models_attempted=0,models_initialized=0,actual_native=0,
        fully_recorded_native=0,replay_native=0,private_native=0)
    progress=dict(in_step=False,replay_started=False,replay_complete=False)
    vehicle=None
    try:
        assert time.time()<auth['deadline_unix']-100
        result['models_attempted']=1;vehicle=create_vehicle(out/'physics',task);result['models_initialized']=1
        item,arrays=execute(vehicle,task,auth['deadline_unix'],lambda v,d:replay(v,d,out/'physics'),progress)
        result.update(item,actual_native=progress['actual_native'],fully_recorded_native=progress['fully_recorded_native'],replay_native=progress['replay_native'])
        np.savez_compressed(out/'BODY_AND_STEERING.npz',**arrays)
    except BaseException as error:
        result.update(error=repr(error),traceback=traceback.format_exc())
        if vehicle is not None:
            result['actual_native']=None if progress['in_step']else vehicle.count
            result['fully_recorded_native']=len(vehicle.rows)
            result['replay_native']=None if progress['replay_started']and not progress['replay_complete']else progress.get('replay_native',0)
            try:result['partial']=vehicle.finish()
            except Exception as save_error:result['partial_save_error']=repr(save_error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time(),empirical_only=True)
        save_child(out,result)
    return 0 if result['passed']else 1


if __name__=='__main__':sys.exit(main())
