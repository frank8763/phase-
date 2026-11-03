"""Plot actual saved observation timing; no physical prediction."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v741_preemptive_timing_analysis';r=json.loads((root/'RESULT.json').read_text());rows=[x for x in r['records']if x['label']in['S073_AM8_C1_SCAN','S073_AM8_C1_ADVANCE_4']]
fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True)
for row in rows:
 x=[p['actual_public_step']for p in row['samples']];hold=[p['geometric_hold_3_28s_lower_m']for p in row['samples']];forward=[p['geometric_forward_0_30m_lower_m']for p in row['samples']];label='Observation phase'if 'SCAN'in row['label']else'Advance phase';color='#337b55'if 'SCAN'in row['label']else'#bc4b3f';ax.plot(x,hold,color=color,label=label+': hold-pose bound',lw=2);ax.plot(x,forward,color=color,ls='--',alpha=.7,label=label+': geometric 0.30 m bound')
ax.axhline(.155,color='black',ls=':',label='Unchanged 0.155 m admission floor');ax.axvline(114.5,color='gray',alpha=.7);ax.set_xlabel('Actual public boundary index (0.08 s per step)');ax.set_ylabel('3.28 s clearance lower bound (m)');ax.set_title('A full safe motion contract can outlast the window for a fresh certificate');ax.grid(alpha=.18);ax.legend(loc='lower left',fontsize=8);ax.text(.99,.97,'Geometric diagnostics only; native handover is unverified',transform=ax.transAxes,ha='right',va='top',fontsize=8);fig.savefig(root/'observation_handover_window.png',dpi=200);fig.savefig(root/'observation_handover_window.pdf');plt.close(fig)
