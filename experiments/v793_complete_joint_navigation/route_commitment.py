"""Reference persistence uses the same spatial proposal field as the global search. It never certifies physical execution."""
import numpy as np
from planner import wrap

def route_check(field,path,index,current,rows,step,last_plan):
    end=min(len(path),index+26)
    minimum=float(np.min(field.pose_values(path[index:end,:3])))
    current_invalid=minimum<.155-1e-6
    net_stagnant=False;arc_progress=None
    if step-last_plan>=30 and len(rows)>=30:
        previous=np.asarray(rows[-30]['pose']);old_index=int(rows[-30]['path_index'])
        net_stagnant=bool(np.linalg.norm(current[:2]-previous[:2])<.04 and abs(wrap(current[2]-previous[2]))<.06)
        lo=max(0,min(old_index,index));hi=min(len(path)-1,max(old_index,index))
        arc_progress=float(np.linalg.norm(np.diff(path[lo:hi+1,:2],axis=0),axis=1).sum())
    return {'current_route_minimum_m':minimum,'current_route_invalid':bool(current_invalid),'old_net_motion_stagnant':net_stagnant,'route_arc_progress_last30_m':arc_progress,'stagnated_without_route_progress':bool(net_stagnant and(arc_progress is None or arc_progress<.08)),'source':'current causal spatial proposal field and executed same-reference progress','validation_basis':'SAME_AS_GLOBAL_SEARCH_FIELD','dynamic_execution_certificate_separate':True,'authorizes_control':False,'future_native_gate_unchanged':True}
