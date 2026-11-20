"""Original declared coupled-mode body envelope versus fixed32210 causal set.

Geometry only: old finite static tests do not prove this state's response.
"""
import math
import os
from pathlib import Path
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from snapshot_diagnostic import R,C,O,RAW,read,sha,function,load,scalar_distance,np,SimpleNamespace,json

def main():
    os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ZERO_MODEL600_STOP')));signal.alarm(600)
    frozen=read(O/'ENVELOPE_SOURCE_FREEZE.json');assert all(sha(R/p)==h for p,h in frozen['files'].items())
    source=read(C/'COUPLED_ENVELOPE_INPUT.json');assert source['translation_radius_m']==.02 and source['yaw_radius_rad']==.1
    body=read(RAW/'APPLIED_JOURNAL.json')[32210]['body'];known=read(RAW/'physics/SETUP.json')['known']
    polygon=np.asarray(read(O/'ORIGINAL_SEGMENT_ALL_FUTURE_POLYGON.json')['source_polygon'])
    distances=function('experiments/v934_rpccr_certified_recovery/polygon_geometry.py','distances')
    geometry=load('same_static_footprint_for_envelope','experiments/v855_renewal_worker/exact_footprint.py')
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.array([.3,0.]),rectangles=np.asarray(known['known_rectangles']),circles=np.asarray(known['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
    yaws=body[2]+np.linspace(-.1,.1,201);centers=np.c_[np.full(len(yaws),body[0]),np.full(len(yaws),body[1]),yaws]
    rear=centers.copy();rear[:,:2]-=.3*np.c_[np.cos(yaws),np.sin(yaws)]
    dynamic=distances(centers,polygon);static=geometry.pose_values(field,rear)
    reserve=.02+math.hypot(.44,.375)*.001/2;minimum=np.minimum(dynamic,static);at=int(np.argmin(minimum))
    error=abs(float(dynamic[at])-scalar_distance(centers[at],polygon));assert error<=1e-8
    result=dict(original_declared_body_envelope=source,source_native_tick=32210,coefficient_source_tick=32200,
        all_future_geometry_passed=float(minimum.min())-reserve>=.22-1e-8,
        sampled_minimum_m=float(minimum.min()),translation_and_continuous_rotation_allowance_m=reserve,
        complete_envelope_lower_m=float(minimum.min())-reserve,required_m=.22,limiting_yaw_offset_rad=float(yaws[at]-body[2]),
        independent_scalar_error_m=error,full_yaw_samples=len(yaws),source_actual_response_not_yet_qualified=True,
        old_static_samples_not_treated_as_generalization=True,physical_entry_ready=False,models=0,physical_native=0,replay_native=0,wall_s=time.monotonic()-begin)
    p=O/'ORIGINAL_COUPLED_ENVELOPE_GEOMETRY.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n')
    assert all(sha(R/p)==h for p,h in frozen['files'].items());print(json.dumps(result));signal.alarm(0)
if __name__=='__main__':main()
