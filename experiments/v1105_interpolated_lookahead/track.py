"""Original signed controller/predictor following a proposed geometric path."""
import numpy as np,math
from prediction import Predictor,initial
from kernel import PARAMETERS,REQUIRED,checks,ref,predict
from recovery_source import forecast_packet
def path_distance(point,path):
    q=np.asarray(path,dtype=float)[:,:2];p=np.asarray(point,dtype=float)[:2]
    assert len(q)>0 and np.isfinite(q).all() and np.isfinite(p).all(),'INVALID_METRIC_INPUT'
    if len(q)==1:return float(np.linalg.norm(q[0]-p))
    edge=q[1:]-q[:-1];delta=p-q[:-1];length2=np.sum(edge*edge,axis=1)
    fraction=np.divide(np.sum(delta*edge,axis=1),length2,out=np.zeros_like(length2),where=length2>0.)
    fraction=np.clip(fraction,0.,1.)
    return float(np.linalg.norm(delta-fraction[:,None]*edge,axis=1).min())

def lookahead_target(body,path,progress,radius=.25):
    q=np.asarray(path,dtype=float)[:,:2];center=np.asarray(body,dtype=float)[:2]
    assert 0<=progress<len(q) and radius>0 and np.isfinite(q).all() and np.isfinite(center).all(),'INVALID_LOOKAHEAD_INPUT'
    # The caller supplies only the CURRENT gear section, so interpolation can
    # neither look through a reversing cusp nor extend beyond its endpoint.
    relative=q[progress:]-center;hits=np.flatnonzero(np.linalg.norm(relative,axis=1)>=radius)
    if not len(hits):return q[-1].copy()
    j=int(hits[0])+progress
    if j==progress:return q[j].copy()
    a=q[j-1]-center;edge=q[j]-q[j-1];aa=float(edge@edge)
    assert aa>0.,'DEGENERATE_CIRCLE_CROSSING'
    bb=2*float(a@edge);cc=float(a@a)-radius*radius;disc=bb*bb-4*aa*cc
    assert disc>=-1e-12,'NO_CIRCLE_SEGMENT_INTERSECTION'
    fraction=(-bb+math.sqrt(max(0.,disc)))/(2*aa)
    assert -1e-10<=fraction<=1+1e-10,'CIRCLE_TARGET_OUTSIDE_SEGMENT'
    return q[j-1]+float(np.clip(fraction,0.,1.))*edge

def rollout(x,path,gear):
    p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);states=[p.state.copy()];controls=[];requests=[];mem=[np.r_[p.adapter.last,p.adapter.integral]];events=[];cross=0.;ticks=0
    def advance(v,w):
        nonlocal ticks
        assert ticks<40000,'NOMINAL_TRACKING_NATIVE_CAP';s,u=p.step(v,w,False);states.append(s);controls.append(u);requests.append([v,w,0.]);mem.append(np.r_[p.adapter.last,p.adapter.integral]);ticks+=1
    runs=[];i=0
    while i<len(gear):
        j=i+1
        while j<len(gear)and gear[j]==gear[i]:j+=1
        runs.append((i,j,gear[i]));i=j
    failure=None
    try:
        for begin,end,direction in runs:
            q=path[begin:end+1];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q[:,:2],axis=0),axis=1))];progress=0;start=ticks
            if arc[-1]<1e-7:continue
            assert abs(p.state[3])<=.003 and abs(p.adapter.last[2:]).max()<=1e-10,'GEAR_CHANGE_NOT_STOPPED'
            while np.linalg.norm(p.state[:2]-q[-1,:2])>.02:
                stop=min(len(q),progress+81);progress=max(progress,progress+int(np.argmin(np.linalg.norm(q[progress:stop,:2]-p.state[:2],axis=1))))
                target=lookahead_target(p.state,q,progress,.25);d=target-p.state[:2];c=math.cos(p.state[2]);s=math.sin(p.state[2]);along=c*d[0]+s*d[1];lateral=-s*d[0]+c*d[1];d2=float(d@d)
                assert d2>1e-8 and direction*along>-.02,'PATH_TARGET_WRONG_GEAR_SIDE'
                k=float(np.clip(2*lateral/d2,-math.tan(.42722137342572125)/.6,math.tan(.42722137342572125)/.6));v=.08 if direction>0 else-.03;advance(v,v*k)
                cross=max(cross,path_distance(p.state,q));assert cross<=.04,'ORIGINAL_PREDICTED_PATH_CROSS_TRACK'
                assert ticks-start<12000,'SEGMENT_TRACKING_CAP'
            for _ in range(2200):advance(0.,0.)
            events.append(dict(begin_native=start,end_native=ticks,gear=direction,complete2200stop=True,translation_speed=float(np.linalg.norm(p.state[3:5]))))
    except AssertionError as exc:
        failure=str(exc)
    states=np.array(states);controls=np.array(controls);requests=np.array(requests);memory=np.array(mem)
    if failure is not None:
        return dict(passed=False,error=failure,analytical_native=len(requests),maximum_predicted_cross_track_m=cross,events=events,partial_witness_saved=True),states,controls,requests
    a,b=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(states[:,:3]);low=float(np.minimum(a,b).min());cc,upper=checks(states,controls,requests,x['packet'],x['setup'],np.array(x['goal']),low,REQUIRED)
    cc.update(complete2200stop=bool(len(requests)>=2200 and np.array_equal(requests[-2200:],np.zeros((2200,3)))),terminal_full_cycle_hold=bool(min(a[-1],b[-1])>=REQUIRED),path_cross_track=cross<=.04)
    review=dict(passed=bool(all(cc.values())),checks={k:bool(v)for k,v in cc.items()},minimum_full_cycle_raw_m=low,goal_upper_m=upper,maximum_predicted_cross_track_m=cross,analytical_native=len(requests),events=events)
    if review['passed']:
        stops=[]
        for i in range(0,len(requests)-2200,125):
            packet=forecast_packet(x['packet'],states[i],memory[i],i);packet['speed_episode']=False
            ss,uu,rr,_=predict(x['setup'],packet,[dict(kind='wait',gear=0,target=0.,ticks=2200)],tail=False);st,dy=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);lower=float(np.minimum(st,dy).min())
            stop_checks,_=checks(ss,uu,rr,packet,x['setup'],ss[-1,:2],lower,REQUIRED)
            stop_checks.pop('goal_upper');full_stop=bool(all(stop_checks.values()) and np.array_equal(rr,np.zeros((2200,3))))
            stops.append(dict(offset_native=i,passed=lower>=REQUIRED and full_stop,full_stop_controls_passed=full_stop,stop_raw_m=lower))
            if not stops[-1]['passed']:break
        review['rolling_stops']=stops;review['passed']=bool(stops and all(q['passed']for q in stops))
    return review,states,controls,requests
