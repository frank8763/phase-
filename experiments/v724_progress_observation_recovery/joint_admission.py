"""Rank ordinary-safe inputs under the unchanged appendable-tail constraint."""
import numpy as np
from serial_predictor import project_to_segment_path
from recovery_supervisor import emit

def admit_ranked(reserved,predictor,real,proposal,gate,field,state,step,path,index,cell):
    if proposal is None:
        emit(cell,'control_decisions.jsonl',{'step':step,'candidate_role':'ORDINARY','stage':'BACKUP_APPEND','detail':{'status':'SKIPPED_NO_NOMINAL'}})
        return proposal,gate,None
    unique=[];seen=set()
    for candidate in predictor.ranked_safe_candidates:
        key=tuple(candidate[1])
        if key not in seen:seen.add(key);unique.append(candidate)
    assert unique and np.array_equal(unique[0][1],proposal),'RANKING_CHANGED_ORIGINAL_MAXIMUM'
    for rank,(score,command,trajectory,clearance,self_margin)in enumerate(unique[:3]):
        summary=reserved.admit_nominal(real,command,field,state,step)
        emit(cell,'control_decisions.jsonl',{'step':step,'candidate_role':'ORDINARY','stage':'BACKUP_APPEND','distinct_command_rank':rank,'ordinary_score':float(score),'first_command':command.tolist(),'unexamined_distinct_safe_commands':len(unique)-rank-1,'detail':reserved.last_attempt})
        if summary is None:continue
        selected=dict(gate);segments=path[index:min(gate['segment_end_index']+1,index+40),:3]
        selected.update(score=float(score),predicted_minimum_clearance_m=float(clearance),predicted_self_domain_margin_m=float(self_margin),predicted_end_pose=trajectory[-1].tolist(),predicted_next_pose=trajectory[7].tolist(),terminal_projected_arc_m=float(project_to_segment_path(trajectory[-1:],segments)[0][0]),joint_admission_distinct_command_rank=rank,joint_admission_maximum_commands=3,ordinary_maximum_score=float(unique[0][0]))
        return command.copy(),selected,summary
    return proposal,gate,None
