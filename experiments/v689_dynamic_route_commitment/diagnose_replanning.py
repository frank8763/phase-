"""Locked saved six-meter route revalidation trigger diagnosis, zero integration."""
import os,sys,json,hashlib,importlib.util
from pathlib import Path
import numpy as np
repo=Path(os.environ['PHASE_REPO']);base=repo/'experiments/v688_dynamic_distance_curriculum';sys.path.insert(0,str(base));sys.path.insert(1,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from motion_tracker import install_time_gate
from future_guide import route_world
from tracking import switch_if_settled
from planner import wrap
spec=importlib.util.spec_from_file_location('v689_readonly_geometry',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F;spec.loader.exec_module(F)
out=repo/'runs/v689_dynamic_route_commitment';out.mkdir(exist_ok=True)
records=[];sources={}
for name in ['teacher6m','learned6m_train_task']:
 cell=repo/'runs/v688_dynamic_distance_curriculum'/name/'paired/geometry_memory';trace=json.loads((cell/'trace.json').read_text());execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];states={x['step']:x for x in [json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()]};plans=[json.loads(p.read_text())for p in sorted(cell.glob('planning_*.json'))]
 for previous,new in zip(plans,plans[1:]):
  step=new['step'];current=np.asarray(new['pose']);path=np.asarray(previous['path']);index=trace[step-1]['path_index'];gear=int(path[min(index+1,len(path)-1),3]);end=index+1
  while end<len(path)-1 and int(path[end+1,3])==gear:end+=1
  distances=np.linalg.norm(path[index:min(end+1,index+40),:2]-current[:2],axis=1);nearest=index+int(np.argmin(distances));index=min(nearest,end-1)if end<len(path)-1 else nearest
  index,transition=switch_if_settled(path,index,current,np.asarray(execution[step-1]['qvel_full']))
  world=new['causal_input'];state=states[step];route_input,_=route_world(world,state);spatial=build(F,route_input);causal=build(F,world);install_time_gate(causal,state,'predictive',[],[])
  segment=path[index:min(len(path),index+26),:3];projected_min=float(np.min(spatial.pose_values(segment)));current_min=float(np.min(causal.pose_values(segment)));heading=float(abs(wrap(current[2]-path[index,2])));dwell=step-previous['step'];deviation=bool(dwell>=12 and(float(np.min(distances))>.2 or heading>.5));stagnation=False
  if dwell>=30 and step>=30:
   past=np.asarray(trace[step-30]['pose']);stagnation=bool(np.linalg.norm(current[:2]-past[:2])<.04 and abs(wrap(current[2]-past[2]))<.06)
  reasons=[]
  if projected_min<.155-1e-6:reasons.append('FUTURE_PROJECTION_ROUTE_REVALIDATION')
  if index>=len(path)-4:reasons.append('ROUTE_NEAR_END')
  if deviation:reasons.append('TRACKING_DEVIATION')
  if stagnation:reasons.append('STAGNATION')
  records.append({'run':name,'step':step,'previous_plan_step':previous['step'],'index':index,'projected_route_minimum_m':projected_min,'current_joint_route_minimum_m':current_min,'heading_error_rad':heading,'nearest_segment_distance_m':float(np.min(distances)),'dwell_steps':dwell,'stopped_cusp_transition':transition,'reconstructed_reasons':reasons,'projection_only_and_current_safe':reasons==['FUTURE_PROJECTION_ROUTE_REVALIDATION']and current_min>=.155-1e-6})
 for p in [cell/'trace.json',cell/'v648_execution.jsonl',cell/'motion_estimate.jsonl',*cell.glob('planning_*.json')]:sources[str(p.relative_to(repo))]=hashlib.sha256(p.read_bytes()).hexdigest()
result={'status':'ZERO_INTEGRATION_TRIGGER_DIAGNOSIS','records':records,'sole_projected_replans_with_current_safe':sum(x['projection_only_and_current_safe']for x in records),'total_replanning_events':len(records),'source_sha256':sources,'robot_integrations':0,'training_updates':0,'scope':'reconstructs old route check before replanning; not a proof a cached route is dynamically executable'}
(out/'REPLAN_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_sha256'},indent=2))
