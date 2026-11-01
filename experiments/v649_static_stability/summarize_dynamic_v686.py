"""Post-closure persisted-evidence accounting and a standalone scientific figure."""
import json,gzip,hashlib
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v686_dynamic_open_curriculum';pair=root/'open01/paired';cell=pair/'geometry_memory'
read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
assert read(root/'ROUND_WINDOW.json')['round_closed']
actual_runs=[p.parent.parent for p in root.glob('*/paired/geometry_memory/result.json')]
result=read(cell/'result.json');trace=read(cell/'trace.json');states=lines(cell/'motion_estimate.jsonl');decisions=lines(cell/'control_decisions.jsonl');ad=lines(cell/'model_admission.jsonl');layer=read(pair/'LAYER_METRICS_V2.json')
goals=np.asarray([4.,*[t['goal_distance_m']for t in trace]]);delta=goals[:-1]-goals[1:]
tracking=[];plans={int(p.stem.split('_')[-1]):read(p)for p in cell.glob('planning_*.json')};current=None
for t in trace:
 if t['step']in plans:current=plans[t['step']]
 if current and current['path'] is not None:tracking.append(float(np.linalg.norm(np.asarray(current['path'])[:,:2]-t['pose'][:2],axis=1).min()))
reverse=[x['step']for x in ad if x.get('active_gear')==-1];forward=[x['step']for x in ad if x.get('active_gear')==1 and not x.get('observation_initialization')]
final_reject=read(cell/'rejected_control.json')if(cell/'rejected_control.json').exists()else None
account={'status':read(root/'development01/COMPLETION.json')['status'],'new_task':'OPEN_SINGLE_CROSSING_01','new_navigation_native_steps':sum(read(p/'geometry_memory/result.json')['physics_steps']for p in actual_runs),'full_navigation_replay_native_steps':sum(read(p/'NATIVE_REPLAY_AUDIT.json')['replay_integration_steps']for p in actual_runs),'navigation_private_prediction_integrations':sum(read(p/'geometry_memory/result.json')['prediction_steps']for p in actual_runs),'preflight_robot_integrations':0,'geometry_tasks':1,'independent_confirmation':0,'training_updates':0,'stage_access':0,'real_robot':0,'original_result':result,'layer_metrics':layer,'minimum_goal_distance_m':float(goals.min()),'net_goal_progress_m':float(4-goals[-1]),'reverse_public_steps':len(reverse),'reverse_net_goal_progress_m':float(delta[reverse].sum()),'forward_nonobservation_public_steps':len(forward),'forward_net_goal_progress_m':float(delta[forward].sum()),'median_spatial_tracking_error_m':float(np.median(tracking))if tracking else None,'maximum_spatial_tracking_error_m':max(tracking,default=None),'last_rejected_control':final_reject,'no_unknown_dynamic_stability_claim':True,'raw_deleted':False}
for key,test in [('observation',lambda x:bool(x.get('observation_initialization'))),('retained_backup',lambda x:x['status']=='RETAINED_REVERSE_BRAKE_CONTRACT')]:
 ids=[x['step']for x in ad if test(x)];account[key+'_public_steps']=len(ids);account[key+'_net_goal_progress_m']=sum(float(goals[i]-goals[i+1])for i in ids)
account.update(status='CLOSED_OPEN_ARENA_NON_ARRIVAL_WITH_ORIGINAL_AUDITOR_FAILURE',original_driver_status='STOPPED_EXCEPTION',independent_physical_command_audit_v2='PASS',saved_tail_geometry_audit='PASS',declared_arena_vehicle_audit='PASS',normal_frozen_repeat_not_executed=True,layer_metric_v1_conservative_marginal_retained=True)
(root/'FINAL_ANALYSIS.json').write_text(json.dumps(account,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,3,figsize=(13,4));ax=axes[0];prior=np.asarray(read(pair/'KNOWN_PRIOR_REFERENCE.json')['path']);ax.plot(prior[:,0],prior[:,1],'k--',label='Known prior route')
if plans:
 p=np.asarray(plans[min(plans)]['path']);ax.plot(p[:,0],p[:,1],color='tab:blue',alpha=.65,label='First causal detour')
xy=np.asarray([[-3.,-2.],*[t['pose'][:2]for t in trace]]);ax.plot(xy[:,0],xy[:,1],color='tab:green',label='Executed vehicle')
ax.plot([-1,-1],[-2.25,-1.75],color='tab:red',lw=9,alpha=.35,label='Actor center sweep')
ax.scatter([-3,1],[-2,-2],c=['black','purple']);ax.set_aspect('equal');ax.set_xlabel('x (m)');ax.set_ylabel('y (m)');ax.legend(fontsize=7);ax.set_title('Open-arena layer test')
axes[1].plot(np.arange(len(goals))*.08,goals);axes[1].axhline(.45,color='k',ls='--');axes[1].set_xlabel('Simulated time (s)');axes[1].set_ylabel('Goal distance (m)');axes[1].set_title('Actual goal progress')
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
axes[2].plot([x['time']for x in native],[x['actual_clearance_m']for x in native]);axes[2].axhline(.15,color='red',ls='--',label='0.15 m floor');axes[2].set_xlabel('Simulated time (s)');axes[2].set_ylabel('Actual native clearance (m)');axes[2].legend(fontsize=8);axes[2].set_title('Safety prefix, separate from arrival')
for ax in axes:ax.grid(alpha=.2)
fig.tight_layout();dest=repo/'docs/figures';dest.mkdir(exist_ok=True);fig.savefig(dest/'dynamic_curriculum_v686.png',dpi=180);fig.savefig(dest/'dynamic_curriculum_v686.pdf');plt.close(fig)
print(json.dumps({k:v for k,v in account.items()if k not in ['original_result','layer_metrics','last_rejected_control']},indent=2))
