import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
from pathlib import Path
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());out=repo/'runs/v774_map_conditioned_failure_analysis';proto=read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json');goal=np.asarray(proto['goal_xy']);base=np.load(repo/'runs/v772_map_conditioned_progress/ORIGINAL_256_NATIVE_REPLAY.npz')['qpos'][-1];records=read(out/'CANDIDATES.json');hist=read(out/'RAY_HISTORIES.json');fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for folder,name,label,color in [('v767_certified_progress_release','FEEDBACK','Previous certified release','#999999'),('v772_map_conditioned_progress','MAP_HISTORY','Known map: past set (B)','#3377aa'),('v772_map_conditioned_progress','MAP_FUTURE','Known map: past + future (max B,C)','#aa3355')]:
 raw=repo/'runs'/folder;b=read(raw/(name+'_MAIN_SUMMARY.json'));z=np.load(raw/(name+'_MAIN_ACTUAL.npz'));q=z['qpos'];t=np.arange(1,len(q)+1)*.01;progress=np.linalg.norm(base[:2]-goal)-np.linalg.norm(q[:,:2]-goal,axis=1);k=b['scheduled_public_completed']*8;ax[0,0].plot(t[:k],progress[:k],color=color,label=label);ax[0,0].plot(t[k-1:],progress[k-1:],ls='--',color=color)
 ax[0,1].plot(q[:k,0],q[:k,1],color=color,label=label);ax[0,1].plot(q[k-1:,0],q[k-1:,1],color=color,ls='--');ax[0,1].scatter(q[k-1,0],q[k-1,1],s=25,color=color)
 if name!='FEEDBACK':
  d=b['decisions'];ax[1,0].step([x['local_public']*.08 for x in d],[len(x['ranking'])for x in d],where='post',label=label,color=color)
  rc=[x for x in records if x['profile']==name];ax[1,1].plot([x['action_index']for x in rc],[x['unknown_min_m']for x in rc],marker='o',ms=3,label=label,color=color)
for x,y,hx,hy in proto['known_rectangles']:ax[0,1].add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#cccccc',alpha=.5))
for x,y,rad in proto['known_circles']:ax[0,1].add_patch(Circle((x,y),rad,color='#bbbbbb',alpha=.5))
for h in hist:ax[0,1].scatter(*h['witness_center'],marker='x',s=55,color='#222222')
ax[0,1].scatter(*base[:2],marker='s',color='#222222',s=25);ax[0,1].set(xlim=(-4.5,-1.8),ylim=(-3.7,-1.2),aspect='equal',title='Same checkpoint trajectories; x = possible-center witness',xlabel='World x (m)',ylabel='World y (m)')
ax[0,0].set(title='Actual goal progress (dashed = final retained tail)',xlabel='Elapsed simulated time (s)',ylabel='Net goal progress (m)');ax[0,0].legend(fontsize=8)
ax[1,0].set(title='Certified actions from the fixed 15',xlabel='Elapsed simulated time (s)',ylabel='Admissible actions',ylim=(-.5,16))
ax[1,1].axhline(.155,color='#444444',ls='--',label='Unchanged admission floor .155 m');ax[1,1].set(title='Final rejected actions: unknown future clearance',xlabel='Registered action index',ylabel='Minimum lower bound (m)');ax[1,1].legend(fontsize=8)
for a in ax.flat:a.grid(alpha=.2)
fig.suptitle('V772: known-map reachability qualifies offline; sustained physical progress NOT PASSED',fontsize=13)
for ext in ['png','pdf']:fig.savefig(out/('map_conditioned_progress.'+ext),dpi=180)
