"""Measured V1376 drive/brake records vs a request-arc proxy; zero models.

These are different initial states and request profiles from the new32210
schedule. Results diagnose sensitivity, never qualify its response envelope.
"""
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json


def rear(body):
    return [body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]]


def reference(origin,v,k,n,moving):
    distance=v*min(n,moving)*.01;yaw=origin[2]+k*distance
    return [origin[0]+(math.sin(yaw)-math.sin(origin[2]))/k,
            origin[1]-(math.cos(yaw)-math.cos(origin[2]))/k,yaw]


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'SAVED_DRIVE_SOURCE_FREEZE.json')['files'];assert all(sha(R/p)==h for p,h in frozen.items())
    sources=[]
    for task in ['capture_main','capture_repeat']:
        raw=R/'runs/v858_nav2_verified/v1376'/task
        assert read(raw/'FINAL_INDEPENDENT_AUDIT.json')['passed']
        rows=read(raw/'APPLIED_JOURNAL.json');final=read(raw/'FINAL_PACKET.json');results=[]
        for name,start,stop,end in [('reverse_original_steering',9390,9675,9875),('forward_prepared_steering',10395,10575,10775)]:
            selected=rows[start:stop];v,w=selected[0]['request'][:2];k=w/v;origin=rear(selected[0]['body'])
            assert all(r['request']==[v,w,False] and r['applied'] for r in selected)
            assert all(r['request']==[0.,0.,False] and r['applied'] for r in rows[stop:end]) and end-stop==200
            body=[rows[i]['body'] if i<len(rows) else final['body'] for i in range(start,end+1)]
            positions=[rear(b) for b in body];reference_poses=[reference(origin,v,k,i,stop-start) for i in range(len(body))]
            instantaneous=[];matched=[];first_failure=None;previous=0;match_failed=False
            for i,(actual,ref) in enumerate(zip(positions,reference_poses)):
                dp=math.dist(actual[:2],ref[:2]);dy=abs(math.atan2(math.sin(actual[2]-ref[2]),math.cos(actual[2]-ref[2])))
                instantaneous.append(dict(offset_native=i,position_error_m=dp,yaw_error_rad=dy))
                if first_failure is None and (dp>.02+1e-8 or dy>.1+1e-8):first_failure=i
                candidates=[]
                for j in range(max(previous,i-20),min(len(body)-1,i+20)+1):
                    p=reference_poses[j];a=math.dist(actual[:2],p[:2]);b=abs(math.atan2(math.sin(actual[2]-p[2]),math.cos(actual[2]-p[2])))
                    if a<=.02+1e-8 and b<=.1+1e-8:candidates.append((j,a,b))
                if not candidates:
                    match_failed=True;matched.append(dict(offset_native=i,matched=False));continue
                # Freeze earliest-match memory only along an uninterrupted chain.
                j,a,b=candidates[0]
                if not match_failed:previous=j
                matched.append(dict(offset_native=i,matched=True,reference_offset_native=j,position_error_m=a,yaw_error_rad=b,time_error_s=abs(i-j)*.01))
            measured_v=[r['body'][3] for r in selected]
            t90=next((i*.01 for i,s in enumerate(measured_v) if s*v>0 and abs(s)>=.09),None)
            stopping=rows[stop:end]
            settled=next((i*.01 for i in range(len(stopping)) if all(max(abs(x) for x in r['body'][3:])<=.003 for r in stopping[i:])),None)
            empirical_accel=max(abs((body[i+1][3]-body[i][3])/.01) for i in range(len(body)-1))
            item=dict(segment=name,start_native=start,drive_end_native=stop,tail_end_native=end,drive_native=stop-start,actual_stop_native=end-stop,
                original_request=[v,w],initial_actual_front=rows[start]['encoders'][:2],initial_control=rows[start]['last_ctrl'],
                maximum_direct_request_arc_rear_error_m=max(p['position_error_m'] for p in instantaneous),
                maximum_direct_request_arc_yaw_error_rad=max(p['yaw_error_rad'] for p in instantaneous),
                direct_2cm_pointwise_proxy_passed=first_failure is None,first_direct_tube_failure_offset_native=first_failure,
                plus_minus_point2_monotone_discrete_proxy_passed=not match_failed,
                actual_time_to90percent_of_point1_speed_s=t90,measured_body_peak_abs_speed_m_s=max(abs(s) for s in measured_v),
                actual_braking_rear_displacement_m=math.dist(positions[stop-start][:2],positions[-1][:2]),
                empirical_body_acceleration_max_m_s2=empirical_accel,measured_tail_sustained_body_rest_after_s=settled,
                final_actual_speed_m_s=body[-1][3],instantaneous_residuals=instantaneous,discrete_time_matching=matched,
                different_initial_state_and_request_profile_than32210=True,not_a32210_response_certificate=True)
            results.append(item)
        sources.append(dict(task=task,segments=results))
    for a,b in zip(sources[0]['segments'],sources[1]['segments']):
        assert {k:v for k,v in a.items()}=={k:v for k,v in b.items()},'ORIGINAL_REPEAT_RESPONSE_DIAGNOSIS_NOT_EXACT'
    assert any(not x['direct_2cm_pointwise_proxy_passed'] for x in sources[0]['segments'])
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        scope='saved actual V1376 drive and brake samples only; different state/profile from registered32210 moving schedule',
        same_version_main_repeat_diagnostic_exact=True,actual_moving_response_for32210_qualified=False,
        physical_admission=False,no_new_candidate=True,sources=sources,
        finding='Original actual components pass their endpoint gates, while pointwise request-arc reference can exceed2cm; instantaneous target legality or final arrival does not certify the declared timed tube.',
        next_required='Qualify a response-aware executable reference and phase synchronization on the exact32210 schedule before physical admission; retain source-clock occupancy and full braking reserves.',
        wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'SAVED_DRIVE_RESPONSE_DIAGNOSTIC.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps(dict(models=0,physical_native=0,physical_admission=False,main_repeat_exact=True,segments=[{k:v for k,v in x.items() if k not in ['instantaneous_residuals','discrete_time_matching','initial_actual_front','initial_control']} for x in sources[0]['segments']]),allow_nan=False))


if __name__=='__main__':main()
