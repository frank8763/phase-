"""Standalone scientific figure from the already closed attribution arrays."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v739_joint_return_failure_analysis';result=json.loads((root/'RESULT.json').read_text());curves=np.load(root/'SAVED_TAIL_ATTRIBUTION_CURVES.npz')['curves']
assert result['status']=='FIXED_JOINT_REJECTION_ATTRIBUTION_COMPLETE'
fig,axes=plt.subplots(1,3,figsize=(12.5,3.6),sharey=True,constrained_layout=True)
for ax,summary in zip(axes,result['summaries']):
 best=summary['best_saved_tail'];idx=next(i for i,r in enumerate(result['records'])if(r['step'],r['rank'],r['tail_index'])==(best['step'],best['rank'],best['tail_index']));x=np.arange(1,329)*.01
 ax.plot(x,curves[idx,0],label='Known static geometry',color='#527b5c',lw=1.8)
 ax.plot(x,curves[idx,3],label='Original causal certificate',color='#bb3c39',lw=2)
 ax.plot(x,curves[idx,4],label='No future aging (diagnostic only)',color='#5675b7',ls='--',lw=1.4)
 ax.axhline(.155,color='black',ls=':',label='Unchanged admission floor')
 tick=best['first_original_below_floor_tick'];ax.axvline(tick*.01,color='#bb3c39',alpha=.35,lw=1);ax.annotate(f'{tick*.01:.2f} s',xy=(tick*.01,.155),xytext=(-30,-28),textcoords='offset points',color='#9e2b28')
 ax.set_title(f'Original state {summary["step"]}: best of {summary["tails"]} tails');ax.set_xlabel('Prediction look-ahead (s)');ax.grid(alpha=.18);ax.set_xlim(0,3.28)
axes[0].set_ylabel('Whole-body clearance lower bound (m)');handles,labels=axes[-1].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,fontsize=9)
fig.suptitle('All fixed joint returns rejected by future occupancy growth; no new navigation',fontsize=12)
fig.savefig(root/'joint_return_failure.png',dpi=200);fig.savefig(root/'joint_return_failure.pdf');plt.close(fig)
