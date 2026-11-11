"""Geometry candidate for a full recovery route, forward-first then reversible.

Reverse geometry is NOT a calibrated reverse dynamics certificate. A candidate
requires separate complete actual-input/physics qualification before execution.
"""
import heapq,math,time
import numpy as np
from full_route import ref,REQUIRED,GOAL_RADIUS,MAX_EXPANSIONS,MAX_EDGES
GX,GW=np.polynomial.legendre.leggauss(8)

def primitive(state,target,distances,direction):
    x,y,a,d0=np.asarray(state,float);s=np.asarray(distances,float);change=target-d0
    if abs(change)<1e-13:
        poses=ref._old.primitive([x,y,a],direction,ref.GAIN*math.tan(d0)/.6,s)
        return np.c_[poses,np.full(len(s),d0)]
    slope=math.copysign(.6/.03,change);ramp=abs(change)/abs(slope);u=np.minimum(s,ramp);delta=d0+slope*u
    def heading(at):return a-direction*ref.GAIN*(np.log(np.cos(d0+slope*at))-math.log(math.cos(d0)))/(.6*slope)+ref.RATE_COUPLING*slope*at
    points=u[:,None]*(GX[None,:]+1)/2;h=heading(points)
    px=x+direction*u/2*(np.cos(h)@GW);py=y+direction*u/2*(np.sin(h)@GW);h=heading(u);tail=s-u;kt=ref.GAIN*math.tan(target)/.6
    if abs(kt)<1e-12:px+=direction*tail*np.cos(h);py+=direction*tail*np.sin(h)
    else:px+=(np.sin(h+direction*kt*tail)-np.sin(h))/kt;py-=(np.cos(h+direction*kt*tail)-np.cos(h))/kt
    return np.c_[px,py,h+direction*kt*tail,delta]

def construct(packet,source,goal,known,deadline,allow_reverse=False):
    initial=ref.snapshot_state(packet,source,packet['body_measured_at']);goal=np.asarray(goal,float);geom=ref._old.Geometry(known,source['periodic']);a,b=geom.clearances(initial[None,:3]);lower=float(min(a[0],b[0]))
    base=dict(passed=False,models=0,integrations=0,scope='COMPLETE_GEOMETRIC_RECOVERY_CANDIDATE_NOT_ACTUATION_AUTHORITY',original_goal=goal.tolist(),original_goal_radius_m=.45,required_clearance_m=REQUIRED,
        initial_state=initial.tolist(),source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'],allow_reverse_geometry=allow_reverse,physical_ready=False,reverse_dynamics_qualified=False)
    if lower<REQUIRED:return dict(base,status='INITIAL_FULL_CYCLE_REJECTED',expanded=0)
    heuristic,hproof=geom.heuristic(goal);samples=np.linspace(.1/8,.1,8)
    def key(p,gear,run):return(round(p[0]/.05),round(p[1]/.05),round((p[2]%(2*math.pi))*144/(2*math.pi))%144,round(p[3]/(ref.MAX_DELTA/2)),gear,min(run,3))
    nodes=[(initial,-1,None,0,0,0,lower)];best={key(initial,0,0):0.};heap=[(1.5*heuristic(initial),0.,0)];expanded=rejected=0;begun=time.monotonic();best_goal=float(np.linalg.norm(initial[:2]-goal));end=None
    controls=[(gear,float(target))for gear in ([1,-1]if allow_reverse else[1])for target in ref.TARGETS]
    while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,_,_,depth,gear,run,minimum=nodes[index]
        if cost>best.get(key(state,gear,run),math.inf)+1e-10:continue
        expanded+=1;error=float(np.linalg.norm(state[:2]-goal));best_goal=min(best_goal,error)
        if depth>0 and error<=GOAL_RADIUS:end=index;break
        if depth>=MAX_EDGES:continue
        edges=np.asarray([primitive(state,target,samples,direction)for direction,target in controls]);a,b=geom.clearances(edges[:,:,:3].reshape(-1,3));values=np.minimum(a,b).reshape(len(controls),8)
        for j,(direction,target)in enumerate(controls):
            if gear and gear!=direction and run<3:continue
            if values[j].min()<REQUIRED:rejected+=1;continue
            child=edges[j,-1];nr=min(3,run+1)if direction==gear else 1
            nc=cost+.1*(1 if direction>0 else 2)+.015*abs(target)/ref.MAX_DELTA+.02*abs(target-state[3])/ref.MAX_DELTA+(.4 if gear and direction!=gear else 0)
            marker=key(child,direction,nr)
            if nc>=best.get(marker,math.inf)-1e-10:continue
            best[marker]=nc;nodes.append((child,index,dict(direction=direction,target=target),depth+1,direction,nr,min(minimum,float(values[j].min()))));heapq.heappush(heap,(nc+1.5*heuristic(child),nc,len(nodes)-1))
    report=dict(base,expanded=expanded,generated=len(nodes),rejected_edges=rejected,best_goal_distance_m=best_goal,wall_s=time.monotonic()-begun)
    if end is None:return dict(report,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_COMPLETE_GEOMETRIC_ROUTE')
    terminal=end;chain=[]
    while end!=-1:chain.append(end);end=nodes[end][1]
    actions=[nodes[i][2]for i in reversed(chain[:-1])];states=[initial]
    for action in actions:states.extend(primitive(states[-1],action['target'],samples,action['direction']))
    states=np.asarray(states)
    return dict(report,passed=True,status='COMPLETE_GEOMETRIC_RECOVERY_CANDIDATE',actions=actions,path=states[:,:3].tolist(),state_path=states.tolist(),
        minimum_raw_full_cycle_clearance_m=nodes[terminal][6],terminal_goal_distance_m=float(np.linalg.norm(states[-1,:2]-goal)),reverse_edges=sum(x['direction']<0 for x in actions),gear_changes=sum(a['direction']!=b['direction']for a,b in zip(actions,actions[1:])))
