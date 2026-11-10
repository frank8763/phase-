"""Only the visited-state quantization differs; frozen V997 motion/geometry."""
import heapq,importlib.util,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=R/'experiments/v997_input_consistent_recovery'
sys.path.insert(0,str(C))
s=importlib.util.spec_from_file_location('v999_frozen_response_reference',C/'state_reference.py')
ref=importlib.util.module_from_spec(s);s.loader.exec_module(ref)

def search(start,goal,known,variant,deadline):
    start=np.asarray(start);geometry=ref._old.Geometry(known,None);heuristic,hproof=geometry.heuristic(goal)
    res=variant['xy_res'];bins=variant['yaw_bins'];steering=variant['steering_bins']
    def key(p):return(round(p[0]/res),round(p[1]/res),round((p[2]%(2*math.pi))*bins/(2*math.pi))%bins,round(p[3]/(ref.MAX_DELTA/steering)))
    nodes=[(start,-1,None)];best={key(start):0.};best_pose={key(start):start}
    heap=[(1.5*heuristic(start),0.,0)];samples=np.linspace(ref.STEP/ref.EDGE_N,ref.STEP,ref.EDGE_N)
    endpoint=None;expanded=rejected=pruned=distinct=0;maximum_merge_xy=maximum_merge_yaw=0.;begun=time.monotonic()
    while heap and expanded<ref.MAX_EXPANSIONS and time.time()<deadline:
        _,cost,index=heapq.heappop(heap);state,_,_=nodes[index]
        if cost>best.get(key(state),math.inf)+1e-10:continue
        expanded+=1
        if np.linalg.norm(state[:2]-goal)<=.2:endpoint=index;break
        edges=np.array([ref.primitive(state,t,samples)for t in ref.TARGETS]);values=geometry.clearances(edges[:,:,:3].reshape(-1,3))[0].reshape(len(ref.TARGETS),ref.EDGE_N)
        allowed=(values>=ref.REQUIRED).all(axis=1)
        for j,target in enumerate(ref.TARGETS):
            if not allowed[j]:rejected+=1;continue
            child=edges[j,-1];next_cost=cost+ref.STEP*(1+.15*abs(target)/ref.MAX_DELTA)+.02*abs(target-state[3])/ref.MAX_DELTA;marker=key(child)
            if next_cost>=best.get(marker,math.inf)-1e-10:
                pruned+=1
                if marker in best_pose:
                    previous=best_pose[marker];xy=float(np.linalg.norm(child[:2]-previous[:2]));a=abs(math.atan2(math.sin(child[2]-previous[2]),math.cos(child[2]-previous[2])))
                    if max(xy,a)>1e-10:distinct+=1
                    maximum_merge_xy=max(maximum_merge_xy,xy);maximum_merge_yaw=max(maximum_merge_yaw,a)
                continue
            best[marker]=next_cost;best_pose[marker]=child;nodes.append((child,index,float(target)))
            heapq.heappush(heap,(next_cost+1.5*heuristic(child),next_cost,len(nodes)-1))
    reason='GOAL_FOUND'if endpoint is not None else'WALL_CAP'if time.time()>=deadline else'WORK_CAP'if expanded>=ref.MAX_EXPANSIONS else'HEAP_EXHAUSTED'
    result=dict(passed=endpoint is not None,status=reason,expanded=expanded,generated=len(nodes),rejected_edges=rejected,max_expansions=ref.MAX_EXPANSIONS,
        variant=variant,pruned_same_key=pruned,distinct_pose_merges=distinct,maximum_pruned_merge_xy_m=maximum_merge_xy,
        maximum_pruned_merge_yaw_rad=maximum_merge_yaw,heuristic=hproof,wall_s=time.monotonic()-begun)
    if endpoint is None:return result
    chain=[]
    while endpoint!=-1:chain.append(endpoint);endpoint=nodes[endpoint][1]
    chain.reverse();return dict(result,states=[nodes[i][0].tolist()for i in chain],targets=[nodes[i][2]for i in chain[1:]])

def prefix(route,start,goal,known,source):
    if not route['passed']:return dict(passed=False,status='NO_FULL_GOAL_STATIC_ROUTE')
    geometry=ref._old.Geometry(known,source['periodic']);dense=[np.array(start)];targets=[];options=[];minimum=math.inf
    for target in route['targets'][:round(ref.MAX_LENGTH/ref.STEP)]:
        segment=ref.primitive(dense[-1],target,np.linspace(ref.STEP/ref.EDGE_N,ref.STEP,ref.EDGE_N))
        a,b=geometry.clearances(segment[:,:3]);lower=float(np.minimum(a,b).min())
        if lower<ref.REQUIRED:break
        dense.extend(segment);targets.append(target);minimum=min(minimum,lower)
        nominal,progress=ref.progress_lower_bound(start,dense[-1],goal)
        if progress>=.4:options.append((len(targets),nominal,progress))
    if not options:return dict(passed=False,status='NO_CERTIFIED_ACTUAL_PROGRESS_LOWER_BOUND',available_length_m=len(targets)*ref.STEP)
    count,nominal,progress=options[-1];states=np.array(dense[:count*ref.EDGE_N+1])
    return dict(passed=True,status='ANALYTICAL_PREFIX_ONLY',initial_state=list(start),edge_targets=targets[:count],state_path=states.tolist(),path=states[:,:3].tolist(),
        original_goal=list(goal),nominal_length_m=count*ref.STEP,actual_goal_progress_lower_m=progress,minimum_raw_full_cycle_clearance_m=minimum,
        source_native_tick=source['source_native_tick'],physical_tracking_qualified=False)
