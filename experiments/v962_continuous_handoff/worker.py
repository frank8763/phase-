"""One real steering-continuous handoff; exact V959case6 prefix, no navigation."""
import fcntl
import importlib.util
import json
import math
import os
import signal
import sys
import time
import traceback
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).parent;OPS=ROOT/'runs/v963_continuous_dynamic'
OUT=ROOT/'runs/v858_nav2_verified/v962/handoff_left'
sys.path[:0]=[str(ROOT/'experiments/v963_continuous_dynamic'),str(ROOT/'experiments/v961_steering_continuity')]
from authority import component_authorized
from steering_continuity import SteeringContinuity
spec=importlib.util.spec_from_file_location('v962_scoped_results',ROOT/'experiments/v953_stop_align_components/result_contract.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)


def nominal_step(pose,v,w):
    x,y,a=pose;dt=.01;b=a+w*dt
    if abs(w)<1e-10:return np.array([x+v*dt*math.cos(a),y+v*dt*math.sin(a),b])
    return np.array([x+v/w*(math.sin(b)-math.sin(a)),y-v/w*(math.cos(b)-math.cos(a)),b])


def execute(vehicle,task,auth,progress,clock=time.time,monotonic=time.monotonic,sleep=time.sleep):
    body=[];steering=[];expected=[];shapes=[];initial=None;current=None;selected=(0.,0.);continuity=SteeringContinuity();begun=monotonic()
    for tick in range(1820):
        sleep(max(0.,begun+tick*.01-monotonic()));assert clock()<auth['deadline_unix']-20
        if tick<420:v,w=task['warm']if tick<200 else(task['command']if tick<220 else(0.,0.))
        else:
            if tick==420:
                initial=np.asarray(vehicle.body());current=initial[:3].copy()
                assert abs(initial[3:5]).max()<=.03,'HANDOFF_BODY_NOT_STOPPED'
            if (tick-420)%5==0:
                now=monotonic();s=vehicle.steering_sample()
                packet=dict(native_tick=vehicle.count,body=list(vehicle.body()),body_measured_at=now,steering=dict(native_tick=vehicle.count,
                    measured_at=now,position=s[:2].tolist(),velocity=s[2:].tolist()))
                requested=(.1,0.)if tick<1620 else(0.,0.)
                shape=continuity.preview(packet,*requested,now);selected=shape['selected'];continuity.commit(shape)
                shapes.append(dict(packet=packet,shape=shape))
            v,w=selected
            if tick<1620:current=nominal_step(current,v,w)
            expected.append(current.copy())
        progress['in_step']=True;vehicle.step(v,w);progress['in_step']=False
        body.append(list(vehicle.body()));steering.append(vehicle.steering_sample())
    return body,steering,expected,shapes,initial


def main():
    auth=component_authorized();assert not OUT.exists(),'HANDOFF_ALREADY_ATTEMPTED'
    with(OPS/'HANDOFF_CLAIM.json').open('x')as f:json.dump(dict(at=time.time(),pid=os.getpid()),f)
    lock=(ROOT/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cpus=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpus[min(3,len(cpus)-1)]})
    def halt(*_):raise InterruptedError('HANDOFF_CHILD_OR_ROOT_DEADLINE')
    signal.signal(signal.SIGTERM,halt);signal.signal(signal.SIGALRM,halt)
    signal.setitimer(signal.ITIMER_REAL,min(100.,auth['deadline_unix']-20-time.time()))
    spec=importlib.util.spec_from_file_location('v962_qualified_physical',ROOT/'experiments/v959_hold_response18/physical.py')
    physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
    task=json.loads((ROOT/'experiments/v959_hold_response18/TASKS.json').read_text())[6]
    result=dict(passed=False,index=0,models_attempted=0,models_initialized=0,actual_native=0,replay_native=0,private_native=0)
    vehicle=None;in_step=False;replay_started=False;replay_complete=False
    try:
        result['models_attempted']=1;vehicle=physical.create_vehicle(OUT/'physics',task);result['models_initialized']=1
        progress={}
        try:body,steering,expected,shapes,initial=execute(vehicle,task,auth,progress)
        finally:in_step=progress.get('in_step',False)
        finished=vehicle.finish();result.update(actual_native=vehicle.count,fully_recorded_native=len(vehicle.rows))
        replay_started=True;comparison=physical.replay(vehicle,auth['deadline_unix'],OUT/'physics');replay_complete=True
        result['replay_native']=comparison['replay_native']
        data=np.asarray(body);servo=np.asarray(steering);expected=np.asarray(expected)
        old=ROOT/'runs/v858_nav2_verified/v959/response_06/physics/NATIVE_TRACE.npz'
        with np.load(old)as f:
            with np.load(OUT/'physics/NATIVE_TRACE.npz')as actual:
                prefix=max(float(abs(actual[k][:420]-f[k]).max())if actual[k][:420].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])
        distance=np.linalg.norm(data[420:,:2]-expected[:,:2],axis=1)
        angle=abs(np.arctan2(np.sin(data[420:,2]-expected[:,2]),np.cos(data[420:,2]-expected[:,2])))
        progress=float((data[1619,:2]-initial[:2])@[math.cos(initial[2]),math.sin(initial[2])])
        checks=dict(full1820=finished['actual_native']==1820 and finished['fully_recorded_native']==1820,
            exact_original420_prefix=prefix<=1e-8,all_native_safety=finished['minimum_actual_clearance_m']>=.15 and finished['bad_contacts']==0,
            complete_own_control_replay=comparison['passed']and comparison['replay_native']==1820,
            original_body_speed=float(abs(data[:,3]).max())<=.13,original_body_yaw=float(abs(data[:,4]).max())<=.16,
            full_forward_and_final_stop_position=float(distance.max())<=.04,full_forward_and_final_stop_heading=float(angle.max())<=.035,
            actual_forward_progress_at_least1m=progress>=1.,final_half_second_settled=bool(abs(data[1669:,3:5]).max()<=.03),
            no_reverse=all(row[1]>=0 for row in vehicle.commands),initial_actual_curvature_preserved=shapes[0]['shape']['mode']=='ANCHORED_TO_MEASURED_STOPPED_STEERING',
            steering_reaches_neutral_during_forward=bool(abs(servo[1619,:2]).max()<=.01 and abs(servo[1619,2:]).max()<=.03))
        result.update(passed=bool(all(checks.values())),checks={k:bool(v)for k,v in checks.items()},native=finished,replay=comparison,
            prefix_state_ctrl_max_error=prefix,position_max_m=float(distance.max()),heading_max_rad=float(angle.max()),actual_forward_progress_m=progress)
        np.savez_compressed(OUT/'HANDOFF_ARRAYS.npz',body=data,steering=servo,origin=initial,expected=expected)
        (OUT/'SHAPING.json').write_text(json.dumps(shapes,indent=2)+'\n')
    except BaseException as error:
        result.update(error=repr(error),traceback=traceback.format_exc())
        if vehicle is not None:
            result['actual_native']=None if in_step else vehicle.count
            result['fully_recorded_native']=len(vehicle.rows)
            if replay_started and not replay_complete:result['replay_native']=None
            try:result['partial']=vehicle.finish()
            except Exception as save_error:result['partial_save_error']=repr(save_error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,closed_unix=time.time(),navigation=0)
        writer.save_child(OUT,result)
    return 0 if result['passed']else 1


if __name__=='__main__':sys.exit(main())
