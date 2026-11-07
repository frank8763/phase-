"""Reference persistence uses the same spatial proposal field as the global search. It never certifies physical execution."""
import numpy as np
from planner import wrap

def route_check(field,path,index,current,rows,step,last_plan):
    end=min(len(path),index+26)
    if getattr(field,'temporal_state',None)is None:
        minimum=float(np.min(field.pose_values(path[index:end,:3])))
        extra={}
    else:
        from timed_reference import current_route_samples
        queries,times=current_route_samples(path,index,current)
        import math
        dense=[queries[0]];clock=[times[0]];dymax=.008*math.tan(.42722137342572125)/.6
        for a,b,ta,tb in zip(queries[:-1],queries[1:],times[:-1],times[1:]):
            dy=wrap(b[2]-a[2]);n=max(1,int(math.ceil(abs(dy)/dymax)))
            for u in np.arange(1,n+1)/n:dense.append([*(a[:2]+u*(b[:2]-a[:2])),a[2]+u*dy]);clock.append(ta+u*(tb-ta))
        queries=np.asarray(dense);times=np.asarray(clock)
        minimum=float(np.min(field.reference_values(queries,times)))
        extra={'time_reference_query_poses':queries.tolist(),'time_reference_query_times_s':times.tolist(),'temporal_validation_is_reference_only':True}
    current_invalid=minimum<.155-1e-6
    net_stagnant=False;arc_progress=None
    if step-last_plan>=30 and len(rows)>=30:
        previous=np.asarray(rows[-30]['pose']);old_index=int(rows[-30]['path_index'])
        net_stagnant=bool(np.linalg.norm(current[:2]-previous[:2])<.04 and abs(wrap(current[2]-previous[2]))<.06)
        lo=max(0,min(old_index,index));hi=min(len(path)-1,max(old_index,index))
        arc_progress=float(np.linalg.norm(np.diff(path[lo:hi+1,:2],axis=0),axis=1).sum())
    return {**extra,'current_route_minimum_m':minimum,'current_route_invalid':bool(current_invalid),'old_net_motion_stagnant':net_stagnant,'route_arc_progress_last30_m':arc_progress,'stagnated_without_route_progress':bool(net_stagnant and(arc_progress is None or arc_progress<.08)),'source':'current causal spatial proposal field and executed same-reference progress','validation_basis':'SAME_AS_GLOBAL_SEARCH_FIELD','dynamic_execution_certificate_separate':True,'authorizes_control':False,'future_native_gate_unchanged':True}
