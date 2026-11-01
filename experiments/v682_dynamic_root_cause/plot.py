"""Export a recorded-data diagnosis figure; no integration."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());root=repo/'runs/v682_dynamic_root_cause';a=read(root/'ANALYSIS.json');b=read(root/'EXACT_STATE_ABLATION.json');fig,ax=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
current=np.median([r['position_width_m']for r in a['records']],axis=0);future=np.median([r['future_union_bounding_box_width_m'][-1]for r in a['records']],axis=0);x=np.arange(2)
ax[0].bar(x-.18,current,width=.35,label='Current center uncertainty',color='#5388a5');ax[0].bar(x+.18,future,width=.35,label='At 3.28 s',color='#cb8c48');ax[0].set(xticks=x,xticklabels=['x','y'],ylabel='Center-set bounding-box width (m)',title='Future uncertainty grows despite frequent returns');ax[0].legend(fontsize=7);ax[0].text(.5,.55,'Actual actor diameter: 0.20 m\n(uncertainty width excludes its radius)',ha='center',fontsize=8)
v=[r['net_goal_progress_m']for r in a['goal_progress_partition']];ax[1].bar(['Ordinary\nforward','Ordinary\nreverse','Retained\nbackup'],v,color=['#5b9771','#d08c48','#8b7b9e']);ax[1].axhline(0,color='black',lw=.7);ax[1].set(ylabel='Net reduction in goal distance (m)',title='Ordinary reverse discards most forward gain')
for i,value in enumerate(v):ax[1].text(i,value+(.10 if value>0 else-.10),f'{value:+.2f}',ha='center',va='bottom'if value>0 else'top',fontsize=9)
rs=[r for r in b['records']if r['step']in [227,245]];x=np.arange(2)
for offset,key,label,color in [(-.25,'causal_estimated_current_state_clearance_m','Causal estimate + broad future','#c06b60'),(0,'exact_current_state_same_future_bounds_clearance_m','Exact now + broad future','#5388a5'),(.25,'actual_sinusoid_future_clearance_m','Actual future (evaluator only)','#5b9771')]:ax[2].bar(x+offset,[r[key][-1]for r in rs],width=.24,label=label,color=color)
ax[2].axhline(.155,color='black',ls=':',label='Admission floor');ax[2].set(xticks=x,xticklabels=['227','245'],xlabel='Recorded decision step',ylabel='Clearance at 3.28 s (m)',title='Fixed-pose counterfactual, not a stopping rollout');ax[2].legend(fontsize=6.5,loc='lower right');ax[2].set_ylim(-.12,.32)
for p in ax:p.grid(axis='y',alpha=.15)
fig.suptitle('V682: motion-model breadth, progress loss, and uncertainty decomposition (zero robot integrations)',fontsize=12)
for ext in ['png','pdf']:fig.savefig(repo/f'docs/figures/dynamic_root_cause_v682.{ext}',dpi=180)
print(repo/'docs/figures/dynamic_root_cause_v682.png')
