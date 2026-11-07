"""Causal reference-based certified return from an executing finite backup."""
import json,math,os
from pathlib import Path
import numpy as np

def emit(cell,name,record):
    def default(x):return x.tolist()if isinstance(x,np.ndarray)else x.item()
    with (Path(cell)/name).open('a')as stream:stream.write(json.dumps(record,default=default,allow_nan=False)+'\n')

class RecoverySupervisor:
    def __init__(self,cell):self.cell=Path(cell);self.path=None;self.index=None;self.first_step=None;self.attempts=0;self.successes=0
    def remember(self,path,index,step):
        self.path=None if path is None else np.asarray(path).copy();self.index=int(index);self.first_step=int(step)
    def try_return(self,env,field,state,reserved,predictor,current,last_command,step):
        mode=os.environ.get('PHASE_RECOVERY_ABLATION','FULL')
        assert mode in ('FULL','SHADOW_COMPLETE_TAIL'),'UNREGISTERED_RETURN_MODE'
        before=int(predictor.prediction_steps);q=env.data.qpos.copy();v=env.data.qvel.copy();ctrl=env.data.ctrl.copy();time0=float(env.data.time)
        self.last_shadow_feasible=False
        answer=self._try_return_impl(env,field,state,reserved,predictor,current,last_command,step)
        assert np.array_equal(q,env.data.qpos) and np.array_equal(v,env.data.qvel) and np.array_equal(ctrl,env.data.ctrl) and time0==float(env.data.time),'RETURN_EVALUATION_MUTATED_REAL_STATE'
        emit(self.cell,'return_compute.jsonl',{'step':step,'mode':mode,'prediction_before':before,'prediction_after':int(predictor.prediction_steps),'prediction_delta':int(predictor.prediction_steps)-before,'returned':answer is not None,'shadow_feasible':self.last_shadow_feasible,'real_state_unchanged':True,'hidden_world_geometry_used':False})
        return answer
    def _try_return_impl(self,env,field,state,reserved,predictor,current,last_command,step):
        if self.path is None or self.first_step is None:return None
        age=step-self.first_step
        if step<getattr(reserved,'maneuver_commit_until',self.first_step+4)or age%4:return None
        self.attempts+=1;reserved.check_current_contract(env.data)
        path=self.path;old_index=self.index;gear=int(path[min(old_index+1,len(path)-1),3])
        record={'step':step,'backup_age_public_steps':age,'old_created_step':int(reserved.cache['created_step']),'old_native_cursor':reserved.cursor,'candidate_role':'BACKUP_RETURN','hidden_world_geometry_used':False}
        if gear not in[-1,1]:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'REFERENCE_NOT_FORWARD'});return None
        end=old_index+1
        while end<len(path)-1 and int(path[end+1,3])==gear:end+=1
        start=old_index
        while start>0 and int(path[start,3])==gear:start-=1
        lo=max(start,old_index-12);hi=min(end,old_index+40);index=lo+int(np.argmin(np.linalg.norm(path[lo:hi+1,:2]-current[:2],axis=1)));index=min(index,end-1)
        target_index=index+1;arc=0.
        while target_index<len(path)-1 and arc<.45 and int(path[target_index+1,3])==gear:
            arc+=float(np.linalg.norm(path[target_index+1,:2]-path[target_index,:2]));target_index+=1
        target=path[target_index,:2];rel=target-current[:2];lateral=-math.sin(current[2])*rel[0]+math.cos(current[2])*rel[1]
        steer=float(np.clip(math.atan2(2*float(env.inner.wheel_base)*lateral,max(float(rel@rel),.02)),-env.inner.max_steer,env.inner.max_steer));speed=gear*min(.60,.50/(1+abs(steer)))
        distance=float(np.linalg.norm(current[:2]-env.goal_xy))
        if distance<1.:speed*=.65
        proposal,gate=predictor.select(env,field,path,index,current,steer,speed,last_command)
        emit(self.cell,'control_decisions.jsonl',{**record,'stage':'NOMINAL','summary':gate,'candidates':getattr(predictor,'last_diagnostics',[])})
        if proposal is None:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'NO_SAFE_NOMINAL','nominal_gate':gate});return None
        reserved.set_reference(path,index,env.goal_xy,float(env.inner.wheel_base))
        ranked=predictor.ranked_safe_candidates
        assert ranked and len(ranked)<=25 and np.array_equal(ranked[0][1],proposal),'RETURN_ORIGINAL_RANKING_CHANGED'
        seen=set();summary=None;selected=None
        for rank,(score,command,trajectory,clearance,self_margin) in enumerate(ranked):
            progress=distance-float(np.linalg.norm(trajectory[-1,:2]-env.goal_xy))
            detail={**record,'stage':'RETURN_SELECTION','nominal_rank':rank,'ordinary_score':float(score),'first_command':command.tolist(),'predicted_end_pose':trajectory[-1].tolist(),'predicted_goal_progress_m':progress,'nominal_candidates_total':len(ranked)}
            if False:  # ordinary and return now use the same complete segment merit
                emit(self.cell,'control_decisions.jsonl',{**detail,'status':'SKIPPED_ORIGINAL_PROGRESS_GATE'});continue
            key=tuple(command)
            if key in seen:
                emit(self.cell,'control_decisions.jsonl',{**detail,'status':'SKIPPED_DUPLICATE_ELIGIBLE_COMMAND'});continue
            seen.add(key)
            old=reserved.cache;old_cursor=reserved.cursor
            summary=reserved.try_handover(env.data,command,field,state,step,{'predicted_goal_progress_m':progress,'active_gear':gear,'guidance_scope':'past causal geometry reference; fresh complete native admission','reference_index':index,'public_goal_xy':np.asarray(env.goal_xy).tolist(),'return_nominal_rank':rank,'return_ordinary_score':float(score)},commit=os.environ.get('PHASE_RECOVERY_ABLATION','FULL')=='FULL')
            emit(self.cell,'control_decisions.jsonl',{**record,'stage':'BACKUP_APPEND','return_nominal_rank':rank,'first_command':command.tolist(),'detail':reserved.last_handover_attempt})
            if summary is None:
                assert reserved.cache is old and reserved.cursor==old_cursor,'RANKED_FAILED_HANDOVER_CHANGED_RETAINED_CONTRACT'
                emit(self.cell,'control_decisions.jsonl',{**detail,'status':'COMPLETE_ADMISSION_REJECTED','old_contract_retained':True});continue
            emit(self.cell,'control_decisions.jsonl',{**detail,'status':'SHADOW_FULL_CERTIFICATE'if summary.get('shadow_only')else'COMPLETE_ADMISSION_ACCEPTED'})
            selected=(rank,score,command,trajectory,clearance,self_margin,progress);break
        if selected is None:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'NO_PROGRESS_CANDIDATE_WITH_COMPLETE_BACKUP','examined_nominal_candidates':len(ranked),'distinct_complete_attempts':len(seen)});return None
        rank,score,proposal,trajectory,clearance,self_margin,goal_progress=selected
        if summary.get('shadow_only'):
            self.last_shadow_feasible=True
            emit(self.cell,'shadow_return_attempts.jsonl',{**record,'status':'SHADOW_FEASIBLE_RETURN_SUPPRESSED','predicted_goal_progress_m':goal_progress,'certificate':summary['shadow_certificate'],'old_contract_retained':True})
            return None
        self.successes+=1;emit(self.cell,'handover_attempts.jsonl',{**record,'status':'CERTIFIED_RETURN','maneuver_progress_allowed':bool(reserved.cache['maneuver_contract']['normal_allowed']),'predicted_goal_progress_m':goal_progress,'certificate':summary['handover_certificate']})
        from serial_predictor import project_to_segment_path
        gate=dict(gate)
        segments=path[index:min(gate['segment_end_index']+1,index+40),:3]
        gate.update(score=float(score),predicted_minimum_clearance_m=float(clearance),predicted_self_domain_margin_m=float(self_margin),predicted_end_pose=trajectory[-1].tolist(),predicted_next_pose=trajectory[7].tolist(),terminal_projected_arc_m=float(project_to_segment_path(trajectory[-1:],segments)[0][0]),return_nominal_rank=rank,return_original_candidates=len(ranked),recovery_reserve=summary,certified_backup_handover=True,prediction_steps_total=predictor.prediction_steps)
        return proposal,gate,path.copy(),index
