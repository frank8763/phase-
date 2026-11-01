"""Research plot from persisted negative results; no robot imports or integration."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v671_dynamic_consistency_diagnosis';read=lambda p:json.loads(p.read_text());fig,ax=plt.subplots(1,3,figsize=(14,4),layout='constrained')
for label,folder,name in [('V670: unhit cells','v670_dynamic_empty_samples','dev38_95000011_empty'),('V672: brake-first','v672_dynamic_minimal_backup','dev39_95000011_minimal'),('V673: joint p-v cover','v673_dynamic_joint_forecast','dev40_95000011_joint')]:
 t=read(repo/'runs'/folder/name/'paired/geometry_memory/trace.json');ax[0].plot([r['step']for r in t],[r['goal_distance_m']for r in t],label=label)
ax[0].axhline(.45,color='black',ls='--',lw=1,label='Arrival threshold');ax[0].set(title='Repeated retreat; no branch arrived',xlabel='Public steps',ylabel='Goal distance (m)');ax[0].legend(fontsize=8)
r=read(repo/'runs/v673_dynamic_joint_forecast/dev40_95000011_joint/paired/geometry_memory/rejected_control.json');ax[1].bar([0,1],[r['current_clearance_m'],r['gate']['best_rejected_min_clearance_m']],color=['#3b7a87','#d9843b']);ax[1].axhline(.155,color='black',ls='--',lw=1,label='Admission floor');ax[1].set(xticks=[0,1],xticklabels=['Current estimate','Best rejected\nfuture trajectory'],ylabel='Clearance (m)',title='Current safety does not imply a continuation');ax[1].legend(fontsize=8)
lp=read(root/'TEMPORAL_LP_INFORMATION_DIAGNOSIS.json')['records'];x=np.arange(4);w=.18
for offset,k,label,color in [(-1.5,'velocity_width_old_m_s','Original x','#3878a8'),(-.5,'velocity_width_lp_m_s','Temporal LP x','#8bb4d2'),(.5,'velocity_width_old_m_s','Original y','#bf7035'),(1.5,'velocity_width_lp_m_s','Temporal LP y','#edb385')]:
 d=0 if label.endswith('x')else 1;ax[2].bar(x+offset*w,[r[k][d]for r in lp],w,label=label,color=color)
ax[2].set(xticks=x,xticklabels=[r['checkpoint']for r in lp],xlabel='Locked V670 checkpoints',ylabel='Velocity interval width (m/s)',title='Linear history constraints:\nlimited extra information');ax[2].legend(fontsize=8)
for a in ax:a.grid(alpha=.2,axis='y')
fig.suptitle('V671–V673: diagnosis, mechanism tests, and remaining feasibility gap',fontsize=12)
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for suffix in ['png','pdf']:fig.savefig(out/f'dynamic_diagnosis_v671.{suffix}',dpi=180)
print(out/'dynamic_diagnosis_v671.png')
