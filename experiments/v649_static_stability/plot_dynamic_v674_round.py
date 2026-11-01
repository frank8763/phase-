"""Standalone research figure from completed real logs; zero integration."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]if p.exists()else[]
summary=read(repo/'runs/v674_dynamic_renewable_backup/FINAL_ANALYSIS.json');fig,ax=plt.subplots(1,3,figsize=(14,4),layout='constrained')
old=read(repo/'runs/v673_dynamic_joint_forecast/dev40_95000011_joint/paired/geometry_memory/trace.json');ax[0].plot([r['step']for r in old],[r['goal_distance_m']for r in old],color='.6',label='V673: fixed backup')
for record,color in zip([b for b in summary['branches']if not b['is_repeat']],['#287591','#c66a33']):
 cell=repo/record['run']/'geometry_memory';trace=read(cell/'trace.json');ax[0].plot([r['step']for r in trace],[r['goal_distance_m']for r in trace],color=color,label=record['version'])
 attempts=lines(cell/'handover_attempts.jsonl');steps=np.asarray([r['step']for r in trace]);ad=lines(cell/'model_admission.jsonl');accepted=[r['step']for r in attempts if r['status']=='CERTIFIED_RETURN'];alternative=[r['step']for r in ad if r.get('joint_admission_distinct_command_rank',0)>0]
 ax[1].plot(steps,np.searchsorted(accepted,steps,side='right'),color=color,label=record['version']+' certified return')
 if alternative:ax[1].plot(steps,np.searchsorted(alternative,steps,side='right'),color=color,ls='--',label=record['version']+' alternate input')
ax[0].axhline(.45,color='black',ls='--',lw=1,label='Arrival threshold');ax[0].set(xlabel='Public steps (0.08 s each)',ylabel='Goal distance (m)',title='Same development task; full outcomes');ax[0].legend(fontsize=8)
ax[1].set(xlabel='Public steps',ylabel='Cumulative executed interventions',title='Mechanism use is separate from arrival');ax[1].legend(fontsize=8)
probe=read(repo/'runs/v674_dynamic_renewable_backup/selection_probe/COMPLETION.json')['records'][0]['tested'];values=[max(c['minimum_clearance_m']for c in x['backup_attempt']['candidates'])for x in probe];ax[2].bar(range(len(values)),values,color=['#a34c44','#3e8d66','#a34c44']);ax[2].axhline(.155,color='black',ls='--',lw=1,label='Original certificate floor');ax[2].set(xticks=range(len(values)),xticklabels=['Highest score','Second input','Third input'],ylabel='Best backup clearance (m)',ylim=(0,.21),title='Locked step 217: a concrete missed input');ax[2].legend(fontsize=8)
for a in ax:a.grid(alpha=.2,axis='y')
fig.suptitle('V674–V675: two non-arrivals; raw-control contract audit failed',fontsize=12)
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(out/f'dynamic_renewable_backup_v674.{ext}',dpi=180)
print(out/'dynamic_renewable_backup_v674.png')
