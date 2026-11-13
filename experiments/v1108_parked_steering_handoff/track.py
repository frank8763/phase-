"""Bounded body-position preview follower of the unchanged official Smac path."""
import sys,math
from pathlib import Path
import numpy as np
from prediction import Predictor,initial
from kernel import PARAMETERS,REQUIRED,checks,ref,predict
from recovery_source import forecast_packet
from preview import Preview
from parked_control import Adapter as ParkAdapter
def path_distance(point,path):
    q=np.asarray(path,dtype=float)[:,:2];p=np.asarray(point,dtype=float)[:2]
    assert len(q)>0 and np.isfinite(q).all() and np.isfinite(p).all(),'INVALID_METRIC_INPUT'
    if len(q)==1:return float(np.linalg.norm(q[0]-p))
    edge=q[1:]-q[:-1];delta=p-q[:-1];length2=np.sum(edge*edge,axis=1)
    fraction=np.divide(np.sum(delta*edge,axis=1),length2,out=np.zeros_like(length2),where=length2>0.)
    fraction=np.clip(fraction,0.,1.)
    return float(np.linalg.norm(delta-fraction[:,None]*edge,axis=1).min())

COUNTS=dict(cpp_preview_native=0,cpp_preview_calls=0,cpp_work_exact=True,python_tracking_native=0,python_rolling_stop_native=0)
MODES=[];ALIGN_TARGETS=[]
CAP=.42722137342572125
def project_arc(point,q,arc,previous):
    edge=np.diff(q[:,:2],axis=0);length=np.diff(arc);lo=max(0.,previous-.02);hi=min(float(arc[-1]),previous+.25)
    valid=(arc[:-1]<=hi)&(arc[1:]>=lo)&(length>0.);idx=np.flatnonzero(valid);assert len(idx),'EMPTY_PROGRESS_WINDOW'
    a=q[idx,:2];d=edge[idx];length=length[idx];fraction=((point[:2]-a)*d).sum(axis=1)/(length*length)
    lower=np.maximum(0.,(lo-arc[idx])/length);upper=np.minimum(1.,(hi-arc[idx])/length);fraction=np.clip(fraction,lower,upper)
    error=np.linalg.norm(point[:2]-(a+fraction[:,None]*d),axis=1);k=int(error.argmin())
    return max(previous,float(arc[idx[k]]+fraction[k]*length[k]))
def prefix_cross(states,q):
    points=states[:,:,:2];a=q[:-1,:2];d=np.diff(q[:,:2],axis=0);l2=(d*d).sum(axis=1)
    delta=points[:,:,None,:]-a[None,None,:,:]
    frac=np.divide((delta*d).sum(axis=3),l2,out=np.zeros(delta.shape[:-1]),where=l2>0.)
    delta-=np.clip(frac,0.,1.)[:,:,:,None]*d
    return np.sqrt((delta*delta).sum(axis=3).min(axis=2)).max(axis=1)
def select(preview,state,memory,q,arc,progress,direction):
    speed=.08 if direction>0 else-.03
    steps=min(500,max(25,int(math.ceil((arc[-1]-progress)/(abs(speed)*.01)))))
    targets=np.unique(np.r_[np.linspace(-CAP,CAP,21),np.clip(state[6],-CAP,CAP)])
    try:ss,uu,_=preview.expand(state,memory,targets,speed,steps)
    except BaseException:
        COUNTS['cpp_work_exact']=False
        raise
    COUNTS['cpp_preview_native']=preview.native;COUNTS['cpp_preview_calls']=preview.calls
    desired=np.minimum(arc[-1],progress+abs(speed)*.01*np.arange(1,steps+1))
    reference=np.c_[np.interp(desired,arc,q[:,0]),np.interp(desired,arc,q[:,1])]
    error=((ss[:,:,:2]-reference[None,:,:])**2).sum(axis=2)
    cost=error.mean(axis=1)+4*error[:,-1]+1e-5*(targets-state[6])**2
    valid=prefix_cross(ss[:,:25],q)<=.04
    assert valid.any(),'NO_PREVIEW_TRACKING_BRANCH'
    cost[~valid]=np.inf;selected=int(cost.argmin())
    return float(targets[selected]),speed,ss[selected,:25],uu[selected,:25],float(cost[selected])

def complete_stop(setup,packet,state,memory):
    # A predicted rolling state can have nonzero lateral velocity. The public
    # packet schema lacks this component; do not silently reset it to zero.
    origin=initial(packet);origin['state']=np.array(state,copy=True);origin['last_ctrl']=np.array(memory[:4],copy=True);origin['integral']=float(memory[4])
    p=Predictor(setup,origin,PARAMETERS);ss=[p.state.copy()];uu=[]
    assert np.array_equal(ss[0],state),'ROLLING_STOP_ORIGIN_CHANGED'
    for _ in range(2200):
        s,u=p.step(0.,0.,False);ss.append(s);uu.append(u);COUNTS['python_rolling_stop_native']+=1
    return np.asarray(ss),np.asarray(uu),np.zeros((2200,3))

def rollout(x,path,gear):
    preview=Preview(x['setup']);p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);p.adapter.__class__=ParkAdapter
    states=[p.state.copy()];controls=[];requests=[];memory=[np.r_[p.adapter.last,p.adapter.integral]];events=[];decisions=[];ticks=0;cross=0.;maximum_cpp_error=0.;active_q=None
    def advance(v,w):
        nonlocal ticks,cross
        assert ticks<40000,'NOMINAL_TRACKING_NATIVE_CAP'
        mode=getattr(p.adapter,'parked_target',None)
        s,u=p.step(v,w,False);states.append(s);controls.append(u);requests.append([v,w,0.]);MODES.append(int(mode is not None));ALIGN_TARGETS.append(float(mode)if mode is not None else 0.);memory.append(np.r_[p.adapter.last,p.adapter.integral]);ticks+=1;COUNTS['python_tracking_native']=ticks
        cross=max(cross,path_distance(s,active_q));assert cross<=.04,'ORIGINAL_PREDICTED_PATH_CROSS_TRACK'
        return s,u
    runs=[];i=0
    while i<len(gear):
        j=i+1
        while j<len(gear)and gear[j]==gear[i]:j+=1
        runs.append((i,j,gear[i]));i=j
    failure=None
    try:
        for section,(begin,end,direction) in enumerate(runs):
            active_q=q=path[begin:end+1];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1))];progress=0.;start=ticks
            if arc[-1]<1e-7:continue
            assert abs(p.state[3])<=.003 and abs(p.adapter.last[2:]).max()<=1e-10,'GEAR_CHANGE_NOT_STOPPED'
            if section:
                alignment_start=ticks;aligned=False
                for attempt in range(3):
                    progress=project_arc(p.state,q,arc,progress)
                    target,_,_,_,_=select(preview,p.state,np.r_[p.adapter.last,p.adapter.integral],q,arc,progress,direction)
                    assert np.max(abs(p.state[3:6]))<=.003,'PARKED_MODE_ENTRY_NOT_SETTLED'
                    p.adapter.parked_target=target;stable=0
                    for _ in range(600):
                        advance(0.,0.)
                        ready=abs(p.state[6]-target)<=.005 and abs(p.state[7])<=.015 and np.max(abs(p.state[3:6]))<=.003 and abs(p.adapter.last[2:]).max()<=1e-10
                        stable=stable+1 if ready else 0
                        if stable>=10:break
                    assert stable>=10,'PARKED_STEERING_NOT_SETTLED'
                    p.adapter.parked_target=None
                    progress=project_arc(p.state,q,arc,progress)
                    following,_,_,_,_=select(preview,p.state,np.r_[p.adapter.last,p.adapter.integral],q,arc,progress,direction)
                    if abs(following-p.state[6])<=.015:aligned=True;break
                assert aligned,'NO_STABLE_PARKED_STEERING_HANDOFF'
                events.append(dict(kind='parked_steering',begin_native=alignment_start,end_native=ticks,gear=direction,independent_mode_logged=True,rear_targets_zero=True,target=target))
            while np.linalg.norm(p.state[:2]-q[-1,:2])>.02:
                progress=project_arc(p.state,q,arc,progress)
                target,v,expected_s,expected_u,cost=select(preview,p.state,np.r_[p.adapter.last,p.adapter.integral],q,arc,progress,direction)
                decisions.append(dict(native=ticks,gear=direction,progress_arc_m=progress,target=target,cost=cost))
                for k in range(25):
                    s,u=advance(v,v*math.tan(target)/.6);error=max(float(abs(s-expected_s[k]).max()),float(abs(u-expected_u[k]).max()));maximum_cpp_error=max(maximum_cpp_error,error)
                    assert error<=1e-8,'PREVIEW_ORIGINAL_CONTROLLER_MISMATCH'
                    if np.linalg.norm(p.state[:2]-q[-1,:2])<=.02:break
                assert ticks-start<12000,'SEGMENT_TRACKING_CAP'
            moving_end=ticks
            for _ in range(2200):advance(0.,0.)
            events.append(dict(begin_native=start,moving_end_native=moving_end,end_native=ticks,gear=direction,complete2200stop=True,translation_speed=float(np.linalg.norm(p.state[3:5]))))
    except AssertionError as exc:failure=str(exc)
    ss=np.array(states);uu=np.array(controls);rr=np.array(requests);mm=np.array(memory)
    review=dict(passed=False,analytical_native=len(rr),maximum_predicted_cross_track_m=cross,maximum_selected_cpp_python_error=maximum_cpp_error,events=events,decisions=decisions,preview_native=preview.native,preview_calls=preview.calls)
    if failure is not None:
        review.update(error=failure,partial_witness_saved=True);return review,ss,uu,rr
    a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);low=float(np.minimum(a,b).min());cc,upper=checks(ss,uu,rr,x['packet'],x['setup'],np.array(x['goal']),low,REQUIRED)
    cc.update(complete2200stop=bool(len(rr)>=2200 and np.array_equal(rr[-2200:],np.zeros((2200,3)))),terminal_full_cycle_hold=bool(min(a[-1],b[-1])>=REQUIRED),path_cross_track=cross<=.04)
    review.update(passed=bool(all(cc.values())),checks={k:bool(v)for k,v in cc.items()},minimum_full_cycle_raw_m=low,goal_upper_m=upper)
    if review['passed']:
        stops=[]
        for i in range(0,len(rr)-2200,125):
            packet=forecast_packet(x['packet'],ss[i],mm[i],i);packet['speed_episode']=False
            stop_s,stop_u,stop_r=complete_stop(x['setup'],packet,ss[i],mm[i])
            st,dy=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(stop_s[:,:3]);lower=float(np.minimum(st,dy).min());sc,_=checks(stop_s,stop_u,stop_r,packet,x['setup'],stop_s[-1,:2],lower,REQUIRED);sc.pop('goal_upper')
            passed=bool(all(sc.values())and np.array_equal(stop_r,np.zeros((2200,3))));stops.append(dict(offset_native=i,passed=passed,full_stop_controls_passed=passed,stop_raw_m=lower))
            if not passed:break
        review['rolling_stops']=stops;review['passed']=bool(stops and all(q['passed']for q in stops))
    return review,ss,uu,rr

def replay(x,states,controls,requests):
    p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);p.adapter.__class__=ParkAdapter;maximum=0.
    assert len(MODES)==len(ALIGN_TARGETS)==len(requests),'MISSING_COMMAND_INTENTS'
    for i,(req,mode,target)in enumerate(zip(requests,MODES,ALIGN_TARGETS)):
        p.adapter.parked_target=target if mode else None
        s,u=p.step(*req);maximum=max(maximum,float(abs(s-states[i+1]).max()),float(abs(u-controls[i]).max()))
    return dict(passed=maximum<=1e-8,native=len(requests),maximum_state_ctrl_error=maximum,steering_only_native=sum(MODES),requires_explicit_mode_and_target_log=True,analytical_replay_not_physics=True)

