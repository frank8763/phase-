"""Exact original next segment against same-prefix all-future polygon; geometry only."""
import json
import math
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,C,O,RAW,read,sha,load,function,scalar_distance,np,SimpleNamespace

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    manifest=read(O/'SEGMENT_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in manifest['files'].items())
    fixed=read(O/'FIXED_INPUTS.json');assert fixed['models_authorized'] is False
    body=read(RAW/'APPLIED_JOURNAL.json')[32210]['body'];known=read(RAW/'physics/SETUP.json')['known'];model=read(RAW/'CAUSAL_PREDICTION_MODEL.json');assert model['periodic']['source_tick']==32200
    queue=[];segment=None
    for e in read(RAW/'SEGMENT_RECORDS.json'):
        if e['event']=='INSTALL_ORDERED_ROUTE':queue=e['segments'][1:]
        elif e['event']=='CUSP_NEXT_SEGMENT_CHECK':
            if e['native_tick']==32210:segment=queue[0];break
            queue=queue[1:] if e['accepted'] else []
    assert segment is not None
    swept=load('same_causal_swept_function','experiments/v1020_terminal_two_route_development/periodic_support.py')
    clipped=function('experiments/v1366_canonical_timed_lattice/build_polygons.py','clipped');distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    geometry=load('original_static_rectangular_footprint','experiments/v855_renewal_worker/exact_footprint.py')
    normals=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
    stamp=model['last_observed_time'];period=math.tau/.32;bounds=swept.swept_bounds(model['periodic']['vertices'],stamp,stamp+period)+.10;polygon=clipped(normals,bounds)
    actual=[body[0]-.3*math.cos(body[2]),body[1]-.3*math.sin(body[2]),body[2]];poses=np.vstack([actual,segment['poses']]);dense=[];maximum_gap=0.
    for a,b in zip(poses[:-1],poses[1:]):
        turn=math.atan2(math.sin(b[2]-a[2]),math.cos(b[2]-a[2]));distance=float(np.linalg.norm(b[:2]-a[:2]));count=max(1,int(math.ceil(distance/.001)),int(math.ceil(abs(turn)/.001)))
        maximum_gap=max(maximum_gap,(distance+math.hypot(.74,.375)*abs(turn))/(2*count))
        dense.extend([[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*turn] for t in np.linspace(0,1,count,endpoint=False)])
    dense.append(poses[-1].tolist());rear=np.asarray(dense);center=rear.copy();center[:,:2]+=.3*np.c_[np.cos(rear[:,2]),np.sin(rear[:,2])]
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    dynamic=distances(center,polygon);static=geometry.pose_values(field,rear);minimum=np.minimum(dynamic,static);index=int(np.argmin(minimum));error=0.
    for i in sorted({0,index,len(rear)//2,len(rear)-1}):error=max(error,abs(float(dynamic[i])-scalar_distance(center[i],polygon)))
    assert error<=1e-8
    lower=float(minimum.min())-maximum_gap;result=dict(geometry_passed=lower>=.22-1e-8,full_dynamics_or_actual_response_qualified=False,
        source_native_tick=32210,coefficient_source_tick=32200,all_future_under_same_declared_periodic_class=True,actor_radius_already_in_support_m=.10,
        original_segment_unchanged=segment,actual_start_gap_included=True,sample_count=len(rear),minimum_sample_distance_m=float(minimum.min()),
        continuous_interpolation_allowance_m=maximum_gap,continuous_geometry_lower_m=lower,limiting_index=index,limiting_body=center[index].tolist(),
        independent_scalar_max_error=error,source_polygon=polygon.tolist(),source_support=bounds.tolist(),dense_rear_path=rear.tolist(),
        original_disk_handoff_lower_m=.1431194065616253,models=0,physical_native=0,private_native=0,replay_native=0,wall_s=time.monotonic()-begin)
    p=O/'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json';assert not p.exists();p.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    assert all(sha(R/p)==h for p,h in manifest['files'].items())
    print(json.dumps({k:v for k,v in result.items() if k not in ['original_segment_unchanged','source_polygon','source_support','dense_rear_path']}))
if __name__=='__main__':main()
