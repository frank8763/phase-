"""Early bounded joint selection from causal nominal inputs and complete tails."""
import copy,gzip,json
import numpy as np
from recovery_supervisor import emit
from serial_predictor import project_to_segment_path

GUARD_M=.155+.08*3.28

def activate(reserved,state,step):
    if getattr(reserved,'early_joint_started_step',None)is not None:return False
    cache=reserved.cache
    if state['center']is None or cache is None:return False
    if cache['minimum_causal_predicted_clearance_m']>=GUARD_M:return False
    reserved.early_joint_started_step=int(step)
    return True

def representatives(unique,current_xy,goal):
    distance=float(np.linalg.norm(np.asarray(current_xy)-goal))
    eligible=[i for i,c in enumerate(unique)if float(np.mean(c[1][2:]))>=0. and distance-float(np.linalg.norm(c[2][-1,:2]-goal))>=.02]
    if not eligible:return []
    choices=[eligible[0],max(eligible,key=lambda i:(float(np.mean(unique[i][1][:2])),-i)),min(eligible,key=lambda i:(float(np.mean(unique[i][1][:2])),i)),max(eligible,key=lambda i:(float(np.mean(unique[i][1][2:])),-i))]
    return list(dict.fromkeys(choices))

def select(reserved,predictor,real,gate,field,state,step,path,index,cell,unique):
    goal=np.asarray(reserved.public_goal_xy,float)
    ranks=representatives(unique,real.qpos[:2],goal)
    if not ranks:return None
    before={k:getattr(reserved,k)for k in ['cache','cursor','expected','expected_ctrl','finish_pending']}
    q=real.qpos.copy();v=real.qvel.copy();ctrl=real.ctrl.copy();time0=float(real.time)
    records=[];admitted=[];directory=cell/'early_joint';directory.mkdir(exist_ok=True)
    try:
        reserved.proactive=True
        for rank in ranks:
            score,command,trajectory,clearance,self_margin=unique[rank]
            summary=reserved.admit_nominal(real,command,field,state,step)
            detail=copy.deepcopy(reserved.last_attempt)
            row=dict(rank=rank,nominal_score=float(score),first_command=command.tolist(),summary=summary,detail=detail,certificate=None)
            if summary is not None:
                cache=copy.deepcopy(reserved.cache)
                gain=float(np.linalg.norm(q[:2]-goal)-np.linalg.norm(cache['qpos'][-1,:2]-goal))
                value=float(cache['minimum_causal_predicted_clearance_m']+.5*gain)
                assert gain>=.02 and cache['proactive_joint']and abs(value-cache['score'])<=1e-10
                file=directory/f'step{step:04d}_rank{rank:02d}.json.gz';assert not file.exists()
                with gzip.open(file,'wt')as stream:json.dump(cache,stream,default=lambda x:x.tolist()if isinstance(x,np.ndarray)else x.item())
                row.update(certificate=str(file.relative_to(cell)),goal_gain_m=gain,joint_score=value,minimum_m=cache['minimum_causal_predicted_clearance_m'])
                admitted.append((value,float(score),-rank,cache,summary,rank))
            records.append(row)
            emit(cell,'control_decisions.jsonl',dict(step=step,candidate_role='ORDINARY',stage='EARLY_JOINT_APPEND',**row))
    finally:
        reserved.proactive=False
        for key,value in before.items():setattr(reserved,key,value)
    assert np.array_equal(real.qpos,q)and np.array_equal(real.qvel,v)and np.array_equal(real.ctrl,ctrl)and real.time==time0,'EARLY_JOINT_MUTATED_REAL_STATE'
    chosen=max(admitted,key=lambda x:x[:3])if admitted else None
    event=dict(step=step,started_step=reserved.early_joint_started_step,public_goal_xy=goal.tolist(),representative_ranks=ranks,probes=records,selected_rank=None if chosen is None else chosen[-1],original_unique_commands=len(unique),hidden_world_geometry_used=False,reference_path=np.asarray(path).tolist(),reference_index=int(index),real_qpos=q.tolist(),selection='max(complete328_minimum+.5*complete_goal_gain,nominal_score,-rank); all original gates plus336 continuation')
    emit(cell,'early_joint_decisions.jsonl',event)
    if chosen is None:return None
    value,nominal_score,_,cache,summary,rank=chosen
    reserved.cache=cache;reserved.cursor=0;reserved.expected=(np.asarray(cache['initial_qpos']),np.asarray(cache['initial_qvel']));reserved.expected_ctrl=np.asarray(cache['prefix_command']).copy();reserved.finish_pending=False
    reserved.last_prefix_qpos=np.asarray(cache['initial_qpos']).copy();reserved.last_prefix_qvel=np.asarray(cache['initial_qvel']).copy()
    _,command,trajectory,clearance,self_margin=unique[rank];segments=path[index:min(gate['segment_end_index']+1,index+40),:3]
    selected=dict(gate);selected.update(score=float(nominal_score),predicted_minimum_clearance_m=float(clearance),predicted_self_domain_margin_m=float(self_margin),predicted_end_pose=trajectory[-1].tolist(),predicted_next_pose=trajectory[7].tolist(),terminal_projected_arc_m=float(project_to_segment_path(trajectory[-1:],segments)[0][0]),joint_admission_distinct_command_rank=rank,joint_admission_maximum_commands=len(unique),ordinary_maximum_score=float(unique[0][0]),early_joint_selection=True,early_joint_score=float(value),early_joint_probes=len(ranks))
    return command.copy(),selected,summary
