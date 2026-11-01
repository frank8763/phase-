"""Causal reference-based certified return from an executing finite backup."""
import json,math
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
        if self.path is None or self.first_step is None:return None
        age=step-self.first_step
        if age<4 or age%4:return None
        self.attempts+=1;reserved.check_current_contract(env.data)
        path=self.path;old_index=self.index;gear=int(path[min(old_index+1,len(path)-1),3])
        record={'step':step,'backup_age_public_steps':age,'old_created_step':int(reserved.cache['created_step']),'old_native_cursor':reserved.cursor,'candidate_role':'BACKUP_RETURN','hidden_world_geometry_used':False}
        if gear!=1:
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
        steer=float(np.clip(math.atan2(2*float(env.inner.wheel_base)*lateral,max(float(rel@rel),.02)),-env.inner.max_steer,env.inner.max_steer));speed=min(.60,.50/(1+abs(steer)))
        distance=float(np.linalg.norm(current[:2]-env.goal_xy))
        if distance<1.:speed*=.65
        proposal,gate=predictor.select(env,field,path,index,current,steer,speed,last_command)
        emit(self.cell,'control_decisions.jsonl',{**record,'stage':'NOMINAL','summary':gate,'candidates':getattr(predictor,'last_diagnostics',[])})
        if proposal is None:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'NO_SAFE_NOMINAL','nominal_gate':gate});return None
        goal_progress=distance-float(np.linalg.norm(np.asarray(gate['predicted_end_pose'])[:2]-env.goal_xy))
        if goal_progress<.02:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'INSUFFICIENT_PREDICTED_GOAL_PROGRESS','predicted_goal_progress_m':goal_progress});return None
        summary=reserved.try_handover(env.data,proposal,field,state,step,{'predicted_goal_progress_m':goal_progress,'active_gear':1,'guidance_scope':'past causal geometry reference; fresh complete native admission','reference_index':index})
        emit(self.cell,'control_decisions.jsonl',{**record,'stage':'BACKUP_APPEND','detail':reserved.last_handover_attempt})
        if summary is None:
            emit(self.cell,'handover_attempts.jsonl',{**record,'status':'NOMINAL_SAFE_BUT_NO_BACKUP','predicted_goal_progress_m':goal_progress});return None
        self.successes+=1;emit(self.cell,'handover_attempts.jsonl',{**record,'status':'CERTIFIED_RETURN','predicted_goal_progress_m':goal_progress,'certificate':summary['handover_certificate']})
        gate.update(recovery_reserve=summary,certified_backup_handover=True,prediction_steps_total=predictor.prediction_steps)
        return proposal,gate,path.copy(),index
