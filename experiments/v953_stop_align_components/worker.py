"""One immutable component task; model import only after authority and lock."""
import fcntl
import json
import math
import os
import signal
import sys
import time
import traceback
from pathlib import Path
import numpy as np

CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]
OUT=ROOT/'runs/v953_stop_align_components'
sys.path[:0]=[str(CODE),str(ROOT/'experiments/v945_rpccr_observation_liveness'),
               str(ROOT/'experiments/v862_ready_static')]
from authority import authorized


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def controls(index,tick,case):
    if index<18:
        return case['warm']if tick<200 else(case['command']if tick<220 else[0.,0.])
    return case['warm']if tick<200 else([0.,0.]if tick<400 else(case['command']if tick<1600 else[0.,0.]))


def main():
    auth=authorized();index=int(sys.argv[1]);assert 0<=index<=18
    task=json.loads((CODE/'TASKS.json').read_text())[index]
    claim=OUT/('CASE_%02d_CLAIM.json'%index)
    with claim.open('x')as f:json.dump(dict(pid=os.getpid(),at=time.time(),index=index),f)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[min(3,len(cpus)-1)]})
    def halt(*_):raise InterruptedError('COMPONENT_ABSOLUTE_OR_CHILD_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,min(60. if index<18 else 90.,auth['deadline_unix']-20-time.time()))
    # Fail before these imports if no new authority, or sources/tasks changed.
    sys.path.insert(0,str(CODE))
    from physical import create_vehicle,replay
    from command_tube import nominal
    out=ROOT/task['output'];assert not out.exists(),'CASE_ALREADY_ATTEMPTED'
    result=dict(passed=False,index=index,models_attempted=0,actual_native=0,
                fully_recorded_native=0,replay_native=0,private_native=0)
    vehicle=None;in_step=False;replay_started=False;replay_complete=False
    try:
        assert time.time()<auth['deadline_unix']-100,'INSUFFICIENT_COMPONENT_TIME'
        result['models_attempted']=1;vehicle=create_vehicle(out/'physics',task)
        joints=vehicle.m.actuator_trnid[np.asarray(vehicle.adapter.commands.ids[:2]),0]
        q=vehicle.m.jnt_qposadr[joints];dof=vehicle.m.jnt_dofadr[joints]
        assert len(set(joints))==2 and np.all(q>=7)and np.all(dof>=6),'INVALID_STEERING_JOINT_MAPPING'
        ticks=420 if index<18 else 1800
        body=[];steering=[];phases=[];begun=time.monotonic();origin=None
        for i in range(ticks):
            time.sleep(max(0.,begun+i*.01-time.monotonic()))
            assert time.time()<auth['deadline_unix']-20,'ABSOLUTE_MODEL_DEADLINE'
            if i==(200 if index<18 else 400):
                origin=list(vehicle.body())
                if index==18:
                    assert max(abs(origin[3]),abs(origin[4]))<=.03,'HANDOFF_BODY_NOT_STOPPED'
                    assert abs(vehicle.d.qpos[q]).max()<=.01 and abs(vehicle.d.qvel[dof]).max()<=.03,'HANDOFF_STEERING_NOT_ALIGNED'
            v,w=controls(index,i,task)
            in_step=True;vehicle.step(v,w);in_step=False
            body.append(list(vehicle.body()));steering.append([*vehicle.d.qpos[q],*vehicle.d.qvel[dof]]);phases.append(vehicle.adapter.mode)
        finished=vehicle.finish();result.update(actual_native=vehicle.count,fully_recorded_native=len(vehicle.rows))
        replay_started=True;compare=replay(vehicle,auth['deadline_unix'],out/'physics');replay_complete=True
        result['replay_native']=compare['replay_native']
        data=np.asarray(body);servo=np.asarray(steering)
        if index<18:
            actual=data[200:];expected=nominal(origin,*task['command'],np.arange(1,221)*.01)
            position_limit=.04 if task['command'][0]*origin[3]<0 else .02
        else:
            actual=data[400:600];t=np.arange(1,201)*.01
            expected=np.c_[origin[0]+.1*t*math.cos(origin[2]),origin[1]+.1*t*math.sin(origin[2]),np.full(1200,origin[2])]
            position_limit=.04
        position=np.linalg.norm(actual[:,:2]-expected[:,:2],axis=1)
        angle=abs(np.arctan2(np.sin(actual[:,2]-expected[:,2]),np.cos(actual[:,2]-expected[:,2])))
        checks=dict(complete_native=finished['actual_native']==ticks and finished['fully_recorded_native']==ticks,
            all_native_safety=finished['minimum_actual_clearance_m']>=.15 and finished['bad_contacts']==0,
            full_control_replay=compare['passed']and compare['replay_native']==ticks,
            bounded_position=float(position.max())<=position_limit,
            bounded_rotation=float(angle.max())<=.035,
            measured_speed_bound=float(abs(data[:,3]).max())<=.13,
            measured_yaw_bound=float(abs(data[:,4]).max())<=.16,
            settled_by_half_second=bool(np.max(abs(data[(269 if index<18 else 1649):,3:5]))<=.03),
            final_measured_steering_neutral=bool(abs(servo[-1,:2]).max()<=.01 and abs(servo[-1,2:]).max()<=.03))
        if index==18:
            gain=float((data[1599,:2]-origin[:2])@[math.cos(origin[2]),math.sin(origin[2])])
            checks['actual_forward_progress']=gain>=1.
            checks['no_reverse_handoff_request']=all(controls(index,i,task)[0]>=0 for i in range(ticks))
            result['straight_actual_forward_progress_m']=gain
        np.savez_compressed(out/'BODY_AND_STEERING.npz',body=data,steering=servo,origin=origin,expected=expected,phases=np.asarray(phases))
        result.update(passed=all(checks.values()),checks=checks,
            position_residual_max_m=float(position.max()),position_bound_m=position_limit,
            angle_residual_max_rad=float(angle.max()),native=finished,replay=compare)
    except BaseException as error:
        result.update(error=repr(error),traceback=traceback.format_exc())
        if vehicle is not None:
            result['actual_native']=None if in_step else vehicle.count
            result['fully_recorded_native']=len(vehicle.rows)
            if replay_started and not replay_complete:result['replay_native']=None
            try:result['partial']=vehicle.finish()
            except Exception as save_error:result['partial_save_error']=repr(save_error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        result.update(closed=True,closed_unix=time.time(),empirical_only=True)
        from result_contract import save_child
        save_child(out,result)
    return 0 if result['passed']else 1


if __name__=='__main__':sys.exit(main())
