"""Causal breadcrumb refuge admission; geometry only, no vehicle/actor truth."""
import math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v881_timing_accounting_continuation')]
from support_envelope import polygon,NORMALS
from reproduce import pose,footprint,intersects
from snapshot_geometry import field,dense
from exact_footprint import pose_values
HOLD_S=4.
LATENCY_S=1.
DRIFT_M=.04
BODY=np.asarray([[-.63,-.565],[.63,-.565],[.63,.565],[-.63,.565]])

def wait_ok(body,support,age,hold=HOLD_S):
    if support is None:return True
    a=float(body[2]);forward=np.asarray([math.cos(a),math.sin(a)]);left=np.asarray([-math.sin(a),math.cos(a)])
    minimum=NORMALS@np.asarray(body[:2])-.63*np.abs(NORMALS@forward)-.565*np.abs(NORMALS@left)
    return bool(np.any(minimum>np.asarray(support)+.1+.08*(max(0.,age)+hold+LATENCY_S)+1e-8))

def exit_path_ok(path,support,age,known):
    samples=dense(path);minimum=float(np.min(pose_values(field(known),samples)))
    if minimum<.15+DRIFT_M+.009:return dict(passed=False,reason='EXIT_STATIC_BODY_SWEEP',minimum_static_m=minimum)
    elapsed=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(samples[:,:2],axis=0),axis=1))/.08]
    a=samples[:,2];forward=np.c_[np.cos(a),np.sin(a)];left=np.c_[-np.sin(a),np.cos(a)]
    projection=samples[:,:2]@NORMALS.T-.65*np.abs(forward@NORMALS.T)-.585*np.abs(left@NORMALS.T)
    if support is not None:
        future=np.asarray(support)[None,:]+.1+.08*(max(0.,age)+elapsed[:,None]+LATENCY_S)
        allowed=np.any(projection>future+1e-8,axis=1)
        if not np.all(allowed):return dict(passed=False,reason='EXIT_TIME_OCCUPANCY',at_elapsed_s=float(elapsed[np.flatnonzero(~allowed)[0]]))
    count=len(samples);elapsed=float(elapsed[-1])
    endpoint=samples[-1]
    if not wait_ok(endpoint,support,max(0.,age)+elapsed):return dict(passed=False,reason='EXIT_TERMINAL_HOLD_NOT_ADMITTED')
    endpoint_a=float(endpoint[2]);endpoint_f=np.asarray([math.cos(endpoint_a),math.sin(endpoint_a)]);endpoint_l=np.asarray([-math.sin(endpoint_a),math.cos(endpoint_a)])
    terminal_margin=None if support is None else float(np.max(NORMALS@endpoint[:2]-.63*np.abs(NORMALS@endpoint_f)-.565*np.abs(NORMALS@endpoint_l)-np.asarray(support)-.1-.08*(max(0.,age)+elapsed+HOLD_S+LATENCY_S)))
    return dict(passed=True,samples=count,terminal_separation_margin_m=terminal_margin,minimum_static_m=minimum,nominal_timing_speed_m_s=.08,elapsed_assumption_s=elapsed,terminal_hold_s=HOLD_S,engineering_drift_m=DRIFT_M,scope='Continuous geometric sampling bounds and finite assumed travel timing; actual controller delay/tracking independently checked, not formal dynamical backup')

def choose_refuge(body,history,support,age,known,memory=None):
    # History is chronological actual measured odometry, never a future actor pose.
    positions=[[*x['body'][:3]]for x in history]
    if not positions:return None
    eligible=[]
    for i in range(len(history)-1,-1,-1):
        distance=float(np.linalg.norm(np.asarray(body[:2])-positions[i][:2]))
        if not .75<=distance<=1.5:continue
        route=[list(body[:3]),*reversed(positions[i:])]
        # Remove repeated adjacent odometry poses before dense interpolation.
        clean=[route[0]]
        for x in route[1:]:
            if np.linalg.norm(np.asarray(x[:2])-clean[-1][:2])>.005:clean.append(x)
        if len(clean)<2:continue
        # A historical recovery reference must be a genuine reverse segment.
        # Reject mixed-gear history rather than changing its orientation or geometry.
        points=np.asarray(clean);delta=np.diff(points[:,:2],axis=0)
        signed=np.sum(delta*np.c_[np.cos(points[:-1,2]),np.sin(points[:-1,2])],axis=1)
        if np.any(signed>=-1e-5):continue
        proof=exit_path_ok(clean,support,age,known)
        if proof['passed']:eligible.append(dict(goal=positions[i],breadcrumb_native_tick=history[i]['native_tick'],distance_m=distance,geometry_contract=proof,reference_path=clean))
    # Completed reversals can create chronological loops. A previous admitted
    # actual-history corridor remains a candidate, only after current-pose and
    # fresh-observation revalidation through the SAME original exit contract.
    for prior in memory or []:
        saved=prior['selection']
        distance=float(np.linalg.norm(np.asarray(body[:2])-saved['goal'][:2]))
        if not .75<=distance<=1.5:continue
        try:clean,tracking=retained_suffix(body,saved['reference_path'])
        except AssertionError:continue
        points=np.asarray(clean);delta=np.diff(points[:,:2],axis=0)
        signed=np.sum(delta*np.c_[np.cos(points[:-1,2]),np.sin(points[:-1,2])],axis=1)
        if np.any(signed>=-1e-5):continue
        proof=exit_path_ok(clean,support,age,known)
        if proof['passed']:
            eligible.append(dict(goal=list(saved['goal']),breadcrumb_native_tick=saved['breadcrumb_native_tick'],distance_m=distance,geometry_contract=proof,reference_path=clean,provenance='REVALIDATED_PREVIOUS_ACTUAL_HISTORY',source_refuge_request_native_tick=prior['native_tick'],memory_tracking=tracking))
    # Choose the largest finite terminal separation reserve, rather than first fit.
    # The same retained route is returned to control and rechecked against fresh sensing.
    return max(eligible,key=lambda x:(x['geometry_contract']['terminal_separation_margin_m'] or 0.,-x['distance_m']))if eligible else None

def retained_suffix(body,reference):
    """Actual pose to nearest remaining real-history segment; never invent a detour."""
    points=np.asarray(reference,dtype=float)
    assert points.ndim==2 and points.shape[1]==3 and len(points)>=2 and np.isfinite(points).all(),'INVALID_RETAINED_REFERENCE'
    distance=np.linalg.norm(points[:,:2]-np.asarray(body[:2]),axis=1);idx=int(np.argmin(distance))
    assert float(distance[idx])<=.04,'RETAINED_REFERENCE_TRACKING_MARGIN'
    # Keep at least the original endpoint. Region completion occurs before it.
    idx=min(idx,len(points)-2)
    clean=[list(body[:3])]
    for row in points[idx+1:]:
        if np.linalg.norm(row[:2]-np.asarray(clean[-1][:2]))>.001:clean.append(row.tolist())
    assert len(clean)>=2,'RETAINED_REFERENCE_EXHAUSTED'
    return clean,dict(nearest_history_index=idx,measured_reference_distance_m=float(distance.min()),tracking_margin_m=.04)
