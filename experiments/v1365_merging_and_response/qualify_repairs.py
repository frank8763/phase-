"""Exact-pose pruning and steering-slew regressions; no new vehicle models."""
import copy
import os
import time
from common import *
from slew_primitive import generate,physical_ready,MAX_CENTER,STEERING_RATE


def independent_path_review(path):
    p=np.asarray(path);assert p.ndim==2 and p.shape[1]==6 and np.isfinite(p).all()
    assert abs(p[0,3])<1e-8 and np.max(abs(np.diff(p[:,3])-.01))<1e-8,'CLOCK'
    assert abs(p[:,4]).max()<=.100000001 and abs(p[:,5]).max()<=MAX_CENTER+1e-8
    assert np.max(abs(np.diff(p[:,5])))<=STEERING_RATE*.01+1e-10,'STEERING_SLEW'
    assert np.max(abs(np.diff(p[:,4])))<=.001+1e-10,'NOMINAL_ACCELERATION'
    error=0.
    for a,b in zip(p[:-1],p[1:]):
        distance=.005*(a[4]+b[4]);curvature=math.tan((a[5]+b[5])/2)/.6
        yaw=a[2]+distance*curvature
        if abs(curvature)>1e-10:x=a[0]+(math.sin(yaw)-math.sin(a[2]))/curvature;y=a[1]-(math.cos(yaw)-math.cos(a[2]))/curvature
        else:x=a[0]+distance*math.cos(a[2]);y=a[1]+distance*math.sin(a[2])
        error=max(error,abs(x-b[0]),abs(y-b[1]),abs(yaw-b[2]))
    assert error<=1e-8,'NOMINAL_INTEGRATION'
    return dict(passed=True,maximum_reconstruction_error_m_or_rad=error,samples=len(p),actual_physics_qualified=False)


def main():
    os.sched_setaffinity(0,{3});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));begin=time.monotonic()
    target=O/'REPAIR_QUALIFICATION.json';assert not target.exists()
    row=call(O/'libexact_pose.so','plan_exact_pose');print('EXACT_POSE_SEARCH',json.dumps({k:v for k,v in row.items() if k!='path'}),flush=True)
    cases=[]
    specifications=[('forward_straight',0.,0.,.1,0.,2.),
                    ('cruise_opposite_steering',.1,-MAX_CENTER,.1,MAX_CENTER,1.2),
                    ('curved_brake',.1,MAX_CENTER,0.,MAX_CENTER,2.4)]
    for name,v,s,wanted,delta,seconds in specifications:
        path=generate([0.,0.,0.],v,s,wanted,delta,seconds)
        proof=independent_path_review(path);case=dict(name=name,review=proof,path=path.tolist())
        if name=='cruise_opposite_steering':
            reached=np.flatnonzero(abs(path[:,5]-MAX_CENTER)<1e-10)
            case['first_opposite_extreme_s']=None if not len(reached) else float(path[reached[0],3])
            assert len(reached) and case['first_opposite_extreme_s']>=2*MAX_CENTER/.6-1e-8
        cases.append(case)
    negatives=[]
    probes=[('parked_steering_assumed',lambda:generate([0.,0.,0.],0.,0.,0.,MAX_CENTER,1.)),
            ('moving_sign_reversal',lambda:generate([0.,0.,0.],.1,0.,-.1,0.,1.)),
            ('reverse_without200hold',lambda:generate([0.,0.,0.],0.,0.,-.1,0.,1.,prior_gear=1,rest_native=0)),
            ('bad_clock',lambda:generate([0.,0.,0.],0.,0.,.1,0.,.015))]
    for name,probe in probes:
        try:probe()
        except AssertionError:negatives.append(name)
        else:raise AssertionError('ILLEGAL_PRIMITIVE_ACCEPTED '+name)
    for name,column,value in [('instantaneous_steering',5,MAX_CENTER),('clock_tamper',3,-.1),('velocity_jump',4,.1)]:
        path=np.array(cases[0]['path']);path[1,column]=value
        try:independent_path_review(path)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('BAD_PATH_ACCEPTED '+name)
    assert not physical_ready(response_envelope=None,full_route_reviewed=False)
    result=dict(passed=True,scope='exact-label and nominal-steering regressions only',exact_search=row,
        exact_search_source_sha256=sha(C/'exact_search.cpp'),exact_search_library_sha256=sha(O/'libexact_pose.so'),
        cases=cases,negative_cases=negatives,actual_control_response_qualified=False,
        original_terminal_full_route_qualified=row['code']==0,physical_launch_allowed=False,models=0,physical_native=0,wall_s=time.monotonic()-begin)
    dump(target,result);print(json.dumps({k:v for k,v in result.items() if k not in ['cases','exact_search']}))


if __name__=='__main__':main()
