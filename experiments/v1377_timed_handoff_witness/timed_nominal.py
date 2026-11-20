"""Same registered32210 candidate, full nominal move/brake/hold interval geometry.

An actual coupled-steering response envelope is deliberately NOT substituted
by the fixed-body preparation assumed in this nominal diagnostic.
"""
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,C,O,RAW,read,sha,load,function,scalar_distance,np,SimpleNamespace

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    manifest=read(O/'TIMED_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in manifest['files'].items())
    config=read(C/'TIME_IMPLEMENTATION.json');fixed=read(O/'FIXED_INPUTS.json');assert fixed['models_authorized'] is False
    row=read(RAW/'APPLIED_JOURNAL.json')[32210];body=row['body'];known=read(RAW/'physics/SETUP.json')['known'];model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200
    segment=read(O/'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['original_segment_unchanged'];goal=np.asarray(segment['poses'][-1]);assert segment['gear']==-1
    start=np.array([body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]])
    length=float(np.linalg.norm(goal[:2]-start[:2]));cap=config['speed_m_s'];ta=cap/.1;tb=cap/.05;cruise=(length-cap*ta/2-cap*tb/2)/cap;assert cruise>=0
    moving=ta+cruise+tb;total=math.ceil((moving+2.)/.02)*.02;poses=[];speeds=[];timepoints=np.arange(round(total/.02)+1)*.02
    for t in timepoints:
        if t<=ta:s=.05*t*t;v=.1*t
        elif t<=ta+cruise:s=.05*ta*ta+cap*(t-ta);v=cap
        elif t<=moving:
            z=t-ta-cruise;s=.05*ta*ta+cap*cruise+cap*z-.025*z*z;v=max(0.,cap-.05*z)
        else:s=length;v=0.
        distance=-min(s,length);k=config['reverse_curvature_m_inv'];angle=start[2]+k*distance
        poses.append([start[0]+(math.sin(angle)-math.sin(start[2]))/k,start[1]-(math.cos(angle)-math.cos(start[2]))/k,angle]);speeds.append(-v)
    rear=np.asarray(poses);centers=rear.copy();centers[:,:2]+=.3*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])]
    pos=float(np.linalg.norm(rear[-1,:2]-goal[:2]));heading=abs(math.atan2(math.sin(rear[-1,2]-goal[2]),math.cos(rear[-1,2]-goal[2])))
    assert pos<=.12 and heading<=.20 and max(abs(np.asarray(speeds)))<=.1+1e-8
    swept=load('unchanged_timed_support','experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped');distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    geometry=load('unchanged_static_footprint','experiments/v855_renewal_worker/exact_footprint.py')
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    static=geometry.pose_values(field,rear);normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    origin=model['last_observed_time'];vertices=model['periodic']['vertices'];cache={}
    def polygon(index):
        if index not in cache:
            lo=max(0.,index*.1-.2-.02);hi=(index+1)*.1+.2+.02
            bounds=swept.swept_bounds(vertices,origin+lo,origin+hi)+.1;cache[index]=(clipped(normals,bounds),bounds.tolist(),[origin+lo,origin+hi])
        return cache[index][0]
    corner=math.hypot(.74,.375);interpolation=(.1+corner*.05)*.02/2
    hold=next(r['combined_lower_m'] for r in read(O/'STOPPED_BODY_INTERVAL_PREREQUISITE.json')['rows'] if r['hold_horizon_s']==40. and r['future_time_uncertainty_s']==.2)
    tests=[];independent=0.;candidates=[]
    for wait in config['wait_seconds']:
        times=wait+config['fixed_body_nominal_prepare_s']+timepoints;indices=np.floor(times/.1+1e-10).astype(int);values=np.empty(len(times))
        for index in np.unique(indices):
            mask=indices==index;values[mask]=distances(centers[mask],polygon(int(index)))
        combined=np.minimum(values,static);at=int(np.argmin(combined));lower=min(float(combined.min())-interpolation,hold)
        error=abs(float(values[at])-scalar_distance(centers[at],polygon(int(indices[at]))));independent=max(independent,error);assert error<=1e-8
        result=dict(wait_s=wait,nominal_geometry_passed=lower>=.22-1e-8,complete_nominal_interval_lower_m=lower,limiting_move_time_s=float(timepoints[at]),
            limiting_relative_time_s=float(times[at]),limiting_index=at,position_error_m=pos,heading_error_rad=heading,total_nominal_time_s=float(times[-1]),
            hold_fixed_body_minimum_m=hold,continuous_body_interpolation_allowance_m=interpolation,source_time_uncertainty_s=.2)
        tests.append(result)
        if result['nominal_geometry_passed']:candidates.append(dict(result,relative_times=times.tolist(),rear_path=rear.tolist(),speed=speeds,interval_indices=indices.tolist(),geometry_values=values.tolist(),static_values=static.tolist()))
    supports={str(k):dict(polygon=v[0].tolist(),support=v[1],absolute_interval=v[2]) for k,v in cache.items()}
    result=dict(registered_candidate='TIME_BOUND_NEXT_SEGMENT',source_native_tick=32210,coefficient_source_tick=32200,
        tests=tests,nominal_geometry_passes=len(candidates),candidates=candidates,all_source_intervals=supports,
        actual_start_used_without_cusp_teleport=True,old_nominal_cusp_not_claimed_visited=True,original_subsegment_endpoint_contract_unchanged=True,
        fixed_body_nominal_preparation_is_NOT_actual_coupled_response=True,full_actual_steering_and_tracking_time_envelope_qualified=False,
        complete_physical_admission=False,independent_limiting_geometry_error_m=independent,nominal_kinematic_samples=len(rear),
        models=0,physical_native=0,private_native=0,replay_native=0,wall_s=time.monotonic()-begin)
    path=O/'FULL_NOMINAL_INTERVAL_DIAGNOSTIC.json';assert not path.exists();path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert all(sha(R/p)==h for p,h in manifest['files'].items())
    print(json.dumps(dict(nominal_geometry_passes=len(candidates),tests=tests,full_actual_admission=False,models=0,physical_native=0,wall_s=result['wall_s'])))
    signal.alarm(0)
if __name__=='__main__':main()
