"""Plots from completed recorded evidence, no simulation."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());fig,ax=plt.subplots(1,3,figsize=(15,4.4),layout='constrained')
for folder,name,label,color in [('v680_dynamic_later_stop_reserve','dev47_95000011_laterstop','V680 causal baseline','#5388a5'),('v683_dynamic_current_state_diagnosis','diagnosis49_95000011_currentstate','V683 exact-current diagnostic','#967bb0')]:
 trace=read(repo/'runs'/folder/name/'paired/geometry_memory/trace.json');ax[0].plot([(r['step']+1)*.08 for r in trace],[r['goal_distance_m']for r in trace],label=label,color=color)
ax[0].axhline(.45,color='black',ls=':',label='Arrival floor');ax[0].set(xlabel='Simulated time (s)',ylabel='Goal distance (m)',title='Exact current state is insufficient here');ax[0].legend(fontsize=7)
r=read(repo/'runs/v685_dynamic_terminal_forensics/retry02/COMPLETION.json')['records'];x=np.arange(len(r));ax[1].plot(x,[a['recomputed_total_minimum_m']for a in r],'o-',color='#c06b60',ms=3,label='Original future motion outer set');ax[1].plot(x,[a['known_static_minimum_m']for a in r],'^--',color='#5388a5',ms=3,label='Known static geometry');ax[1].plot(x,[a['actual_future_minimum_m']for a in r],'s-',color='#5b9771',ms=3,label='Actual future (evaluator only)');ax[1].axhline(.155,color='black',ls=':',label='Unchanged admission floor');ax[1].set(xlabel='Original candidate index (no new search)',ylabel='Minimum predicted clearance (m)',title='All18 rejected by the dynamic outer set');ax[1].legend(fontsize=6.6,loc='lower left')
v=read(repo/'runs/v684_dynamic_consistent_proposals/pre_navigation_retry02/COMPLETION.json')['records'];cases=[row for row in v if row['old_reference_terminal_error']is not None];x=np.arange(len(cases));ax[2].bar(x-.18,[a['old_reference_terminal_error']for a in cases],width=.35,label='Original proposal',color='#5388a5');ax[2].bar(x+.18,[a['new_reference_terminal_error']for a in cases],width=.35,label='Consistent turning-circle target',color='#cb8c48');ax[2].set(xticks=x,xticklabels=[str(a['checkpoint'])for a in cases],xlabel='Locked old decision',ylabel='Contour +0.2 heading error',title='Ideal target repair had no registered increment');ax[2].legend(fontsize=7);ax[2].text(.5,.010,'245: no safe nominal input',ha='center',fontsize=8)
for a in ax:a.grid(axis='y',alpha=.15)
fig.suptitle('V683–V685: controlled information test, rejected repair, and exact terminal failure attribution',fontsize=12)
for ext in ['png','pdf']:fig.savefig(repo/f'docs/figures/dynamic_information_v683.{ext}',dpi=180)
print(repo/'docs/figures/dynamic_information_v683.png')
