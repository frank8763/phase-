"""Saved-only interpretation and trajectory figure; no model loading or stepping."""
import gzip,json,os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
root=repo/'runs/v797_retained_tail_mpc';read=lambda p:json.loads(p.read_text())
assert(repo/'REVIEW_PENDING').exists()and read(root/'ROUND_WINDOW.json')['round_closed']
assert not(root/'SAVED_DIAGNOSIS.json').exists()
result=read(root/'RESULT.json');audit=read(root/'SAVED_AUDIT.json')
assert audit['status']=='ALL_RETAINED_MPC_SAVED_EVIDENCE_VERIFIED'
protocol=read(repo/'runs/v793_complete_joint_navigation/main_slot01/paired/STATIC_PROTOCOL.json')
reference=np.asarray(read(own/'REFERENCE_PATH.json')['path'])
old=[json.loads(s)for s in(repo/'runs/v793_complete_joint_navigation/main_slot01/paired/geometry_memory/v648_execution.jsonl').read_text().splitlines()]
actual=[];contexts={}
with gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','rt')as f:
    for line in f:
        row=json.loads(line)
        if row['context']=='ORIGINAL_REPLAY'or row['context'].endswith('_REPEAT'):continue
        actual.append(row);contexts.setdefault(row['context'],[]).append(row)
steps=[]
for r in result['records']:
    label=f"S200_R{r['refresh']:02d}";cs=read(root/(label+'_CANDIDATES.json'))
    steps.append(dict(refresh=r['refresh'],candidates=len(cs),safe=sum(x['safety_admissible']for x in cs),
        route_admissible=sum(x['admissible']for x in cs),
        future_clearance_rejections=sum(x['clearance_m']<.155 for x in cs),
        static_clearance_rejections=sum(x['static_minimum_m']<.155 for x in cs),
        self_rejections=sum(x['self_margin_m']<.002 for x in cs),
        linear_speed_rejections=sum(x['terminal_speed_m_s']>.025 for x in cs),
        angular_speed_rejections=sum(x['terminal_angular_rad_s']>.025 for x in cs),
        best_causal_minimum_m=max(x['clearance_m']for x in cs),
        selected=r['selected'],actual_executed=r['actual_executed']))
diagnosis=dict(status='CLOSED_CORRIDOR_SAVED_DIAGNOSIS_COMPLETE',steps=steps,
    stopped_reason=result['stopped_reason'],first_discovery=result['first_discovery'],
    central_root_center_crossed=result['central_root_center_crossed'],component_qualified=result['component_qualified'],
    best_absolute_goal_progress_m=result['maximum_absolute_goal_progress_m'],
    old_best_absolute_goal_progress_m=result['old_best_absolute_progress_m'],
    reference_arc_progress_m=result['reference_arc_progress_m'],
    actual_public=len(actual)//8,actual_native=len(actual),full_global_dynamic_passed=False,
    new_models=0,new_integrations=0,not_a_new_independent_navigation_sample=True)
if actual:
    q=np.asarray([x['qpos']for x in actual]);v=np.asarray([x['qvel']for x in actual]);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
    delta=np.diff(np.vstack([np.asarray(old[199]['qpos_full'])[:2],q[:,:2]]),axis=0)
    signed=np.sum(delta*np.c_[np.cos(yaw),np.sin(yaw)],axis=1)
    diagnosis.update(actual_path_length_m=float(np.linalg.norm(delta,axis=1).sum()),
        reverse_projection_m=float(np.maximum(-signed,0).sum()),actual_end_xy=q[-1,:2].tolist(),
        final_absolute_goal_progress_m=float(8.-np.linalg.norm(q[-1,:2]-protocol['goal_xy'])),
        terminal_speed_m_s=float(np.linalg.norm(v[-1,:2])),terminal_angular_rad_s=float(np.linalg.norm(v[-1,3:6])))
    # Whole rectangle beyond the divider plane, a separate stronger event.
    left=q[:,0]-(.44*abs(np.cos(yaw))+.375*abs(np.sin(yaw)))
    diagnosis['whole_declared_rectangle_beyond_central_wall_right_face']=bool(np.any(left>.08))
else:q=np.empty((0,20))
(root/'SAVED_DIAGNOSIS.json').write_text(json.dumps(diagnosis,indent=2)+'\n')
fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained')
old_xy=np.asarray([x['qpos_full'][:2]for x in old])
for ax in axes:
    for x,y,hx,hy in protocol['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,fc='#acb7c3',ec='#637387',lw=.7))
    for x,y,r in protocol['known_circles']:ax.add_patch(Circle((x,y),r,fc='#acb7c3',ec='#637387',lw=.7))
    ax.plot(reference[:,0],reference[:,1],color='#22a26a',ls='--',lw=2,label='Causal global reference (step 153)')
    ax.plot(old_xy[:,0],old_xy[:,1],color='#9a9a9a',lw=1.3,alpha=.8,label='V793 old failed trajectory')
    if len(q):ax.plot(q[:,0],q[:,1],color='#1671c4',lw=2,label='V797 actual retained-tail MPC from old step 200');ax.scatter(*q[-1,:2],s=45,c='#1671c4',marker='s')
    ax.scatter(*old_xy[199],marker='o',s=45,c='#5e3c99',zorder=5,label='Old checkpoint 200')
    ax.axvline(0,color='#d34b32',ls=':',lw=1,label='Central x=0')
    ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_xlabel('x [m]');ax.set_ylabel('y [m]')
axes[0].set(xlim=(-5,5),ylim=(-5,5),title='Same field; actual saved states only')
axes[1].set(xlim=(-2.6,1.7),ylim=(-2.5,.35),title='Central approach: proposal versus execution')
axes[0].legend(fontsize=7,loc='upper left')
fig.suptitle('V797 retained-tail MPC — finite old-state development',fontsize=12)
fig.savefig(root/'actual_retained_mpc.png',dpi=150);plt.close(fig)
print(json.dumps(diagnosis))
