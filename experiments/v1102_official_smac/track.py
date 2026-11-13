"""Original signed controller/predictor following a proposed geometric path."""
import numpy as np,math
from prediction import Predictor,initial
from kernel import PARAMETERS,REQUIRED,checks,ref,predict
from recovery_source import forecast_packet
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
                carrot=min(int(np.searchsorted(arc,arc[progress]+.25)),len(q)-1);d=q[carrot,:2]-p.state[:2];c=math.cos(p.state[2]);s=math.sin(p.state[2]);along=c*d[0]+s*d[1];lateral=-s*d[0]+c*d[1];d2=float(d@d)
                assert d2>1e-8 and direction*along>-.02,'PATH_TARGET_WRONG_GEAR_SIDE'
                k=float(np.clip(2*lateral/d2,-math.tan(.42722137342572125)/.6,math.tan(.42722137342572125)/.6));v=.08 if direction>0 else-.03;advance(v,v*k)
                cross=max(cross,float(np.linalg.norm(q[:,:2]-p.state[:2],axis=1).min()));assert cross<=.04,'ORIGINAL_PREDICTED_PATH_CROSS_TRACK'
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
            ss,uu,rr,_=predict(x['setup'],packet,[dict(kind='wait',gear=0,target=0.,ticks=2200)],tail=False);st,dy=ref._old.Geometry(x['setup']['known'],x['source']['periodic']).clearances(ss[:,:3]);lower=float(np.minimum(st,dy).min());stops.append(dict(offset_native=i,passed=lower>=REQUIRED,stop_raw_m=lower))
            if lower<REQUIRED:break
        review['rolling_stops']=stops;review['passed']=bool(stops and all(q['passed']for q in stops))
    return review,states,controls,requests
