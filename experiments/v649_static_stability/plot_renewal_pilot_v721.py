"""Scientific persisted-evidence figure; no simulator or new navigation."""
import json,os
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];out=repo/'runs/v722_renewal_navigation_diagnosis/figures';out.mkdir(exist_ok=True);os.environ['MPLCONFIGDIR']=str(out/'mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
read=lambda p:json.loads(p.read_text())
known=read(repo/'experiments/v721_recursive_unseen_navigation/KNOWN_FIELD.json');diagnosis=read(repo/'runs/v722_renewal_navigation_diagnosis/DIAGNOSIS.json')
fig,axes=plt.subplots(1,3,figsize=(15,4.8),constrained_layout=True)
ax=axes[0]
for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='.6'))
for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,color='.6'))
for label,name,color in [('V712 fixed initial disk','v712_joint_field_continuation','darkorange'),('V721 causal renewal','v721_recursive_unseen_navigation','teal')]:
 pair=repo/'runs'/name/'main01/paired';rows=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];p=read(pair/'STATIC_PROTOCOL.json');xy=np.array([p['start_qpos'][:2],*[r['qpos_full'][:2]for r in rows]]);goal=np.array(p['goal_xy']);time=np.r_[0.,[r['time']for r in rows]]
 ax.plot(*xy.T,lw=2,color=color,label=label);ax.scatter(*xy[-1],marker='x',color=color,s=55)
 axes[1].plot(time,8.-np.linalg.norm(xy-goal,axis=1),color=color,label=label)
ax.scatter([-4,4],[-2,-2],c=['royalblue','crimson'],marker='*',s=85);ax.add_patch(Circle((3,-1),.35,color='red',alpha=.2));ax.set(xlim=(-5,5),ylim=(-5,5),xlabel='x (m)',ylabel='y (m)',title='Actual executed trajectories\nActor remains far ahead');ax.set_aspect('equal');ax.legend(fontsize=8)
axes[1].set(xlabel='Simulation time (s)',ylabel='Goal progress (m)',title='More progress, neither run arrived');axes[1].grid(alpha=.2);axes[1].axhline(0,color='.5',lw=.5)
cp=diagnosis['checkpoints'];times=[x['time']for x in cp]
axes[2].plot(times,[x['renewed_current_stationary_actor_clearance_lower_bound_m']for x in cp],'o-',label='Current stationary pose')
axes[2].plot(times,[x['renewed_stationary_328_end_clearance_lower_bound_m']for x in cp],'s-',label='Same pose after 3.28 s')
axes[2].axhline(.155,color='crimson',ls='--',label='Admission floor 0.155 m');axes[2].set(xlabel='V721 simulation time (s)',ylabel='Conservative actor clearance (m)',title='Saved-checkpoint certificate limits\nMarkers are fixed-pose witnesses');axes[2].grid(alpha=.2);axes[2].legend(fontsize=8)
fig.suptitle('RP-CCR pre-detection temporal renewal: one development task, non-arrival preserved',fontsize=13)
for suffix in ['png','pdf']:fig.savefig(out/('rpccr_renewal_v721.'+suffix),dpi=180)
print(out/'rpccr_renewal_v721.png')
