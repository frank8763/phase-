"""Complete SE2-steering-time routes using only a causal periodic coefficient set.

The certificate is tied to a future native start tick; it is not executable
unless a native receiver enforces that start window and unchanged initial state.
"""
import heapq,math,time
import numpy as np
from full_route import ref,REQUIRED,GOAL_RADIUS,MAX_EXPANSIONS
from command_tube import NORMALS
from exact_footprint import pose_values

EDGE_TICKS=334;WAIT_TICKS=200;DT=.01;START_DELAY_TICKS=1000;START_JITTER_S=.05;MAX_TICKS=22000

def interval_support(vertices,starts,ends):
    starts=np.asarray(starts,float);ends=np.asarray(ends,float);result=[]
    for v in vertices:
        p=np.asarray(v,float);a=p[:,1];b=p[:,2];phase=np.arctan2(a,b);radius=np.hypot(a,b)
        left=p[:,0]+np.sin(.32*starts[:,None])*a+np.cos(.32*starts[:,None])*b
        right=p[:,0]+np.sin(.32*ends[:,None])*a+np.cos(.32*ends[:,None])*b
        upper=np.maximum(left,right);lower=np.minimum(left,right)
        for offset,ismax in [(0.,True),(math.pi,False)]:
            k=np.ceil((.32*starts[:,None]-phase-offset)/(2*math.pi));at=(phase+offset+2*math.pi*k)/.32
            mask=at<=ends[:,None]+1e-12;extreme=p[:,0]+(radius if ismax else-radius)
            if ismax:upper=np.where(mask,np.maximum(upper,extreme),upper)
            else:lower=np.where(mask,np.minimum(lower,extreme),lower)
        result.append((upper.max(axis=1)+2e-7,-lower.min(axis=1)+2e-7))
    return np.column_stack([x[0]for x in result]+[x[1]for x in result])

class TimedGeometry:
    def __init__(self,known,prior,start_sim_time):
        self.static=ref._old.field(known);self.prior=prior;self.start=start_sim_time;self.cache={}
    def bounds(self,elapsed,duration,n):
        key=(elapsed,duration,n)
        if key not in self.cache:
            t=np.linspace(0,duration*DT,n);half=duration*DT/(n-1)/2 if n>1 else duration*DT/2
            starts=self.start+elapsed*DT+np.maximum(0,t-half)-START_JITTER_S
            ends=self.start+elapsed*DT+np.minimum(duration*DT,t+half)+START_JITTER_S
            self.cache[key]=interval_support(self.prior['vertices'],starts,ends)
        return self.cache[key]
    def clearances(self,poses,bounds):
        p=np.asarray(poses);c=np.cos(p[:,2]);s=np.sin(p[:,2]);front=np.c_[c,s];left=np.c_[-s,c]
        low=p[:,:2]@NORMALS.T-.44*abs(front@NORMALS.T)-.375*abs(left@NORMALS.T)
        dynamic=np.max(low-bounds-.1,axis=1)
        return pose_values(self.static,p),dynamic

def construct(packet,source,goal,known,deadline,accept_complete=None):
    initial=ref.snapshot_state(packet,source,packet['body_measured_at']);goal=np.asarray(goal,float);prior=source['periodic'];original=ref._old.Geometry(known,prior)
    a,b=original.clearances(initial[None,:3]);start_lower=float(min(a[0],b[0]));start_tick=packet['native_tick']+START_DELAY_TICKS
    base=dict(passed=False,models=0,integrations=0,full_goal_route_required=True,partial_progress_never_success=True,original_goal=goal.tolist(),original_goal_radius_m=.45,
        goal_reference_radius_m=GOAL_RADIUS,required_clearance_m=REQUIRED,initial_state=initial.tolist(),source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'],
        planned_motion_start_native_tick=start_tick,start_window_ticks=5,start_hold_full_cycle_lower_m=start_lower,certificate_requires_native_clock_enforcement=True,physical_ready=False)
    if start_lower<REQUIRED:return dict(base,status='INITIAL_WAIT_NOT_FULL_CYCLE_SAFE',expanded=0)
    geom=TimedGeometry(known,prior,packet['sim_time']+START_DELAY_TICKS*DT);heuristic,hproof=ref._old.Geometry(known,None).heuristic(goal)
    samples=np.linspace(0,.1,9);period=2*math.pi/.32
    def key(p,t):return(round(p[0]/.025),round(p[1]/.025),round((p[2]%(2*math.pi))*144/(2*math.pi))%144,round(p[3]/(ref.MAX_DELTA/2)),round(((t*DT)%period)/.5))
    nodes=[(initial,-1,None,0,start_lower)];best={key(initial,0):0.};heap=[(1.5*heuristic(initial),0.,0)];expanded=rejected=0;start=time.monotonic();best_goal=float(np.linalg.norm(initial[:2]-goal));endpoint=None
    def rebuild(index):
        chain=[]
        while index!=-1:chain.append(index);index=nodes[index][1]
        actions=[nodes[j][2]for j in reversed(chain[:-1])];states=[initial];times=[0];elapsed=0
        for action in actions:
            duration=WAIT_TICKS if action['kind']=='wait'else EDGE_TICKS
            edge=np.repeat(np.asarray(states[-1])[None,:],9,axis=0)if action['kind']=='wait'else ref.primitive(states[-1],action['target'],samples)
            states.extend(edge[1:]);times.extend(elapsed+np.arange(1,9)*duration/8);elapsed+=duration
        return actions,np.asarray(states),np.asarray(times)*DT
    while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,_,_,elapsed,minimum=nodes[index]
        if cost>best.get(key(state,elapsed),math.inf)+1e-10:continue
        expanded+=1;error=float(np.linalg.norm(state[:2]-goal));best_goal=min(best_goal,error)
        if elapsed>0 and error<=GOAL_RADIUS:
            aa,bb=original.clearances(state[None,:3])
            if min(aa[0],bb[0])>=REQUIRED:
                actions,states,times=rebuild(index)
                if accept_complete is None or accept_complete(actions,states,times):endpoint=index;break
        if elapsed>=MAX_TICKS:continue
        edges=np.asarray([ref.primitive(state,target,samples)for target in ref.TARGETS]);bounds=geom.bounds(elapsed,EDGE_TICKS,9)
        a,b=geom.clearances(edges[:,:,:3].reshape(-1,3),np.tile(bounds,(len(ref.TARGETS),1)));values=np.minimum(a,b).reshape(len(ref.TARGETS),9)
        candidates=[(dict(kind='move',target=float(target)),edges[j,-1],EDGE_TICKS,float(values[j].min()),.1*(1+.15*abs(target)/ref.MAX_DELTA)+.02*abs(target-state[3])/ref.MAX_DELTA)for j,target in enumerate(ref.TARGETS)]
        waitposes=np.repeat(state[None,:3],9,axis=0);aa,bb=geom.clearances(waitposes,geom.bounds(elapsed,WAIT_TICKS,9))
        candidates.append((dict(kind='wait'),state,WAIT_TICKS,float(np.minimum(aa,bb).min()),WAIT_TICKS*DT*.03))
        for action,child,duration,lower,delta in candidates:
            if lower<REQUIRED:rejected+=1;continue
            t=elapsed+duration
            if t>MAX_TICKS:continue
            next_cost=cost+delta;marker=key(child,t)
            if next_cost>=best.get(marker,math.inf)-1e-10:continue
            best[marker]=next_cost;nodes.append((child,index,action,t,min(minimum,lower)));heapq.heappush(heap,(next_cost+1.5*heuristic(child),next_cost,len(nodes)-1))
    report=dict(base,expanded=expanded,generated=len(nodes),rejected_edges=rejected,best_goal_distance_m=best_goal,wall_s=time.monotonic()-start,max_duration_s=MAX_TICKS*DT)
    if endpoint is None:return dict(report,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_COMPLETE_TIMED_ROUTE')
    actions,states,times=rebuild(endpoint)
    return dict(report,passed=True,status='COMPLETE_CAUSAL_TIMED_GEOMETRY',actions=actions,path=states[:,:3].tolist(),state_path=states.tolist(),times_s=times.tolist(),
        minimum_raw_interval_clearance_m=nodes[endpoint][4],terminal_goal_distance_m=float(np.linalg.norm(states[-1,:2]-goal)),wait_actions=sum(a['kind']=='wait'for a in actions))
