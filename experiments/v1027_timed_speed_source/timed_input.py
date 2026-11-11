"""Full goal input search in pose/actuator-memory/native-time with real braking.

Only an analytical candidate. Native start-tick and tracking enforcement are
mandatory before actuation. Waiting evolves the original predictor and brakes;
no state/velocity/clock is reset or assumed to jump to rest.
"""
import heapq,math,time,sys
from pathlib import Path
import numpy as np
from geometry_model import ref,REQUIRED,RHO
from whole_input import initial,Predictor,PARAMETERS,checks,public_setup
from fast_predict import Expander
from time_geometry import interval_support
NORMALS=np.c_[np.cos(np.arange(16)*math.pi/8),np.sin(np.arange(16)*math.pi/8)]
CAP=.42722137342572125;TARGETS=np.linspace(-CAP,CAP,5);DT=.01;MOVE=125;HOLD=200;START_DELAY=0;MAX_TICKS=40000;MAX_EXPANSIONS=30000;STRIDE=5

def predict(setup,packet,actions):
    engine=Predictor(setup,initial(packet),PARAMETERS);states=[engine.state.copy()];ctrl=[];requests=[]
    for action in [*actions,dict(kind='wait',ticks=200,target=0.)]:
        v=.08 if action['kind']=='move'else 0.;w=v*math.tan(action['target'])/.6
        for _ in range(action['ticks']):
            state,u=engine.step(v,w,False);states.append(state);ctrl.append(u);requests.append([v,w,False])
    return np.asarray(states),np.asarray(ctrl),np.asarray(requests,float)

class Geometry:
    def __init__(self,known,prior,start):
        self.static=ref._old.Geometry(known,None);self.prior=prior;self.start=start;self.cache={}
    def clearances(self,poses,ticks,half_s):
        ticks=np.asarray(ticks,float);key=(tuple(ticks),half_s)
        if key not in self.cache:
            t=self.start+ticks*.01;self.cache[key]=interval_support(self.prior['vertices'],t-half_s-.05,t+half_s+.05)
        b=self.cache[key];p=np.asarray(poses);c=np.cos(p[:,2]);s=np.sin(p[:,2]);front=np.c_[c,s];left=np.c_[-s,c]
        lower=p[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T)
        dynamic=(lower-b-.1).max(axis=1);static=self.static.clearances(p)[0]
        return np.minimum(static,dynamic)
    def complete(self,states):
        lowest=math.inf
        for start in range(0,len(states),2048):
            q=states[start:start+2048];lower=self.clearances(q[:,:3],np.arange(start,start+len(q)),.005);lowest=min(lowest,float(lower.min()))
        return lowest

def construct(packet,source,goal,setup,deadline):
    setup=public_setup(setup);ref.snapshot_state(packet,source,packet['body_measured_at']);goal=np.asarray(goal,float)
    origin=initial(packet);state=np.asarray(origin['state']);memory=np.r_[origin['last_ctrl'],origin['integral']];full=ref._old.Geometry(setup['known'],source['periodic']);a,b=full.clearances(state[None,:3]);initial_lower=float(min(a[0],b[0]));base=dict(passed=False,models=0,integrations=0,scope='FULL_NATIVE_TIME_008_INPUT_SOURCE_ONLY',physical_ready=False,actuation_authority=False,original_goal=goal.tolist(),required_raw_clearance_m=REQUIRED,planned_motion_start_native_tick=packet['native_tick']+START_DELAY,start_window_ticks=5,initial_full_cycle_hold_lower_m=initial_lower)
    if initial_lower<REQUIRED:return dict(base,status='INITIAL_FULL_CYCLE_HOLD_REJECTED')
    geometry=Geometry(setup['known'],source['periodic'],packet['sim_time']+START_DELAY*.01);heuristic,_=ref._old.Geometry(setup['known'],None).heuristic(goal);engine=Expander(setup)
    def key(s,m,t):return(round(s[0]/.05),round(s[1]/.05),round((s[2]%(2*math.pi))*144/(2*math.pi))%144,round(s[6]/(CAP/2)),round(s[7]/.03),round(s[3]/.01),round(m[4]/.02),round((t*.01%(2*math.pi/.32))/.5))
    nodes=[(state,memory,-1,None,0,initial_lower)];best={key(state,memory,0):0.};heap=[(1.5*heuristic(state),0.,0)];expanded=rejected=0;best_goal=float(np.linalg.norm(state[:2]-goal));begun=time.monotonic();tested=[]
    def chain(index):
        out=[]
        while nodes[index][2]!=-1:out.append(nodes[index][3]);index=nodes[index][2]
        return list(reversed(out))
    while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,memory,parent,action,elapsed,lower=nodes[index]
        if cost>best.get(key(state,memory,elapsed),math.inf)+1e-10:continue
        expanded+=1;error=float(np.linalg.norm(state[:2]-goal));best_goal=min(best_goal,error)
        if elapsed and error+.08<=.45:
            actions=chain(index);ss,uu,rr=predict(setup,packet,actions);minimum=geometry.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,goal,minimum,REQUIRED);a,b=full.clearances(ss[-1:,:3]);cc['terminal_full_cycle_hold']=float(min(a[0],b[0]))>=REQUIRED
            tested.append(dict(checks=cc,goal_upper_m=upper,minimum_raw_m=minimum))
            if all(cc.values()):return dict(base,passed=True,status='FULL_TIMED_INPUT_ROUTE_SOURCE_QUALIFIED',expanded=expanded,wall_s=time.monotonic()-begun,actions=actions,state_path=ss.tolist(),planned_body_requests=rr.tolist(),predicted_actuator_controls=uu.tolist(),path=ss[:,:3].tolist(),checks=cc,terminal_goal_upper_m=upper,minimum_full_timed_raw_m=minimum,analytical_prediction_steps=len(rr),wait_actions=sum(x['kind']=='wait'for x in actions),maximum_expansions=MAX_EXPANSIONS)
        if elapsed+HOLD>MAX_TICKS:continue
        choices=[]
        for kind,targets,steps,speeds in [('move',TARGETS,MOVE,np.full(5,.08)),('wait',np.array([0.]),HOLD,np.array([0.]))]:
            if elapsed+steps>MAX_TICKS:continue
            ss,uu,mm=engine.expand(state,memory,targets,steps,speeds)
            ix=np.unique(np.r_[0,np.arange(STRIDE,steps,STRIDE),steps]);poses=np.concatenate([np.repeat(state[None,None,:3],len(targets),axis=0),ss[:,:,:3]],axis=1)[:,ix]
            lower_array=np.asarray([geometry.clearances(p,elapsed+ix,STRIDE*.01/2)for p in poses]);dense=np.concatenate([np.repeat(state[None,None,:3],len(targets),axis=0),ss[:,:,:3]],axis=1)
            j=np.arange(steps+1);left=ix[np.maximum(0,np.searchsorted(ix,j,side='right')-1)];right=ix[np.minimum(len(ix)-1,np.searchsorted(ix,j,side='left'))];dl=np.linalg.norm(dense[:,:,:2]-dense[:,left,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,left,2]);dr=np.linalg.norm(dense[:,:,:2]-dense[:,right,:2],axis=2)+RHO*abs(dense[:,:,2]-dense[:,right,2]);gap=np.minimum(dl,dr).max(axis=1)
            valid=(lower_array.min(axis=1)-gap>=REQUIRED)&(abs(ss[:,:,3]).max(axis=1)<=.13)&(abs(ss[:,:,5]).max(axis=1)<=.16)&(abs(ss[:,:,4]).max(axis=1)<=.03)
            for i,target in enumerate(targets):
                if not valid[i]:rejected+=1;continue
                child=ss[i,-1];cm=mm[i];t=elapsed+steps;nc=cost+steps*.01*.08*(1+.15*abs(target)/CAP);marker=key(child,cm,t)
                if nc>=best.get(marker,math.inf)-1e-10:continue
                best[marker]=nc;nodes.append((child.copy(),cm.copy(),index,dict(kind=kind,target=float(target),ticks=steps),t,min(lower,float(lower_array[i].min())-gap[i])));heapq.heappush(heap,(nc+1.5*heuristic(child),nc,len(nodes)-1))
    return dict(base,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_COMPLETE_TIMED_INPUT_ROUTE',expanded=expanded,generated=len(nodes),rejected_edges=rejected,best_goal_distance_m=best_goal,wall_s=time.monotonic()-begun,input_candidate_checks=tested)
