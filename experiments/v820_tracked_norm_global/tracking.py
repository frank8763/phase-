"""Causal bookkeeping at a stopped forward/reverse cusp.
Position tolerance only selects the next segment; all resulting wheel commands
still require the native rollout and footprint safety gate from the actual state.
"""
import numpy as np
from planner import wrap

def switch_if_settled(path,index,current,velocity):
    gear=int(path[min(index+1,len(path)-1),3]);end=index+1
    while end<len(path)-1 and int(path[end+1,3])==gear:end+=1
    if end>=len(path)-1:return index,None
    distance=float(np.linalg.norm(current[:2]-path[end,:2]));heading=abs(wrap(current[2]-path[end,2]));speed=float(np.linalg.norm(velocity[:2]))
    if distance<=.16 and heading<=.25 and speed<=.05:
        return end,{'status':'STOPPED_CUSP_SWITCH','from_gear':gear,'to_gear':int(path[end+1,3]),'old_index':int(index),'new_index':int(end),'position_error_m':distance,'heading_error_rad':heading,'actual_xy_speed_m_s':speed,'safety_scope':'bookkeeping only; next command still validated from actual state'}
    return index,None
