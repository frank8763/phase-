"""Static scientific figure from closed evidence; no simulator imports."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v748_handover_failure_attribution'
rows=json.loads((root/'OBSERVATION_WINDOWS.json').read_text());candidates=json.loads((root/'CANDIDATES.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
for step in [115,116,117,118]:
 data=[r for r in rows if r['step']==step and r['amplitude']==8.]
 ax[0].plot([r['packet_index']*.08 for r in data],[r['forward_030_geometry_m']for r in data],label=f'Boundary {step}')
ax[0].axhline(.155,color='black',ls='--',label='Certificate floor 0.155 m')
ax[0].set(xlabel='Elapsed actual observation time (s)',ylabel='0.30 m forward reference: clearance lower bound (m)',title='No admissible geometric renewal window')
ax[0].legend(fontsize=8);ax[0].grid(alpha=.2)
idx=np.arange(len(candidates))
for field,label in [('static_min_m','Known static geometry'),('minimum_causal_m','Actual time-varying certificate'),('unaged_counterfactual_min_m','No-aging counterfactual (never executed)')]:
 ax[1].plot(idx,[c[field]for c in candidates],'.-',ms=4,label=label)
ax[1].axhline(.155,color='black',ls='--')
ax[1].set(xlabel='All 35 saved successor candidates (fixed order)',ylabel='Minimum clearance (m)',title='Rejections arise from future unknown occupancy')
ax[1].legend(fontsize=8);ax[1].grid(alpha=.2)
fig.suptitle('RP-CCR V746 / V748: bounded component diagnosis; global navigation not passed',fontsize=12)
fig.savefig(root/'handover_rejection.png',dpi=200);fig.savefig(root/'handover_rejection.pdf');plt.close(fig)
