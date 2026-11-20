"""Independent nominal time/coefficients/footprint readback. No physical admission."""
import copy
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,C,O,RAW,read,sha,function,scalar_distance,np

def metadata(package,candidate,body,goal):
    assert package['source_native_tick']==32210 and package['coefficient_source_tick']==32200,'FUTURE_SOURCE'
    assert package['fixed_body_nominal_preparation_is_NOT_actual_coupled_response'] is True
    assert package['complete_physical_admission'] is False and package['full_actual_steering_and_tracking_time_envelope_qualified'] is False,'PHYSICAL_ADMISSION_WITHOUT_RESPONSE_ENVELOPE'
    times=np.asarray(candidate['relative_times']);rear=np.asarray(candidate['rear_path']);speed=np.asarray(candidate['speed']);indices=np.asarray(candidate['interval_indices'])
    wait=candidate['wait_s'];assert wait in [0,5,10,15,20,25,30,35,40]
    assert len(times)==len(rear)==len(speed)==len(indices) and np.isfinite(rear).all()
    assert len(times)>101 and np.max(abs(np.diff(times)-.02))<=1e-8,'TIME_SPACING'
    assert abs(times[0]-wait-4.)<=1e-8,'TIME_OR_PREPARATION_CHANGED'
    assert np.array_equal(indices,np.floor(times/.1+1e-10).astype(int)),'TIME_CELL_BINDING'
    start=np.array([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
    assert np.max(abs(rear[0]-start))<=1e-8,'START_POSE_REWRITTEN'
    length=float(np.linalg.norm(goal[:2]-start[:2]));cruise=(length-.15)/.1;t=times-times[0]
    accel=np.clip(t,0,1);coast=np.clip(t-1,0,cruise);brake=np.clip(t-1-cruise,0,2)
    distance=.05*accel**2+.1*coast+.1*brake-.025*brake**2
    expected_v=np.where(t<=1,-.1*t,-np.maximum(0,.1-.05*brake))
    assert np.max(abs(speed-expected_v))<=1e-8 and np.max(abs(speed))<=.1+1e-8,'NOMINAL_VELOCITY_PROFILE'
    assert np.max(abs(speed[-101:]))<=1e-10,'FULL_TWO_SECOND_STOP_TAIL'
    expected_angle=start[2]+.5*distance
    expected=np.c_[start[0]+(np.sin(expected_angle)-math.sin(start[2]))/-.5,start[1]-(np.cos(expected_angle)-math.cos(start[2]))/-.5,expected_angle]
    assert np.max(abs(expected-rear))<=1e-8,'POSE_CURVATURE_OR_ARC_CLOCK'
    assert np.linalg.norm(rear[-1,:2]-goal[:2])<=.12 and abs(math.atan2(math.sin(rear[-1,2]-goal[2]),math.cos(rear[-1,2]-goal[2])))<=.20,'ORIGINAL_ENDPOINT_CONTRACT'
    return times,rear,speed,indices

def independent_swept(vertices,lower,upper):
    values=[]
    for poly in vertices:
        maximum=-math.inf;negative=-math.inf
        for c,a,b in poly:
            points=[lower,upper];phase=math.atan2(a,b)
            for offset in [0.,math.pi]:
                n=math.ceil((.32*lower-phase-offset)/math.tau);at=(phase+offset+math.tau*n)/.32
                if at<=upper+1e-12:points.append(at)
            sampled=[c+a*math.sin(.32*t)+b*math.cos(.32*t) for t in points]
            maximum=max(maximum,max(sampled));negative=max(negative,-min(sampled))
        values.append((maximum+2e-7,negative+2e-7))
    return np.array([v[0] for v in values]+[v[1] for v in values])+.10

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    frozen=read(O/'AUDIT_TIMED_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
    data=read(O/'FULL_NOMINAL_INTERVAL_DIAGNOSTIC.json');body=read(RAW/'APPLIED_JOURNAL.json')[32210]['body'];goal=np.asarray(read(O/'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['original_segment_unchanged']['poses'][-1])
    model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');origin=model['last_observed_time'];vertices=model['periodic']['vertices'];normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped');maximum_support=0.;maximum_geometry=0.;count=0
    for key,row in data['all_source_intervals'].items():
        index=int(key);lower=origin+max(0,index*.1-.22);upper=origin+(index+1)*.1+.22
        assert max(abs(a-b) for a,b in zip(row['absolute_interval'],[lower,upper]))<=1e-8,'INTERVAL_SHIFTED'
        support=independent_swept(vertices,lower,upper);error=float(np.max(abs(support-row['support'])));maximum_support=max(maximum_support,error);assert error<=1e-8
        expected=clipped(normals,support);actual=np.asarray(row['polygon']);assert expected.shape==actual.shape and np.max(abs(expected-actual))<=1e-8,'POLYGON_SHRUNK_OR_CHANGED'
    proof=[]
    for candidate in data['candidates']:
        times,rear,speed,indices=metadata(data,candidate,body,goal);centers=rear.copy();centers[:,:2]+=.3*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])]
        values=np.array([scalar_distance(p,data['all_source_intervals'][str(i)]['polygon']) for p,i in zip(centers,indices)])
        error=float(np.max(abs(values-candidate['geometry_values'])));maximum_geometry=max(maximum_geometry,error);assert error<=1e-8
        margin=(.1+math.hypot(.74,.375)*.05)*.02/2
        assert candidate['continuous_body_interpolation_allowance_m']>=margin-1e-12
        minimum=min(float(np.minimum(values,candidate['static_values']).min())-margin,candidate['hold_fixed_body_minimum_m']);assert minimum>=.22-1e-8
        assert abs(minimum-candidate['complete_nominal_interval_lower_m'])<=1e-8
        # The recorded40.2s hold covers a full period, hence every later fixed-
        # body hold time as well under this same declared periodic class.
        assert 40.2>=math.tau/.32
        proof.append(dict(wait_s=candidate['wait_s'],independent_nominal_geometry_lower_m=minimum,samples=len(times)));count+=len(times)
    rejects=[];original=data['candidates'][0]
    for name in ['future_source','physical_claim','time_shift','wrong_cell','pose_jump','velocity_overflow','short_stop']:
        package=copy.deepcopy(data);candidate=package['candidates'][0]
        if name=='future_source':package['coefficient_source_tick']=32215
        if name=='physical_claim':package['complete_physical_admission']=True
        if name=='time_shift':candidate['relative_times'][0]+=.1
        if name=='wrong_cell':candidate['interval_indices'][0]+=1
        if name=='pose_jump':candidate['rear_path'][0][0]+=.01
        if name=='velocity_overflow':candidate['speed'][50]=-.2
        if name=='short_stop':candidate['speed'][-30]=-.01
        try:metadata(package,candidate,body,goal)
        except AssertionError:rejects.append(name)
        else:raise AssertionError('TAMPER_ACCEPTED '+name)
    result=dict(passed=True,independent_nominal_witnesses=proof,source_intervals=len(data['all_source_intervals']),full_pose_geometry_cases=count,
        maximum_support_scalar_error=maximum_support,maximum_geometry_scalar_error=maximum_geometry,negative_cases=rejects,
        fixed_body_preparation_not_actual_coupled_response=True,actual_steering_tracking_time_envelope_qualified=False,complete_physical_admission=False,
        models=0,physical_native=0,private_native=0,replay_native=0,wall_s=time.monotonic()-begin)
    p=O/'INDEPENDENT_NOMINAL_TIMING_AUDIT.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert all(sha(R/p)==h for p,h in frozen['files'].items())
    print(json.dumps(result));signal.alarm(0)
if __name__=='__main__':main()
