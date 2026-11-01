"""Read persisted C0 tasks, count all integrations, produce a scientific figure."""
from pathlib import Path
import json,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v687_control_curriculum'
read=lambda p:json.loads(p.read_text())
assert read(root/'CONTINUATION_LEDGER.json')['round_closed']
records=[]
for file in sorted(root.glob('*/paired/geometry_memory/result.json')):
 pair=file.parents[1];r=read(file);audit=read(pair/'C0_AUDIT.json')if(pair/'C0_AUDIT.json').exists()else None;trace=read(file.parent/'trace.json');reference=read(pair/'C0_PROTOCOL.json')['reference'];distance=np.asarray([np.linalg.norm(np.asarray(read(pair/'STATIC_PROTOCOL.json')['start_qpos'])[:2]-read(pair/'STATIC_PROTOCOL.json')['goal_xy']),*[x['goal_distance_m']for x in trace]])
 records.append({'name':pair.parent.name,'course':r['course'],'repeat':'repeat'in pair.parent.name,'outcome':r['outcome'],'strict_safe_arrival':r['strict_safe_arrival'],'public_steps':r['public_steps'],'native_steps':r['physics_steps'],'private_prediction_integrations':r['prediction_steps'],'replay_native_steps':0 if audit is None else audit['replay_native_steps'],'goal_distance_m':r['goal_distance_m'],'minimum_native_clearance_m':r['minimum_native_clearance_m'],'backup_steps':r['backup_steps'],'net_goal_progress_m':float(distance[0]-distance[-1]),'minimum_goal_distance_m':float(distance.min()),'audit_status':None if audit is None else audit['status'],'maximum_full_state_replay_error':None if audit is None else max(audit['maximum_qpos_error'],audit['maximum_qvel_error']),'median_nearest_reference_distance_m':None if audit is None else audit['median_nearest_route_distance_m'],'maximum_nearest_reference_distance_m':None if audit is None else audit['maximum_nearest_route_distance_m'],'tail_audit_status':read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json')['status']if(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json').exists()else None,'run':str(pair.relative_to(repo))})
original=read(root/'ROUND_WINDOW.json');latest=read(root/'CONTINUATION_LEDGER.json')
out={'status':latest['status'],'records':records,'actual_course_navigation_runs':len(records),'distinct_preregistered_routes_executed':len({r['course']for r in records}),'repeat_runs':sum(x['repeat']for x in records),'new_navigation_native_steps':sum(x['native_steps']for x in records),'full_control_replay_native_steps':sum(x['replay_native_steps']for x in records),'private_prediction_integrations':sum(x['private_prediction_integrations']for x in records),'initial_directory_failure_native_steps':0,'initial_directory_failure_private_steps':0,'audit_import_failure_integration_steps':0,'original_absolute_deadline_unix':original['absolute_deadline_unix'],'actual_whole_round_elapsed_s':latest['started_unix']+latest['elapsed_s']-original['started_unix'],'training_updates':0,'dynamic_navigation_runs':0,'stage_access':0,'real_robot':0,'independent_confirmation_trials':0,'no_automatic_followup':True,'original_driver_failures_preserved':True,'causal_attribution_limit':'Fixed reference, observation0 and disabled mid-tail handover change multiple components; not single-variable actor-removal ablation.'}
(root/'FINAL_ANALYSIS.json').write_text(json.dumps(out,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(10,8));colors={'straight':'tab:blue','turn':'tab:orange','bypass':'tab:green'}
for ax,course in zip(axes.flat,['straight','turn','bypass']):
 rows=[x for x in records if x['course']==course and not x['repeat']]
 if not rows:ax.set_title(course+' (unexecuted)');continue
 row=rows[0];pair=repo/row['run'];reference=np.asarray(read(pair/'C0_PROTOCOL.json')['reference']);trace=read(pair/'geometry_memory/trace.json');xy=np.asarray([[-3,-2],*[x['pose'][:2]for x in trace]])
 ax.plot(reference[:,0],reference[:,1],'k--',label='Fixed reference');ax.plot(xy[:,0],xy[:,1],color=colors[course],label='Executed');goal=read(pair/'STATIC_PROTOCOL.json')['goal_xy'];ax.scatter(*goal,c='red',label='Goal');ax.set_aspect('equal',adjustable='datalim');ax.set_xlabel('x (m)');ax.set_ylabel('y (m)');ax.set_title(course+': '+row['outcome']);ax.legend(fontsize=8)
ax=axes.flat[3]
for row in records:
 if row['repeat']:continue
 trace=read(repo/row['run']/'geometry_memory/trace.json');ax.plot([(x['step']+1)*.08 for x in trace],[x['goal_distance_m']for x in trace],label=row['course'],color=colors[row['course']])
ax.axhline(.45,color='black',ls='--',label='Arrival threshold');ax.set_xlabel('Simulated time (s)');ax.set_ylabel('Goal distance (m)');ax.set_title('C0 actual goal progress');ax.legend(fontsize=8)
for ax in axes.flat:ax.grid(alpha=.2)
fig.tight_layout();dest=repo/'docs/figures';fig.savefig(dest/'control_curriculum_v687.png',dpi=180);fig.savefig(dest/'control_curriculum_v687.pdf');plt.close(fig)
print(json.dumps({k:v for k,v in out.items()if k!='records'},indent=2))
