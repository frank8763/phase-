"""Rank ordinary-safe inputs under the unchanged appendable-tail constraint."""
import numpy as np
from serial_predictor import project_to_segment_path
from recovery_supervisor import emit

def admit_ranked(reserved,predictor,real,proposal,gate,field,state,step,path,index,cell):
    if proposal is None:
        emit(cell,'control_decisions.jsonl',{'step':step,'candidate_role':'ORDINARY','stage':'BACKUP_APPEND','detail':{'status':'SKIPPED_NO_NOMINAL'}})
        return proposal,gate,None
    reserved.set_reference(path,index,getattr(reserved,'public_goal_xy',path[-1,:2]),.60)
    unique=[];seen=set()
    for candidate in predictor.ranked_safe_candidates:
        key=tuple(candidate[1])
        if key not in seen:seen.add(key);unique.append(candidate)
    assert unique and len(unique)<=25 and np.array_equal(unique[0][1],proposal),'RANKING_CHANGED_ORIGINAL_MAXIMUM'
    if getattr(reserved,'early_joint_started_step',None)is not None and getattr(reserved,'reference',None)is not None:
        from early_joint import select
        result=select(reserved,predictor,real,gate,field,state,step,path,index,cell,unique)
        if result is not None:return result
        if reserved.cache is not None:
            emit(cell,'progress_retained.jsonl',dict(step=step,old_created_step=reserved.cache['created_step'],old_cursor=reserved.cursor,reason='BOUNDED_EARLY_SEARCH_NO_BETTER_PROGRESS_CERTIFICATE',reference_path=np.asarray(path).tolist(),reference_index=int(index),real_qpos=real.qpos.tolist(),real_qvel=real.qvel.tolist(),real_time=float(real.time),old_terminal_qpos=np.asarray(reserved.cache['qpos'])[-1].tolist(),hidden_world_geometry_used=False))
            return proposal,gate,None
    for rank,(score,command,trajectory,clearance,self_margin)in enumerate(unique):
        summary=reserved.admit_nominal(real,command,field,state,step)
        emit(cell,'control_decisions.jsonl',{'step':step,'candidate_role':'ORDINARY','stage':'BACKUP_APPEND','distinct_command_rank':rank,'ordinary_score':float(score),'first_command':command.tolist(),'unexamined_distinct_safe_commands':len(unique)-rank-1,'detail':reserved.last_attempt})
        if summary is None:continue
        selected=dict(gate);segments=path[index:min(gate['segment_end_index']+1,index+40),:3]
        selected.update(progress_contract=reserved.cache.get('progress_contract'),recovery_entry_pending=reserved.progress_pending,score=float(score),predicted_minimum_clearance_m=float(clearance),predicted_self_domain_margin_m=float(self_margin),predicted_end_pose=trajectory[-1].tolist(),predicted_next_pose=trajectory[7].tolist(),terminal_projected_arc_m=float(project_to_segment_path(trajectory[-1:],segments)[0][0]),joint_admission_distinct_command_rank=rank,joint_admission_maximum_commands=len(unique),ordinary_maximum_score=float(unique[0][0]))
        return command.copy(),selected,summary
    return proposal,gate,None
