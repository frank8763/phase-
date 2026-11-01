"""Read-only planning/execution consistency statistics, no simulator imports."""
from pathlib import Path
import json,numpy as np
repo=Path(__file__).resolve().parents[2];cell=repo/'runs/v670_dynamic_empty_samples/dev38_95000011_empty/paired/geometry_memory';out=repo/'runs/v671_dynamic_consistency_diagnosis'
read=lambda p:json.loads(p.read_text())
trace=read(cell/'trace.json');states={s['step']:s for s in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};admissions=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()];plans=[]
for f in sorted(cell.glob('planning_*.json')):
 r=read(f);k=r['step'];path=np.asarray(r['path'])if r['path']is not None else np.empty((0,4));gear=int(path[1,3])if len(path)>1 else None
 length=float(np.linalg.norm(np.diff(path[:,:2],axis=0),axis=1).sum())if len(path)else None
 end=1
 while len(path)>end+1 and path[end+1,3]==gear:end+=1
 seglen=float(np.linalg.norm(np.diff(path[:end+1,:2],axis=0),axis=1).sum())if len(path)else None
 # First geometric crossing of the causal estimated actor's y coordinate.
 state=states[k];center=np.asarray(state['center']);side=None
 if len(path)>1:
  for a,b in zip(path[:-1],path[1:]):
   if min(a[1],b[1])<=center[1]<=max(a[1],b[1])and abs(b[1]-a[1])>1e-10:
    x=a[0]+(center[1]-a[1])/(b[1]-a[1])*(b[0]-a[0]);side='RIGHT'if x>center[0]else'LEFT';break
 plans.append({'step':k,'status':r['stats']['status'],'first_gear':gear,'first_gear_length_m':seglen,'total_path_length_m':length,'causal_crossing_side':side,'goal_distance_m':trace[k-1]['goal_distance_m']if k else float(np.linalg.norm(np.asarray(r['pose'])[:2]-read(cell.parent/'STATIC_PROTOCOL.json')['goal_xy'])),'expanded':r['stats']['expanded'],'wall_s':r['stats']['wall_s'],'current_center_xy':center.tolist()})
for i,r in enumerate(plans):
 end=plans[i+1]['step']if i+1<len(plans)else len(trace);start=r['step'];chunk=trace[start:end]
 r.update(executed_public_until_next_plan=len(chunk),actual_travel_before_next_plan_m=float(np.linalg.norm(np.diff(np.asarray([x['pose'][:2]for x in chunk]),axis=0),axis=1).sum())if len(chunk)>1 else 0.,goal_distance_change_before_next_plan_m=(chunk[-1]['goal_distance_m']-r['goal_distance_m'])if chunk else None)
sides=[r['causal_crossing_side']for r in plans if r['causal_crossing_side']is not None];gears=[r['first_gear']for r in plans if r['first_gear']is not None]
result={'status':'COMPLETED_ZERO_INTEGRATION','planning_attempts':len(plans),'global_goal_paths':sum(r['status']=='GLOBAL_GOAL_PATH'for r in plans),'reverse_first_plans':sum(g==-1 for g in gears),'first_gear_changes':sum(a!=b for a,b in zip(gears[:-1],gears[1:])),'crossing_side_changes':sum(a!=b for a,b in zip(sides[:-1],sides[1:])),'crossing_sides':{s:sides.count(s)for s in set(sides)},'plans_replaced_within_5_public_steps':sum(r['executed_public_until_next_plan']<=5 for r in plans),'planned_wall_s_total':sum(r['wall_s']for r in plans),'ordinary_actual_reverse_gear_steps':sum(r['status']=='MODEL_SAFE_COMMAND'and r['active_gear']==-1 for r in admissions),'retained_reverse_brake_steps':sum(r['status']=='RETAINED_REVERSE_BRAKE_CONTRACT'for r in admissions),'ordinary_positive_local_arc_but_goal_regression_steps':sum(r['status']=='MODEL_SAFE_COMMAND'and r['terminal_projected_arc_m']>r['current_projected_arc_m']and trace[i]['goal_distance_m']>(trace[i-1]['goal_distance_m']if i else 6.965)for i,r in enumerate(admissions)),'navigation_tasks':0,'simulation_integrations':0,'plans':plans}
(out/'PLAN_EXECUTION_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='plans'},indent=2))
