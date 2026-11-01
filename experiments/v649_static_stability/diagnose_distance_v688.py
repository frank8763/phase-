"""Post-run/all-prefix persisted route/controller decomposition, no integrations."""
import os,json,gzip,hashlib,math
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v688_dynamic_distance_curriculum';pair=root/'teacher6m/paired';cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
trace=read(cell/'trace.json');ad=lines(cell/'model_admission.jsonl');decisions=lines(cell/'control_decisions.jsonl');plans={int(p.stem.split('_')[-1]):read(p)for p in cell.glob('planning_*.json')};result=read(cell/'result.json');goals=np.r_[6.,[x['goal_distance_m']for x in trace]];progress=np.diff(-goals)
by_status={};normal_reverse=[];nominal={x['step']:x for x in decisions if x['stage']=='NOMINAL'}
for x in ad:
 group='OBSERVATION'if x.get('observation_initialization')else'RETAINED_BACKUP'if x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'else'ORDINARY_FORWARD'if x['active_gear']==1 else'ORDINARY_REVERSE'
 by_status.setdefault(group,{'steps':0,'net_goal_progress_m':0.});by_status[group]['steps']+=1;by_status[group]['net_goal_progress_m']+=float(progress[x['step']])
 if group=='ORDINARY_REVERSE':
  k=x['step'];before=[-3.,-2.]if k==0 else trace[k-1]['pose'][:2];normal_reverse.append({'step':k,'predicted_goal_progress_m':float(np.linalg.norm(np.asarray(before)-[3,-2])-np.linalg.norm(np.asarray(x['predicted_end_pose'])[:2]-[3,-2])),'predicted_local_arc_progress_m':x['terminal_projected_arc_m']-x['current_projected_arc_m'],'actual_goal_progress_m':float(progress[k])})
first_failed_append=[]
for step in sorted(nominal):
 tests=[d for d in decisions if d['step']==step and d['stage']=='BACKUP_APPEND'and d['detail']['status']in ['NO_APPENDABLE_BACKUP','PREFIX_SELF_DOMAIN_REJECTED']]
 if tests:
  first_failed_append.append({'step':step,'safe_ordinary_count':len([c for c in nominal[step]['candidates']if c['reason']is None]),'tested_append_failures':tests})
  if len(first_failed_append)==3:break
plan_summary=[]
for step,x in sorted(plans.items()):
 path=np.asarray(x['path'])if x['path']is not None else np.empty((0,4));gears=path[:,3]if len(path)else[]
 plan_summary.append({'step':step,'status':x['stats']['status'],'minimum_clearance_m':x['stats'].get('minimum_clearance_m'),'forward_pose_count':int(np.sum(gears==1)),'reverse_pose_count':int(np.sum(gears==-1)),'cusp_count':int(np.sum(np.diff(gears)!=0))if len(path)else 0,'first_executed_route_gear':None if len(path)<2 else int(path[1,3]),'projected_current_rectangle':x.get('causal_route_input',{}).get('rectangles',[])})
out={'status':'ZERO_INTEGRATION_CAUSE_DECOMPOSITION','final_result':result,'controller_groups':by_status,'minimum_actual_goal_distance_m':float(goals.min()),'net_actual_goal_progress_m':float(goals[0]-goals[-1]),'global_goal_routes':sum(x['status']=='GLOBAL_GOAL_PATH'for x in plan_summary),'routes_with_reverse':sum(x['reverse_pose_count']>0 for x in plan_summary),'routes':plan_summary,'ordinary_reverse_steps':len(normal_reverse),'ordinary_reverse_predicted_local_positive_but_goal_negative':sum(x['predicted_local_arc_progress_m']>0 and x['predicted_goal_progress_m']<0 for x in normal_reverse),'ordinary_reverse_first_ten':normal_reverse[:10],'first_three_failed_append_decisions':first_failed_append,'robot_integrations':0,'gradient_updates':0,'causal_attribution':'path direction/replanning, forward execution and reserve feasibility remain coupled; no global impossibility or unique cause claim'}
(root/'CAUSE_DECOMPOSITION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['final_result','routes','first_three_failed_append_decisions','ordinary_reverse_first_ten']},indent=2))
