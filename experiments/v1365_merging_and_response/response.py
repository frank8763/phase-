"""Saved actual response calibration. Reads trace, never simulates a vehicle."""
import os
import time
from common import *


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'SAVED_RESPONSE.json';assert not target.exists()
    journal=read(RAW/'APPLIED_JOURNAL.json');setup=read(RAW/'physics/SETUP.json');initial=read(RAW/'INITIAL_PACKET.json')
    with np.load(RAW/'physics/NATIVE_TRACE.npz') as z:trace={k:z[k].copy() for k in z.files}
    assert len(journal)==len(trace['time'])==19845 and all(z['applied'] for z in journal)
    body=np.array([z['body'] for z in journal]);enc=np.array([z['encoders'] for z in journal]);ctrl=np.array([z['last_ctrl'] for z in journal])
    requested=np.array([z['upstream_request'][:2] for z in journal]);actual=np.array([z['request'][:2] for z in journal])
    addresses=setup['steering_qpos_addresses'];velocities=setup['steering_qvel_addresses']
    errors=dict(position=float(np.max(abs(body[1:,:2]-trace['qpos'][:-1,:2]))),
                steering_position=float(np.max(abs(enc[1:,:2]-trace['qpos'][:-1,addresses]))),
                steering_velocity=float(np.max(abs(enc[1:,2:]-trace['qvel'][:-1,velocities]))),
                control=float(np.max(abs(ctrl[1:]-trace['ctrl'][:-1,setup['actuator_ids']]))))
    assert max(errors.values())<=1e-8,'SAVED_FEEDBACK_TRACE_ALIGNMENT'
    mask=(abs(requested[:,0]-.1)<1e-10)&(abs(requested[:,1])<.001)&(abs(actual[:,0]-.1)<1e-10)
    end=next((i for i,v in enumerate(mask) if not v),len(mask));assert end>=500
    duration=min(end,1001);times=np.arange(duration)*.01;measured=body[:duration]
    projection=(measured[:,:2]-body[0,:2])@np.array([math.cos(body[0,2]),math.sin(body[0,2])])
    nominal=np.where(times<=1.,.05*times**2,.05+.1*(times-1.))
    difference=projection-nominal
    def sustained_time(threshold):
        good=measured[:,3]>=threshold
        return next((i*.01 for i in range(len(good)-49) if good[i:i+50].all()),None)
    checkpoints=[]
    for seconds in [1.,2.,5.,10.]:
        tick=round(seconds/.01)
        if tick<duration:checkpoints.append(dict(native_tick=tick,time_s=seconds,measured_longitudinal_speed_m_s=float(body[tick,3]),
            actual_progress_m=float(projection[tick]),nominal_progress_m=float(nominal[tick]),difference_m=float(difference[tick])))
    bad=np.flatnonzero(abs(difference)>.02+1e-8)
    acceleration=dict(matched_initial_native=duration,original_matched_interval_native=end,
        nominal_acceleration_duration_s=1.,nominal_speed_m_s=.1,
        actual_90percent_speed_sustained_halfsecond_s=sustained_time(.09),
        actual_95percent_speed_sustained_halfsecond_s=sustained_time(.095),
        checkpoints=checkpoints,maximum_absolute_progress_error_m=float(abs(difference).max()),
        nominal200ms_at_point1mps_distance_m=.02,
        first_outside20mm_nominal_progress_native=None if not len(bad) else int(bad[0]),
        original200ms_actual_timing_capture_qualified=not bool(len(bad)),
        remark='Measured near-straight0.1 command step; nominal1s speed ramp is different and cannot be substituted online.')
    # Every original zero request interval lasting at least200native ticks.
    zero=(abs(requested).max(axis=1)<=1e-10)&(abs(actual).max(axis=1)<=1e-10)
    starts=np.flatnonzero(zero&~np.r_[False,zero[:-1]]);ends=np.flatnonzero(zero&~np.r_[zero[1:],False])+1;stops=[]
    for start,finish in zip(starts,ends):
        if finish-start<200:continue
        rest=(abs(body[start:finish,3:]).max(axis=1)<=.003)&(abs(enc[start:finish,2:]).max(axis=1)<=.03)&(abs(ctrl[start:finish,2:]).max(axis=1)<=1e-10)
        first=next((i for i in range(max(0,len(rest)-19)) if rest[i:i+20].all()),None)
        at=None if first is None else int(start+first)
        travelled=np.linalg.norm(np.diff(np.vstack([body[start:finish,:2],trace['qpos'][finish-1,:2]]),axis=0),axis=1)
        stop=dict(start_native=int(start),finish_native=int(finish),zero_native=int(finish-start),start_body=body[start].tolist(),
            first_full_measured_rest_sustained200ms_native=at,
            full_measured_rest_after_s=None if first is None else first*.01,
            both_original200zero_and_full_rest_after_s=None if first is None else max(200,first)*.01,
            maximum_path_drift_during_zero_m=float(travelled.sum()),
            steering_position_drift_rad=float(abs(enc[start:finish,:2]-enc[start,:2]).max()))
        stops.append(stop)
    # Nominal cruise can change curvature instantaneously, while the unchanged
    # actuator law explicitly limits virtual steering center to.6rad/s.
    max_center=math.atan(.6*.5);opposite_time=2*max_center/.6
    # Saved command reversals of steering sign are descriptive only: varying
    # speed/targets do not give controlled opposite-extreme identification.
    curvature=np.divide(requested[:,1],requested[:,0],out=np.zeros(len(journal)),where=abs(requested[:,0])>=.005)
    changes=np.flatnonzero((abs(np.diff(curvature))>.1)&(abs(requested[:-1,0])>=.005)&(abs(requested[1:,0])>=.005))
    steering=dict(unchanged_nominal_wheelbase_m=.6,nominal_extreme_curvature_m_inv=.5,
        unchanged_virtual_steering_rate_rad_s=.6,opposite_extreme_center_angle_change_rad=2*max_center,
        minimum_commanded_opposite_extreme_transition_s=opposite_time,
        nominal_cruise_primitive_instantaneous_curvature_switch_qualified=False,
        matching_controlled_opposite_extreme_saved_experiment=False,large_recorded_upstream_curvature_changes=int(len(changes)),
        parked_steering_uses_separate_explicit_target=True,zero_twist_hold_does_not_establish_requested_new_steering_angle=True)
    result=dict(executed=True,feedback_trace_alignment_errors=errors,acceleration=acceleration,stops=stops,steering=steering,
        source_journal_sha256=sha(RAW/'APPLIED_JOURNAL.json'),source_trace_sha256=sha(RAW/'physics/NATIVE_TRACE.npz'),
        actual_recorded_native_reviewed=len(journal),new_models=0,new_physical_native=0,new_replay_native=0,
        dynamics_or_timing_capture_qualified=False,wall_s=time.monotonic()-begin)
    dump(target,result);print(json.dumps({k:v for k,v in result.items() if k not in ['stops']}));print(json.dumps(stops))


if __name__=='__main__':main()
