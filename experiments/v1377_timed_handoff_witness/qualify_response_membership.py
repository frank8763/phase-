"""Saved measured preparation + explicitly artificial moving audit fixtures."""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,O,read,sha,json
from response_membership_contract import audit,rear


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'RESPONSE_MEMBERSHIP_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    raw=R/'runs/v858_nav2_verified/v1378/steering_response';rows=read(raw/'APPLIED_JOURNAL.json')[32210:];final=read(raw/'FINAL_PACKET.json')
    preparation=[]
    for row in rows:
        preparation.append(dict(native_tick=row['before_native'],sim_time=row['before_native']*.01,
            relative_time_s=(row['before_native']-32210)*.01,body=row['body'],ctrl=row['last_ctrl'],
            steering_velocity=row['encoders'][2:],command=row['request'][:2]))
    preparation.append(dict(native_tick=final['native_tick'],sim_time=final['sim_time'],relative_time_s=(final['native_tick']-32210)*.01,
        body=final['body'],ctrl=final['controller_memory']['last_ctrl'],steering_velocity=final['steering']['velocity'],command=[0.,0.]))
    # Journal's tick binding is checked against the saved actual clock endpoint;
    # intermediate sim_time here is tick-derived, not an extra measured clock.
    fixed=rear(rows[0]['body']);prep_ref=[dict(relative_time_s=r['relative_time_s'],rear=fixed) for r in preparation]
    prep=audit(preparation,prep_ref,origin_tick=32210,source_tick=32200,evidence_kind='ACTUAL_SAVED_PREPARATION',stage='PREPARATION')
    actual_yaw=max(abs(math.atan2(math.sin(r['body'][2]-rows[0]['body'][2]),math.cos(r['body'][2]-rows[0]['body'][2]))) for r in preparation)
    prior=read(raw/'FINAL_INDEPENDENT_AUDIT.json');assert abs(actual_yaw-prior['maximum_body_yaw_change_rad'])<=1e-12
    moving=read(O/'NATIVE_CLOCK_COMMAND_CONTRACT.json');ref=[dict(relative_time_s=t,rear=p) for t,p in zip(moving['relative_times_s'],moving['command_arc_rear_poses'])]
    fixture=[]
    for i,row in enumerate(ref):
        x,y,yaw=row['rear'];body=[x+.3*math.cos(yaw),y+.3*math.sin(yaw),yaw,0.,0.]
        fixture.append(dict(native_tick=32600+i,sim_time=(32600+i)*.01,relative_time_s=row['relative_time_s'],
            body=body,ctrl=[0.,0.,0.,0.],steering_velocity=[0.,0.],command=moving['software_trace'][i]['admitted'] if i<len(moving['software_trace']) else [0.,0.]))
    args=dict(origin_tick=32600,source_tick=32200,evidence_kind='SOFTWARE_REFERENCE_FIXTURE',stage='MOVING')
    ideal=audit(fixture,ref,**args);assert not ideal['actual_moving_response_qualified']
    delayed=copy.deepcopy(fixture)
    for i,row in enumerate(delayed):row['body']=fixture[max(0,i-10)]['body'][:]
    lag=audit(delayed,ref,**args);assert not lag['actual_moving_response_qualified']
    negatives=[]
    changes={
        'position_outside_all_candidates':lambda s:s[500]['body'].__setitem__(0,s[500]['body'][0]+.1),
        'yaw_outside_all_candidates':lambda s:s[500]['body'].__setitem__(2,s[500]['body'][2]+.3),
        'tick_gap':lambda s:s[500].__setitem__('native_tick',s[500]['native_tick']+1),
        'actual_clock_shift':lambda s:s[500].__setitem__('sim_time',s[500]['sim_time']+.01),
        'reference_time_binding':lambda s:s[500].__setitem__('relative_time_s',s[500]['relative_time_s']+.3),
        'nonzero_stop_tail':lambda s:s[-100].__setitem__('command',[-.005,.0025]),
        'final_body_not_rest':lambda s:s[-1]['body'].__setitem__(3,.004),
        'final_steering_not_rest':lambda s:s[-1]['steering_velocity'].__setitem__(0,.04),
        'final_rear_not_zero':lambda s:s[-1]['ctrl'].__setitem__(2,.001),
        'nonfinite_body':lambda s:s[500]['body'].__setitem__(0,math.nan),
    }
    for name,change in changes.items():
        bad=copy.deepcopy(fixture);change(bad)
        try:audit(bad,ref,**args)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('TAMPER_ACCEPTED '+name)
    for name,changed in [('future_source',dict(source_tick=32601)),('fixture_relabelled_actual',dict(evidence_kind='ACTUAL_SAVED_PREPARATION'))]:
        badargs=dict(args);badargs.update(changed)
        try:audit(fixture,ref,**badargs)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('PROVENANCE_TAMPER_ACCEPTED '+name)
    # Confirm a candidate can fit instantaneous geometry yet violate timing.
    too_late=copy.deepcopy(fixture)
    for i,row in enumerate(too_late):row['body']=fixture[max(0,i-80)]['body'][:]
    try:audit(too_late,ref,**args)
    except AssertionError:negatives.append('excessive_phase_delay')
    else:raise AssertionError('DELAY_TAMPER_ACCEPTED')
    assert len(negatives)==13
    result=dict(passed=True,models=0,physical_native=0,private_native=0,replay_native=0,
        measured_saved_preparation=prep,measured_preparation_body_yaw_readback_error=abs(actual_yaw-prior['maximum_body_yaw_change_rad']),
        intermediate_preparation_time_is_tick_derived_not_new_clock_measurement=True,
        ideal_moving_fixture=ideal,point_one_second_lag_fixture=lag,
        moving_fixtures_are_explicitly_artificial_not_physical_trajectories=True,
        negative_cases=negatives,actual_moving_response_qualified=False,physical_admission=False,
        monitor_scope='discrete sufficient monotone sample membership only; does not prove future invariant/complete braking or continuous plant dynamics',
        next_gap='No saved actual moving response for this schedule; source/authenticity/full ctrl/model/contact/replay/continuous reserves remain independently required.',
        wall_s=time.monotonic()-begin)
    assert all(sha(R/p)==h for p,h in frozen.items())
    p=O/'RESPONSE_MEMBERSHIP_QUALIFICATION.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(p)==result
    print(json.dumps(dict(passed=True,negative_cases=len(negatives),saved_preparation_samples=prep['samples'],preparation_rear_residual_m=prep['maximum_rear_position_residual_m'],preparation_yaw_residual_rad=prep['maximum_yaw_residual_rad'],moving_fixture_samples=ideal['samples'],lag_fixture_max_time_s=lag['maximum_phase_time_residual_s'],models=0,physical_native=0,replay_native=0,actual_moving_response_qualified=False,wall_s=result['wall_s'])))


if __name__=='__main__':main()
