"""Direct finite-progress search with causal cycle geometry on every edge."""
import heapq,importlib.util,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=R/'experiments/v997_input_consistent_recovery'
sys.path.insert(0,str(C));s=importlib.util.spec_from_file_location('v1000_frozen_response',C/'state_reference.py');ref=importlib.util.module_from_spec(s);s.loader.exec_module(ref)

def construct(packet,source,goal,known,now,deadline):
    initial=ref.snapshot_state(packet,source,now);goal=np.asarray(goal,float);geometry=ref._old.Geometry(known,source['periodic'])
    static,dynamic=geometry.clearances(initial[None,:3]);lower=float(min(static[0],dynamic[0]))
    base=dict(passed=False,models=0,integrations=0,private_dynamics_predictions=0,original_goal=goal.tolist(),
        initial_state=initial.tolist(),source_native_tick=source['source_native_tick'],body_native_tick=packet['native_tick'],
        required_clearance_m=ref.REQUIRED,unchanged_actual_progress_requirement_m=.4,path=[],physical_tracking_qualified=False)
    if lower<ref.REQUIRED:return dict(base,status='INITIAL_FULL_CYCLE_REJECTED')
    # This heuristic is preference only. Every edge uses the full causal cycle.
    heuristic,hproof=ref._old.Geometry(known,None).heuristic(goal)
    def key(p,depth):return(round(p[0]/.05),round(p[1]/.05),round((p[2]%(2*math.pi))*72/(2*math.pi))%72,round(p[3]/(ref.MAX_DELTA/2)))
    nodes=[(initial,-1,None,0,lower)];best={key(initial,0):0.};heap=[(1.5*heuristic(initial),0.,0)]
    expanded=rejected=0;end=None;begun=time.monotonic();samples=np.linspace(ref.STEP/ref.EDGE_N,ref.STEP,ref.EDGE_N)
    while heap and expanded<5000 and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,_,_,depth,minimum=nodes[index]
        if cost>best.get(key(state,depth),math.inf)+1e-10:continue
        expanded+=1;nominal,progress=ref.progress_lower_bound(initial,state,goal)
        if depth>0 and progress>=.4:end=index;break
        if depth>=12:continue
        edges=np.array([ref.primitive(state,t,samples)for t in ref.TARGETS]);a,b=geometry.clearances(edges[:,:,:3].reshape(-1,3));values=np.minimum(a,b).reshape(len(ref.TARGETS),ref.EDGE_N)
        allowed=(values>=ref.REQUIRED).all(axis=1)
        for j,target in enumerate(ref.TARGETS):
            if not allowed[j]:rejected+=1;continue
            child=edges[j,-1];next_cost=cost+ref.STEP*(1+.15*abs(target)/ref.MAX_DELTA)+.02*abs(target-state[3])/ref.MAX_DELTA
            marker=key(child,depth+1)
            if next_cost>=best.get(marker,math.inf)-1e-10:continue
            best[marker]=next_cost;nodes.append((child,index,float(target),depth+1,min(minimum,float(values[j].min()))))
            heapq.heappush(heap,(next_cost+1.5*heuristic(child),next_cost,len(nodes)-1))
    report=dict(base,expanded=expanded,generated=len(nodes),rejected_edges=rejected,max_expansions=5000,heuristic=hproof,wall_s=time.monotonic()-begun)
    if end is None:return dict(report,status='WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=5000 else'NO_PREFIX_IN_BOUNDED_SEARCH')
    terminal=end;chain=[]
    while end!=-1:chain.append(end);end=nodes[end][1]
    chain.reverse();targets=[nodes[i][2]for i in chain[1:]];states=[initial]
    for target in targets:states.extend(ref.primitive(states[-1],target,samples))
    states=np.array(states);nominal,progress=ref.progress_lower_bound(initial,states[-1],goal)
    return dict(report,passed=True,status='CAUSAL_FINITE_PROGRESS_REFERENCE',state_path=states.tolist(),path=states[:,:3].tolist(),edge_targets=targets,
        nominal_length_m=nodes[terminal][3]*ref.STEP,nominal_goal_progress_m=nominal,actual_goal_progress_lower_m=progress,
        minimum_raw_full_cycle_clearance_m=nodes[terminal][4],reference_speed_m_s=.05,virtual_steering_rate_rad_s=.6,
        response_parameters=ref.PARAMETERS,full_goal_route_required=False,full_goal_reached_claim=False)
