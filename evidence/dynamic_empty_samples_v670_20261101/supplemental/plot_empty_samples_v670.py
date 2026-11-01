"""Static research figure from persisted results only, zero simulation."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v670_dynamic_empty_samples';validation=json.loads((root/'OFFLINE_VALIDATION.json').read_text())
fig,axes=plt.subplots(1,3,figsize=(13.8,4.0),layout='constrained')
x=np.arange(3);a=axes[0]
a.bar(x-.18,[r['old_mean_area_m2']for r in validation['datasets']],.36,label='First-hit baseline')
a.bar(x+.18,[r['new_mean_area_m2']for r in validation['datasets']],.36,label='+ unhit-sample cells')
a.set(xticks=x,xticklabels=['V662: 264','V667: 210','V669: 227'],ylabel='Mean center-box area (m²)',title='Identical recorded packets; finite coverage passed');a.legend(fontsize=8)
arrival_count=0
for label,folder in [('V669: finite recovery','v669_dynamic_reserved_recovery/dev37_95000011_reserve'),('V670: + empty samples','v670_dynamic_empty_samples/dev38_95000011_empty')]:
 path=repo/'runs'/folder/'paired/geometry_memory';trace=json.loads((path/'trace.json').read_text());result=json.loads((path/'result.json').read_text())if(path/'result.json').exists()else json.loads((path/'interrupted.json').read_text())
 arrival_count+=int(result['strict_safe_arrival'])
 axes[1].plot([r['step']for r in trace],[r['goal_distance_m']for r in trace],label=label)
axes[1].axhline(.45,color='black',ls='--',lw=1,label='Strict arrival threshold');axes[1].set(xlabel='Public steps',ylabel='Distance to goal (m)',title=f'Executed development; arrivals = {arrival_count}');axes[1].legend(fontsize=8)
rows=[json.loads(s)for s in(root/'dev38_95000011_empty/paired/geometry_memory/motion_estimate.jsonl').read_text().splitlines()];stats=[r['empty_sample_contract']for r in rows]
axes[2].plot([r['step']for r in rows],[s['removed_cells']/1024 for s in stats],label='Continuous cells excluded')
axes[2].plot([r['step']for r in rows],[1-s['area_after_m2']/s['area_before_m2']for s in stats],label='Immediate outer-box area gain')
axes[2].set(xlabel='V670 decision steps',ylabel='Fraction',ylim=(0,1),title='Outer rectangle can refill excluded interior');axes[2].legend(fontsize=8)
for a in axes:a.grid(alpha=.2)
fig.suptitle('V670: causal information and executed dynamic development',fontsize=12)
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for suffix in ['png','pdf']:fig.savefig(out/f'dynamic_empty_samples_v670.{suffix}',dpi=180)
print(out/'dynamic_empty_samples_v670.png')
