"""Install the one early joint change before the first new model."""
import ast
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=repo/'experiments/v841_early_joint'
assert not(own/'CANDIDATE_FREEZE.json').exists()
p=own/'reserved_recovery.py';s=p.read_text().replace("active=reference is not None and state['center']is not None", "proactive=bool(getattr(self,'proactive',False))\n        active=proactive and reference is not None and state['center']is not None")
s=s.replace("if library!='ORIGINAL'and best is not None:break", "if not proactive and library!='ORIGINAL'and best is not None:break")
s=s.replace("goal_gain=None if not following else", "goal_gain=None if not(following or proactive)else")
s=s.replace("else'ESCAPE_NO_GOAL_PROGRESS'if following and goal_gain<.02 else None", "else'PROACTIVE_NO_GOAL_PROGRESS'if proactive and goal_gain<.02 else'ESCAPE_NO_GOAL_PROGRESS'if following and goal_gain<.02 else None")
s=s.replace("                if reason is not None:continue", "                if proactive:detail['joint_goal_gain_m']=goal_gain\n                if reason is not None:continue")
s=s.replace("                if best is not None and score<=best['score']:continue", "                if proactive:score=minimum+.5*goal_gain\n                detail['selection_score']=float(score)\n                if best is not None and score<=best['score']:continue")
s=s.replace("best={'score':score", "best={'proactive_joint':proactive,'score':score")
p.write_text(s)
p=own/'joint_admission.py';s=p.read_text();needle="    for rank,(score,command,trajectory,clearance,self_margin)in enumerate(unique):"
insert="""    if getattr(reserved,'early_joint_started_step',None)is not None and getattr(reserved,'reference',None)is not None:
        from early_joint import select
        result=select(reserved,predictor,real,gate,field,state,step,path,index,cell,unique)
        if result is not None:return result
"""
s=s.replace(needle,insert+needle);p.write_text(s)
p=own/'run_static.py';s=p.read_text();needle="                    else:\n                        if path is not None and backup_remaining==0:"
insert="""                    else:
                        from early_joint import activate,GUARD_M
                        if activate(reserved,motion_state,step):
                            emit(cell,'early_joint_activation.jsonl',{'step':step,'guard_m':GUARD_M,'previous_reserve_minimum_m':reserved.cache['minimum_causal_predicted_clearance_m'],'previous_created_step':reserved.cache['created_step'],'hidden_world_geometry_used':False})
                        early_start=getattr(reserved,'early_joint_started_step',None)
                        if early_start is not None and last_plan<early_start and step-last_plan>=12 and motion_state['observed_this_frame']:
                            need=True
                            emit(cell,'early_joint_replan.jsonl',{'step':step,'started_step':early_start,'last_plan':last_plan,'observed_this_frame':True,'authorizes_control':False})
                        if path is not None and backup_remaining==0:"""
assert needle in s;s=s.replace(needle,insert);p.write_text(s)
for p in own.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
print('PROACTIVE_REFERENCE_GENERATION_AND_JOINT_FIRST_COMMAND_SELECTION_INSTALLED')
