"""Bound the SAME declared pose tube by complete angular coverage, zero models.

This refines a sufficient Lipschitz test, not the trajectory, safety margin or
response assumptions. No measurement of moving response is supplied here.
"""
import copy
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R, O, RAW, read, sha, json, np, load, function, scalar_distance, SimpleNamespace


def validate(data):
    assert data['models'] == data['physical_native'] == data['private_native'] == data['replay_native'] == 0
    assert data['complete_physical_admission'] is False
    assert data['moving_tracking_and_timing_envelope_qualified'] is False
    assert data['translation_bound_m'] == .02 and data['yaw_bound_rad'] == .1
    assert data['angular_nodes'] == 201 and abs(data['angular_half_cell_allowance_m']-math.hypot(.74,.375)*.0005) < 1e-12
    assert data['moving_time_uncertainty_s'] == .2 and data['predictive_margin_m'] == .22
    assert data['original_trajectory_unchanged'] and data['same_state_tube_as_lipschitz_test']
    assert data['full_native_stop_tail_pending_actual_moving_execution']


def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    begin=time.monotonic();frozen=read(O/'OBSERVED_TUBE_SOURCE_FREEZE.json')['files']
    assert all(sha(R/p)==h for p,h in frozen.items())
    data=read(O/'OBSERVED_PREPARATION_BRIDGE.json')
    rear=np.asarray(data['nominal_rear_poses']);n=len(rear)
    offsets=np.linspace(-.1,.1,201)
    full=np.repeat(rear,len(offsets),axis=0);full[:,2]+=np.tile(offsets,n)
    centers=full.copy();centers[:,:2]+=.3*np.c_[np.cos(full[:,2]),np.sin(full[:,2])]
    indices=np.repeat(data['source_cell_indices'],201)
    distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    geometry=load('tube_original_static','experiments/v855_renewal_worker/exact_footprint.py')
    known=read(RAW/'physics/SETUP.json')['known']
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    dynamic=np.empty(len(full))
    for i in np.unique(indices):
        mask=indices==i;dynamic[mask]=distances(centers[mask],data['source_interval_polygons'][str(i)])
    static=geometry.pose_values(field,full);combined=np.minimum(dynamic,static).reshape(n,201)
    limiting=np.argmin(combined,axis=1)
    maximum_error=0.
    for t,k in enumerate(limiting):
        q=t*201+int(k)
        scalar=scalar_distance(centers[q],data['source_interval_polygons'][str(indices[q])])
        maximum_error=max(maximum_error,abs(float(dynamic[q])-scalar))
    assert maximum_error<=1e-8
    angle_allowance=math.hypot(.74,.375)*.0005
    interpolation=data['continuous_interpolation_allowance_m']
    lower=float(combined.min())-.02-angle_allowance-interpolation
    at=np.unravel_index(int(np.argmin(combined)),combined.shape)
    result=dict(models=0,physical_native=0,private_native=0,replay_native=0,
        translation_bound_m=.02,yaw_bound_rad=.1,angular_nodes=201,
        angular_half_cell_allowance_m=angle_allowance,continuous_motion_allowance_m=interpolation,
        moving_time_uncertainty_s=.2,predictive_margin_m=.22,
        full_pose_cases=len(full),raw_minimum_m=float(combined.min()),conditional_full_tube_lower_m=lower,
        conditional_tube_geometry_passed=lower>=.22,
        limiting_time_s=data['move_relative_times_s'][at[0]],limiting_yaw_offset_rad=float(offsets[at[1]]),
        independent_limiting_angle_scalar_checks=n,independent_geometry_error_m=maximum_error,
        original_trajectory_unchanged=True,same_state_tube_as_lipschitz_test=True,
        lipschitz_sufficient_bound_m=data['conditional_moving_tube_lower_m'],
        full_native_stop_tail_pending_actual_moving_execution=True,
        complete_physical_admission=False,moving_tracking_and_timing_envelope_qualified=False,
        proof='all angular grid poses; distance is 1-Lipschitz under .02m translation and R*half-angle cell; time-cell union and continuous motion interpolation retained',
        remaining_gap='Actual moving steering/velocity/braking response must stay in the same .02m/.1rad spatial and +/-.2s timing envelope; no such actual moving response is qualified.',
        wall_s=time.monotonic()-begin)
    validate(result);rejects=[]
    for key,value in [('complete_physical_admission',True),('moving_tracking_and_timing_envelope_qualified',True),('translation_bound_m',0.),('yaw_bound_rad',0.),('moving_time_uncertainty_s',0.),('predictive_margin_m',.15),('angular_half_cell_allowance_m',0.)]:
        bad=copy.deepcopy(result);bad[key]=value
        try:validate(bad)
        except AssertionError:rejects.append(key)
        else:raise AssertionError('TAMPER_ACCEPTED '+key)
    result['negative_cases_rejected']=rejects
    assert all(sha(R/p)==h for p,h in frozen.items())
    target=O/'OBSERVED_BRIDGE_TUBE_AUDIT.json';assert not target.exists()
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');assert read(target)==result
    print(json.dumps(result,allow_nan=False))


if __name__=='__main__':main()
