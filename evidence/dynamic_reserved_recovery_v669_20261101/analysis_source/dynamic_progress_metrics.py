"""Recorded development metrics; no simulator or controller import."""
import argparse,json,math
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('root');a=p.parse_args();root=Path(a.root)
def read(p):return json.loads(p.read_text())
records=[]
for run in sorted(root.iterdir()):
 cell=run/'paired/geometry_memory'
 if not(cell/'result.json').exists():continue
 result=read(cell/'result.json');trace=read(cell/'trace.json')
 admissions=[json.loads(s)for s in(cell/'model_admission.jsonl').read_text().splitlines()]
 motion=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()]
 protocol=read(run/'paired/STATIC_PROTOCOL.json');start=np.asarray(protocol['start_qpos'][:2])
 xy=np.vstack((start,np.asarray([r['pose'][:2]for r in trace])))
 goal=np.r_[np.linalg.norm(start-protocol['goal_xy']),[r['goal_distance_m']for r in trace]]
 safe=[r['candidate_count_safe']for r in admissions if 'candidate_count_safe'in r]
 error=np.asarray([np.asarray(r['pose'])-d['predicted_next_pose']for r,d in zip(trace,admissions)])
 if len(error):error[:,2]=(error[:,2]+np.pi)%(2*np.pi)-np.pi
 row={'run':run.name,'outcome':result['outcome'],'strict_arrival':result['strict_safe_arrival'],'public_steps':result['public_steps'],'native_steps':result['physics_steps'],
 'goal_distance_initial_m':float(goal[0]),'goal_distance_final_m':float(goal[-1]),'goal_distance_minimum_m':float(min(goal)),
 'travel_length_m':float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),'net_start_displacement_m':float(np.linalg.norm(xy[-1]-start)),
 'steps_goal_regression_over_1mm':int(np.sum(np.diff(goal)>.001)),'reverse_planned_steps':sum(r['active_gear']==-1 for r in trace),
 'planning_events':len(list(cell.glob('planning_*.json'))),'physical_braking_backup_steps':result['backup_steps'],
 'candidate_count_safe_quantiles':np.quantile(safe,[0,.1,.5,.9,1]).tolist()if safe else None,
 'maximum_sensor_age_s':max(r['age_s']for r in motion),'no_observation_decisions':sum(not r['observed_this_frame']for r in motion),
 'maximum_first_public_xy_yaw_error':np.max(abs(error),axis=0).tolist()if len(error)else None,
 'minimum_actual_native_clearance_m':result['minimum_dynamic_native_clearance_m'],'elapsed_navigation_wall_s':result['elapsed_s'],
 'wall_to_simulated_time_ratio':result['elapsed_s']/(result['physics_steps']*.01)if result['physics_steps']else None,
 'scope':'development, no independent confirmation; extra executed distance is not successful recovery'}
 records.append(row)
result={'simulation_steps':0,'records':records};(root/'PROGRESS_METRICS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
