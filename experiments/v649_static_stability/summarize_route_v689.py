"""Persisted training/arrival/participation accounting and scientific plots."""
from pathlib import Path
import json,hashlib
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v689_dynamic_route_commitment'
read=lambda p:json.loads(p.read_text());records=[]
ledger=read(root/'ROUND_WINDOW.json')if(root/'ROUND_WINDOW.json').exists()else read(root/'ROUND_WINDOW.json')
assert ledger['round_closed']
for f in sorted(root.glob('*/paired/geometry_memory/result.json')):
 pair=f.parents[1];r=read(f);aud=read(pair/'INDEPENDENT_CANONICAL_AUDIT.json')if(pair/'INDEPENDENT_CANONICAL_AUDIT.json').exists()else None;replay=read(pair/'NATIVE_REPLAY_AUDIT.json')if(pair/'NATIVE_REPLAY_AUDIT.json').exists()else None;learning=read(pair/'PROJECTION_LEARNING_AUDIT.json')if(pair/'PROJECTION_LEARNING_AUDIT.json').exists()else None
 records.append({'name':pair.parent.name,'run':str(pair.relative_to(repo)),'distance_m':r['course_distance_m'],'phase':r['course_phase'],'role':'TEACHER'if r['proposal_model_sha256']is None else'LEARNED','repeat':'repeat'in pair.parent.name,'outcome':r['outcome'],'strict_arrival':r['strict_safe_arrival'],'public_steps':r['public_steps'],'native_steps':r['physics_steps'],'private_prediction_integrations':r['prediction_steps'],'minimum_actual_clearance_m':r['minimum_dynamic_native_clearance_m'],'goal_distance_m':r['goal_distance_m'],'backup_steps':r['backup_steps'],'physical_command_audit':None if aud is None else aud['status'],'replay_steps':0 if replay is None else replay['replay_integration_steps'],'maximum_replay_full_state_error':None if replay is None else max(replay['maximum_full_public_qpos_error'],replay['maximum_full_public_qvel_error'],replay['maximum_public_mocap_error']),'projection_learning_audit':None if learning is None else learning['status'],'learned_actual_ordinary_steps':0 if learning is None else learning['learned_actual_ordinary_steps'],'ordinary_sample_count':0 if learning is None else learning['ordinary_teacher_sample_count'],'model_sha256':r['proposal_model_sha256']})
failed=[]
for row in read(root/'curriculum01/RESULTS.json'):
 if row['result']is None:
  pair=repo/row['run'];completion=read(pair/'completion.json');partial=read(pair/'geometry_memory/interrupted.json')
  failed.append({'name':row['name'],'distance_m':row['distance_m'],'phase':row['phase'],'run':row['run'],'status':completion['status'],'error':completion['error'],'public_steps':partial['public_steps'],'native_steps':partial['physics_steps'],'counts_as_non_success':True,'training_updates':0})
training=[read(f)for f in sorted(root.glob('training_*/TRAINING.json'))]
out={'status':ledger['status'],'records':records,'training':training,'supervised_gradient_updates':sum(x['gradient_updates']for x in training),'sac_gradient_updates':0,'attempted_navigation_tasks':ledger['navigation_attempts'],'failed_or_unexecuted_attempts':failed,'actual_navigation_runs':len(records),'new_navigation_native_steps':sum(x['native_steps']for x in records),'failed_attempt_native_steps':sum(x['native_steps']for x in failed),'full_replay_native_steps':sum(x['replay_steps']for x in records),'private_prediction_integrations':sum(x['private_prediction_integrations']for x in records),'six_meter_gate_passed':ledger['six_meter_gate_passed'],'eight_meter_started':ledger['eight_meter_started'],'actual_whole_round_elapsed_s':ledger['elapsed_s'],'original_absolute_deadline_unix':read(root/'ROUND_WINDOW.json')['absolute_deadline_unix'],'independent_confirmation':0,'stage_access':0,'real_robot':0,'original_v688_failures_preserved':True,'raw_deleted':False,'scope':'finite causal route-commitment course with frozen6mlearner; not original field dynamic acceptance'}
(root/'FINAL_ANALYSIS.json').write_text(json.dumps(out,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,3,figsize=(14,4));colors=plt.get_cmap('tab10')
for i,row in enumerate(records):
 if row['repeat']:continue
 pair=repo/row['run'];trace=read(pair/'geometry_memory/trace.json');xy=np.asarray([[-row['distance_m']/2,-2],*[t['pose'][:2]for t in trace]])
 label=row['name'];axes[0].plot(xy[:,0],xy[:,1],c=colors(i),label=label);axes[1].plot([(x['step']+1)*.08 for x in trace],[x['goal_distance_m']for x in trace],c=colors(i),label=label)
axes[0].plot([-1,-1],[-2.25,-1.75],c='red',lw=8,alpha=.3,label='Actor center sweep');axes[0].set_aspect('equal',adjustable='datalim');axes[0].set_xlabel('x (m)');axes[0].set_ylabel('y (m)');axes[0].set_title('Executed trajectories');axes[0].legend(fontsize=6)
axes[1].axhline(.45,c='black',ls='--');axes[1].set_xlabel('Simulated time (s)');axes[1].set_ylabel('Goal distance (m)');axes[1].set_title('Arrival and non-arrival kept');axes[1].legend(fontsize=6)
labels=[x['name']for x in records];ordinary=[x['ordinary_sample_count']for x in records];chosen=[x['learned_actual_ordinary_steps']for x in records];xx=np.arange(len(records));axes[2].bar(xx,ordinary,color='lightgray',label='Ordinary executed');axes[2].bar(xx,chosen,color='tab:green',label='Learned target chosen');axes[2].set_xticks(xx,labels,rotation=50,ha='right',fontsize=6);axes[2].set_ylabel('Executed public steps');axes[2].set_title('Actual learned participation');axes[2].legend(fontsize=7)
for ax in axes:ax.grid(alpha=.2)
fig.tight_layout();dest=repo/'docs/figures';fig.savefig(dest/'dynamic_route_commitment_v689.png',dpi=180);fig.savefig(dest/'dynamic_route_commitment_v689.pdf');plt.close(fig)
print(json.dumps({k:v for k,v in out.items()if k not in ['records','training']},indent=2))
