"""Attribute the completed global failure using only saved arrays and raw journals."""
import json,gzip,sys,collections,hashlib
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];src=repo/'experiments/v778_global_retained_reentry';sys.path.insert(0,str(src))
from exact_footprint import pose_values
from unseen_prior import clearance as unseen_clearance
pair=repo/'runs/v778_global_retained_reentry/v780_main01/paired';cell=pair/'geometry_memory';out=repo/'runs/v783_global_failure_attribution';out.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
protocol=read(pair/'STATIC_PROTOCOL.json');b=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
from unseen_prior import set_public_origin
set_public_origin(protocol['start_qpos'][:2]);rows=lines(cell/'v648_execution.jsonl');states={x['step']:x for x in lines(cell/'motion_estimate.jsonl')};goaldistance=np.array([np.linalg.norm(np.asarray(x['qpos_full'])[:2]-protocol['goal_xy'])for x in rows]);initial=float(np.linalg.norm(np.asarray(protocol['start_qpos'])[:2]-protocol['goal_xy']));details=[]
for f in sorted((cell/'retained_reentry').glob('step????.json')):
 x=read(f);counts=collections.Counter();forward=[];candidates=[]
 for c in x['records']:
  z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));p=z['poses'];static=pose_values(field,p);unknown=unseen_clearance(field,p,states[x['step']],np.arange(1,329)*.01);minimum=np.minimum(static,unknown);err=abs(float(minimum.min())-c['minimum_causal_clearance_m']);assert err<=1e-8
  counts['static_rejected']+=int(static.min()<.155);counts['unknown_future_rejected']+=int(unknown.min()<.155);counts['original_all_gates_passed']+=int(c['reason']is None)
  if c['reason']is None and np.mean(c['target'][2:])>=1:forward.append(c)
  candidates.append(dict(index=c['index'],target=c['target'],static_minimum_m=float(static.min()),unknown_future_minimum_m=float(unknown.min()),minimum_tick=int(np.argmin(minimum))+1,first_rejected_tick=int(np.flatnonzero(minimum<.155)[0])+1 if np.any(minimum<.155)else None,goal_progress_m=c['goal_progress_m'],reason=c['reason']))
 details.append(dict(step=x['step'],old_created_step=x['old_created_step'],old_cursor=x['old_native_cursor'],counts=dict(counts),safe_positive_mean_count=len(forward),best_safe_positive_mean_progress_m=max((c['goal_progress_m']for c in forward),default=None),selected=x['selected_index'],candidates=candidates))
plans=[read(p)for p in sorted(cell.glob('planning_*.json'))];ad=lines(cell/'model_admission.jsonl');result=read(cell/'result.json')
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
reliable_counts=[]
for p in packets:
 n=0
 for name in ['lidar','depth']:
  z=np.asarray(p[name])*p[name+'_max_range'];n+=int(np.sum((z>.05)&(z<p[name+'_max_range']-1e-5)))
 reliable_counts.append(n)
summary=dict(status='GLOBAL_SAVED_FAILURE_ATTRIBUTION_COMPLETE',global_task_passed=False,original_task_seed=10010001,main_functional_successes=0,main_functional_trials=1,new_confirmation_denominator_unexecuted=24,old_closed_results_preserved=True,public_steps=len(rows),native_steps=result['physics_steps'],private_native=result['prediction_steps'],full_native_replay=read(pair/'NATIVE_REPLAY_AUDIT.json'),maximum_goal_distance_reduction_m=initial-float(goaldistance.min()),maximum_goal_progress_at_step=int(goaldistance.argmin()),final_goal_distance_reduction_m=initial-float(goaldistance[-1]),progress_lost_after_best_m=float(goaldistance[-1]-goaldistance.min()),maximum_displacement_from_start_m=float(max(np.linalg.norm(np.asarray(x['qpos_full'])[:2]-np.asarray(protocol['start_qpos'])[:2])for x in rows)),global_plans=[dict(step=x['step'],status=x['stats']['status'],points=0 if x['path']is None else len(x['path']))for x in plans],all_global_plans_found=bool(plans)and all(x['path']is not None for x in plans),reentry_attempts=len(details),reentry_selected=sum(x['selected']is not None for x in details),reentry_safe_counts=[dict(step=x['step'],**x['counts'],best_safe_positive_mean_progress_m=x['best_safe_positive_mean_progress_m'])for x in details],raw_packets=len(packets),last_packet_submaximum_rays=reliable_counts[-1],last8_submaximum_rays=reliable_counts[-8:],first_discovery=result['first_discovery_step'],original_reference_handover_successes=result['certified_handover_successes'],last_reentry_step=details[-1]['step'],last_static_rejections=details[-1]['counts']['static_rejected'],last_unknown_future_rejections=details[-1]['counts']['unknown_future_rejected'],last_candidates=details[-1]['candidates'],new_models=0,new_integrations=0,new_predictions=0)
(out/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');(out/'ALL_DECISIONS.json').write_text(json.dumps(details,indent=2)+'\n')
# Standard publication-style plot of the actual saved global path and progress.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
fig,(ax,px)=plt.subplots(1,2,figsize=(12,5),layout='constrained')
for cx,cy,hx,hy in protocol['known_rectangles']:ax.add_patch(Rectangle((cx-hx,cy-hy),2*hx,2*hy,color='#b7bdc6'))
for cx,cy,rad in protocol['known_circles']:ax.add_patch(Circle((cx,cy),rad,color='#b7bdc6'))
xy=np.array([x['qpos_full'][:2]for x in rows]);ax.plot(xy[:,0],xy[:,1],color='#155ba0',lw=2,label='Actual global navigation');ax.scatter(*protocol['start_qpos'][:2],c='#24853a',marker='o',label='Start');ax.scatter(*protocol['goal_xy'],c='#b52e30',marker='*',s=100,label='Goal')
c=read(pair/'DYNAMIC_PROTOCOL.json');anchor=np.asarray(c['anchor_xy']);axis=np.asarray(c['axis_xy']);ends=np.stack([anchor-.25*axis,anchor+.25*axis]);ax.plot(ends[:,0],ends[:,1],c='#c68b00',lw=7,alpha=.5,label='Actor swept center (evaluation only)');ax.set(xlim=(-5,5),ylim=(-5,5),xlabel='x (m)',ylabel='y (m)',title='Original 19-obstacle field; no arrival');ax.set_aspect('equal');ax.legend(fontsize=8)
px.plot(np.arange(len(rows)),initial-goaldistance,c='#155ba0',lw=2,label='Actual reduction of distance to goal')
for x in details:px.axvline(x['step'],color='#d18827',alpha=.35,lw=.7)
px.scatter([goaldistance.argmin()],[initial-goaldistance.min()],color='#24853a',zorder=3,label='Best actual progress');px.set(xlabel='Public control step',ylabel='Reduction of goal distance (m)',title='Retreat erases the initial progress');px.grid(alpha=.25);px.legend(fontsize=8)
figure=repo/'docs/figures/RPCCR_GLOBAL_REENTRY_V778_V780';figure.parent.mkdir(exist_ok=True);fig.savefig(str(figure)+'.png',dpi=180);fig.savefig(str(figure)+'.pdf');plt.close(fig)
print(json.dumps({k:summary[k]for k in ['status','maximum_goal_distance_reduction_m','final_goal_distance_reduction_m','progress_lost_after_best_m','reentry_attempts','reentry_selected','last_static_rejections','last_unknown_future_rejections','last_packet_submaximum_rays']},indent=2))
