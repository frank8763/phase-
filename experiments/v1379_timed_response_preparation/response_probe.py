"""Original frozen response model, canonical isolated locked analytical probe.

No MuJoCo/vehicle construction. Count all response steps, including old saved
calibration, separately from physical integration and physical own replay.
"""
import importlib.abc
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import fcntl
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name


def read(p):return json.loads(Path(p).read_text())


def dump(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')


class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('NO_PHYSICAL_PREPARATION '+name)


def main():
    assert not (O/'RESPONSE_MODEL_PROBE.json').exists(),'ALREADY_PROBED'
    import hashlib
    freeze=read(O/'RESPONSE_SOURCE_FREEZE.json')['files'];assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items())
    authority=read(O/'SUPPLEMENTAL_AUTHORITY.json');assert authority['additional_component_limit']==2 and authority['absolute_deadline_unix']==1795165200
    assert time.time()<1795165200-300
    sys.meta_path.insert(0,NoPhysical())
    begin=time.monotonic();steps=0;working=None;result=dict(passed=False,models=0,physical_native=0,physical_replay_native=0,analytical_native=0)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('RESPONSE_PREPARATION_STOP')))
    signal.alarm(max(1,int(min(1800,1795165200-time.time()-120))))
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
            from logic import Predictor,initial,kernel,Adapter
            import numpy as np
            sys.path.insert(0,str(R/'experiments/v1377_timed_handoff_witness'))
            from native_clock_contract import Timeline
            from gear_handoff import GearHandoff
            # resource_policy supplies the original Phase CPU2/one-thread domain.
            assert sorted(os.sched_getaffinity(0))==[2]
            def advance(p,v,w):
                nonlocal steps
                assert steps<250000 and time.time()<1795165200-100
                state,u=p.step(v,w,False);steps+=1;return state,u
            def body(s):return [float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])]
            def rear(s):return np.array([s[0]-.3*math.cos(s[2]),s[1]-.3*math.sin(s[2]),s[2]])
            def enc(s):
                k=math.tan(s[6])/.6;dk=(1+math.tan(s[6])**2)/.6*s[7];q=[];dq=[]
                for sign in [1.,-1.]:
                    den=1-sign*.27*k;a=.6*k/den;q.append(math.atan(a));dq.append(.6*dk/(den*den*(1+a*a)))
                return q+dq
            def packet(row,trace,i):
                b=row['body'];q=trace['qvel'][i-1]
                return dict(body=b,body_lateral=float(-q[0]*math.sin(b[2])+q[1]*math.cos(b[2])),
                    steering=dict(position=row['encoders'][:2],velocity=row['encoders'][2:]),
                    controller_memory=dict(last_ctrl=row['last_ctrl'],integral=row['integral']),
                    coupled_episode=False,steering_motion_active=row['steering_motion_active_before'])
            calibration=[]
            for task in ['capture_main','capture_repeat']:
                raw=R/'runs/v858_nav2_verified/v1376'/task;rows=read(raw/'APPLIED_JOURNAL.json');final=read(raw/'FINAL_PACKET.json');setup=read(raw/'physics/SETUP.json')
                assert read(raw/'FINAL_INDEPENDENT_AUDIT.json')['passed']
                with np.load(raw/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k] for k in ['qpos','qvel']}
                for name,start,end in [('reverse9390',9390,9875),('forward10395',10395,10775)]:
                    p=Predictor(setup,initial(packet(rows[start],trace,start)),kernel.PARAMETERS);p.adapter.__class__=Adapter
                    p.adapter._steering_motion_active=False;p.adapter.parked_target=None
                    states=[p.state.copy()];maximum_position=maximum_yaw=maximum_v=0.;details=[]
                    for i in range(start,end):
                        row=rows[i];p.adapter.parked_target=row['parked_target'];s,u=advance(p,*row['request'][:2]);states.append(s.copy())
                        actual=rows[i+1]['body'] if i+1<len(rows) else final['body']
                        error=float(np.linalg.norm(rear(s)[:2]-rear(actual)[:2]));angle=abs(math.atan2(math.sin(s[2]-actual[2]),math.cos(s[2]-actual[2])))
                        maximum_position=max(maximum_position,error);maximum_yaw=max(maximum_yaw,angle);maximum_v=max(maximum_v,abs(s[3]-actual[3]))
                        details.append(dict(native=i+1,rear_error_m=error,yaw_error_rad=angle,speed_error_m_s=abs(float(s[3])-actual[3])))
                    calibration.append(dict(task=task,segment=name,source_actual_start=start,source_actual_end=end,
                        rear_error_m=maximum_position,yaw_error_rad=maximum_yaw,speed_error_m_s=maximum_v,
                        same_time_2cm_point1rad_passed=maximum_position<=.02 and maximum_yaw<=.1,
                        finite_saved_case_only=True,not_same32210_response_qualification=True,errors=details))
            raw=R/'runs/v858_nav2_verified/v1378/steering_response';setup=read(raw/'physics/SETUP.json');origin=read(raw/'FINAL_PACKET.json')
            goal=read(R/'runs/v1377_timed_handoff_witness/ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['original_segment_unchanged']['poses'][-1]
            p=Predictor(setup,initial(origin),kernel.PARAMETERS);p.adapter.__class__=Adapter;p.adapter._steering_motion_active=False;p.adapter.parked_target=None
            length=read(R/'runs/v1377_timed_handoff_witness/NATIVE_CLOCK_COMMAND_CONTRACT.json')['original_nominal_length_m']
            gate=GearHandoff();gate.gear=1;gate.last_tick=32599;timeline=Timeline(gate,length)
            states=[p.state.tolist()];controls=[];journal=[];memory=[]
            for tick in range(32600,34600):
                row=timeline.step(tick,body(p.state),p.adapter.last.tolist(),enc(p.state));memory.append([*p.adapter.last.tolist(),float(p.adapter.integral)])
                s,u=advance(p,*row['admitted']);states.append(s.tolist());controls.append(u.tolist());journal.append(row)
                if row['state']=='DONE':break
            else:raise AssertionError('PREDICTED_SCHEDULE_NOT_COMPLETE')
            ending=rear(p.state);position=float(np.linalg.norm(ending[:2]-goal[:2]));heading=abs(math.atan2(math.sin(ending[2]-goal[2]),math.cos(ending[2]-goal[2])))
            checks=dict(saved_calibration_all_within_declared_position_yaw=all(x['same_time_2cm_point1rad_passed'] for x in calibration),
                predicted_endpoint=position<=.12 and heading<=.20,predicted_full200_zero_tail=all(x['admitted']==[0.,0.] for x in journal[-200:]),
                predicted_body_rest=max(abs(p.state[k]) for k in [3,4,5])<=.003,
                predicted_rear_targets_zero=max(abs(x) for x in p.adapter.last[2:])<=1e-10,
                predicted_body_limits=bool((abs(np.asarray(states)[:,3:6])<=np.asarray([.13,.03,.16])+1e-8).all()))
            result.update(passed=all(checks.values()),checks=checks,calibration=calibration,
                origin_native=32600,origin_packet=origin,source_coefficient_native=32200,
                predicted_states=states,predicted_ctrl=controls,predicted_memory=memory,predicted_schedule=journal,
                predicted_position_error_m=position,predicted_heading_error_rad=heading,
                physical_admission=False,actual_moving_response_qualified=False,
                next_gate='Full original causal-time footprint and complete braking reserve, independent response checks and complete physical entry; no physics on any preparation failure')
        except BaseException as exc:
            import traceback
            result.update(passed=False,error=repr(exc),traceback=traceback.format_exc())
        finally:
            signal.alarm(0);result.update(analytical_native=steps,wall_s=time.monotonic()-begin,
                source_unchanged=all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in freeze.items()),closed=True)
            dump(O/'RESPONSE_MODEL_PROBE.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['calibration','predicted_states','predicted_ctrl','predicted_memory','predicted_schedule','origin_packet']},allow_nan=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
