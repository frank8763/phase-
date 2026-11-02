"""Static publication-style diagnostic figure from audited existing traces."""
import gzip,json,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[2]/'runs/v697_rpccr_dynamic_initialization/cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

repo=Path(__file__).resolve().parents[2];root=repo/'runs/v697_rpccr_dynamic_initialization'
read=lambda p:json.loads(p.read_text());account=read(root/'FINAL_EVIDENCE_ACCOUNT.json');assert account['status']=='ALL_FINAL_EVIDENCE_CHECKS_PASS'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,axes=plt.subplots(1,3,figsize=(15,4.4));colors=['#2166ac','#d6604d'];names=['anchor_phase0','original_slot12']
for name,color,label in zip(names,colors,['Old success anchor, phase 0','Original slot 12, new noise/phase']):
    pair=root/name/'paired';cell=pair/'geometry_memory';rows=[json.loads(s) for s in (cell/'v648_execution.jsonl').read_text().splitlines()]
    protocol=read(pair/'STATIC_PROTOCOL.json');xy=np.asarray([protocol['start_qpos'][:2]]+[x['qpos_full'][:2] for x in rows]);times=np.r_[0.,[x['time'] for x in rows]]
    with gzip.open(cell/'dynamic_native.jsonl.gz','rt') as f:native=[json.loads(s) for s in f]
    axes[0].plot(xy[:,0],xy[:,1],color=color,label=label,lw=1.8)
    axes[1].plot(times,np.linalg.norm(xy-[4.,-2.],axis=1),color=color,lw=1.8)
    axes[2].plot([x['time'] for x in native],[x['actual_clearance_m'] for x in native],color=color,lw=1.5)
    first=read(cell/'FIRST_DISCOVERY.json');index=first['step'];axes[0].scatter(xy[index,0],xy[index,1],color=color,s=24,zorder=3)
axes[0].add_patch(plt.Rectangle((-.7,-2.35),.2,.7,facecolor='#999999',alpha=.35,label='Small actor swept envelope'))
axes[0].scatter([-4.,4.],[-2.,-2.],c=['#444444','#238b45'],marker='*',s=95,zorder=4)
axes[0].set(xlim=(-5,5),ylim=(-5,-.8),xlabel='x (m)',ylabel='y (m)',title='Executed root trajectories')
axes[0].set_aspect('equal',adjustable='box');axes[0].legend(loc='upper left',fontsize=7,frameon=False)
axes[1].axhline(.45,color='#333333',ls='--',lw=1);axes[1].set(xlabel='Simulation time (s)',ylabel='Goal distance (m)',title='Actual target progress')
axes[2].axhline(.15,color='#333333',ls='--',lw=1,label='Required 0.15 m');axes[2].set(xlabel='Simulation time (s)',ylabel='Full-body clearance (m)',title='Every native-step actual clearance');axes[2].legend(fontsize=8,frameon=False)
for ax in axes:ax.grid(alpha=.18)
fig.suptitle('RP-CCR V697: initialization repair development — not independent dynamic acceptance',fontsize=12,y=1.02)
fig.tight_layout();out=root/'figures';out.mkdir(exist_ok=True)
for extension in ['png','svg']:fig.savefig(out/('rpccr_v697_evidence.'+extension),bbox_inches='tight')
print(json.dumps({'figure':str(out/'rpccr_v697_evidence.png'),'simulation_integrations':0,'source':'Complete original audited execution and native dynamic traces; no smoothing.'}))
