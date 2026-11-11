"""Bounded forward steering-state search; success requires a complete goal route.

Analytical references only. Every edge uses the full causal periodic occupied
set and unchanged reserves. A geometry result alone never grants actuation.
"""
import heapq,importlib.util,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1022_calibrated_reference',R/'experiments/v997_input_consistent_recovery/state_reference.py');ref=importlib.util.module_from_spec(s);s.loader.exec_module(ref)
# Match reference timing to already qualified planned body requests. No actuator
# command, control gains or calibrated dynamics coefficient is changed.
ref.REFERENCE_SPEED=.03
# Exact virtual steering cap of the frozen actuator allocator.
ref.MAX_DELTA=.42722137342572125
ref.TARGETS=np.linspace(-ref.MAX_DELTA,ref.MAX_DELTA,5)
RHO=math.hypot(.44,.375)
REQUIRED=ref._old.REQUIRED+ref.NUMERICAL_RESERVE+RHO*abs(ref.RATE_COUPLING)*ref.VIRTUAL_RATE/ref.REFERENCE_SPEED*(ref.STEP/ref.EDGE_N)/2
GOAL_RADIUS=.25
MAX_EXPANSIONS=30000
MAX_EDGES=100

def reconstruct(nodes,index,initial,samples):
    chain=[]
    while index!=-1:chain.append(index);index=nodes[index][1]
    targets=[nodes[j][2]for j in reversed(chain[:-1])];states=[np.array(initial)]
    for target in targets:states.extend(ref.primitive(states[-1],target,samples))
    return targets,np.asarray(states)

def construct(packet,source,goal,known,deadline,accept_complete=None):
    initial=ref.snapshot_state(packet,source,packet['body_measured_at']);goal=np.asarray(goal,float)
    assert goal.shape==(2,)and np.isfinite(goal).all()
    geom=ref._old.Geometry(known,source['periodic']);a,b=geom.clearances(initial[None,:3]);lower=float(min(a[0],b[0]))
    base=dict(passed=False,status='FULL_ROUTE_NOT_FOUND',models=0,integrations=0,original_goal=goal.tolist(),original_goal_radius_m=.45,
        goal_reference_radius_m=GOAL_RADIUS,required_clearance_m=REQUIRED,initial_state=initial.tolist(),source_native_tick=source['source_native_tick'],
        body_native_tick=packet['native_tick'],full_goal_route_required=True,partial_progress_never_success=True)
    if lower<REQUIRED:return dict(base,status='INITIAL_FULL_CYCLE_REJECTED',expanded=0)
    heuristic,hproof=geom.heuristic(goal);samples=np.linspace(ref.STEP/ref.EDGE_N,ref.STEP,ref.EDGE_N)
    def key(p):return(round(p[0]/.025),round(p[1]/.025),round((p[2]%(2*math.pi))*144/(2*math.pi))%144,round(p[3]/(ref.MAX_DELTA/2)))
    nodes=[(initial,-1,None,0,lower)];best={key(initial):0.};heap=[(1.5*heuristic(initial),0.,0)]
    expanded=rejected=complete_rejected=0;start=time.monotonic();best_goal=float(np.linalg.norm(initial[:2]-goal));endpoint=None
    while heap and expanded<MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,_,_,depth,minimum=nodes[index]
        if cost>best.get(key(state),math.inf)+1e-10:continue
        expanded+=1;error=float(np.linalg.norm(state[:2]-goal));best_goal=min(best_goal,error)
        if depth>0 and error<=GOAL_RADIUS:
            targets,states=reconstruct(nodes,index,initial,samples)
            if accept_complete is None or accept_complete(targets,states):endpoint=index;break
            complete_rejected+=1
        if depth>=MAX_EDGES:continue
        edges=np.asarray([ref.primitive(state,target,samples)for target in ref.TARGETS]);a,b=geom.clearances(edges[:,:,:3].reshape(-1,3));values=np.minimum(a,b).reshape(len(ref.TARGETS),ref.EDGE_N)
        allowed=(values>=REQUIRED).all(axis=1)
        for j,target in enumerate(ref.TARGETS):
            if not allowed[j]:rejected+=1;continue
            child=edges[j,-1];next_cost=cost+ref.STEP*(1+.15*abs(target)/ref.MAX_DELTA)+.02*abs(target-state[3])/ref.MAX_DELTA
            marker=key(child)
            if next_cost>=best.get(marker,math.inf)-1e-10:continue
            best[marker]=next_cost;nodes.append((child,index,float(target),depth+1,min(minimum,float(values[j].min()))))
            heapq.heappush(heap,(next_cost+1.5*heuristic(child),next_cost,len(nodes)-1))
    report=dict(base,expanded=expanded,generated=len(nodes),rejected_edges=rejected,complete_candidates_rejected=complete_rejected,best_goal_distance_m=best_goal,
        max_expansions=MAX_EXPANSIONS,max_edges=MAX_EDGES,heuristic=hproof,wall_s=time.monotonic()-start)
    if endpoint is None:return dict(report,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=MAX_EXPANSIONS else'NO_COMPLETE_ROUTE_IN_BOUNDED_SEARCH')
    targets,states=reconstruct(nodes,endpoint,initial,samples)
    return dict(report,passed=True,status='COMPLETE_CAUSAL_GEOMETRIC_ROUTE',edge_targets=targets,path=states[:,:3].tolist(),state_path=states.tolist(),
        minimum_raw_full_cycle_clearance_m=nodes[endpoint][4],terminal_goal_distance_m=float(np.linalg.norm(states[-1,:2]-goal)),reference_speed_m_s=.03,
        calibrated_steady_minimum_turning_radius_m=1/(ref.GAIN*ref.K),physical_tracking_qualified=False)
