"""Scientific figures from closed native traces, without model initialization."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];raw=repo/'runs/v753_coupled_progress_repaired';root=repo/'runs/v755_coupled_failure_attribution'
r=json.loads((raw/'RESULT.json').read_text());p=json.loads((repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json').read_text());baseline=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz');initial=baseline['qpos'][-1];names={'STRAIGHT':'Straight','LEFT_RIGHT':'Left then right','RIGHT_LEFT':'Right then left'}
fig,axs=plt.subplots(1,3,figsize=(14,4.3),layout='constrained')
for b in r['branches']:
 name=names[b['profile']];a=np.load(raw/(b['name']+'_ACTUAL.npz'));d=b['decisions'];failed=d[-1];color=axs[0]._get_lines.get_next_color();progress=np.linalg.norm(initial[:2]-p['goal_xy'])-np.linalg.norm(a['qpos'][:,:2]-p['goal_xy'],axis=1);t=np.arange(1,len(progress)+1)*.01;boundary=failed['local_public']*.08
 axs[0].plot(t[t<=boundary],progress[t<=boundary],color=color,label=name);axs[0].plot(t[t>boundary],progress[t>boundary],color=color,ls='--');axs[0].plot([boundary],[progress[failed['local_public']*8-1]],'x',color=color)
 axs[1].plot([x['local_public']*.08 for x in d],[x['minimum_causal_clearance_m']for x in d],'.-',label=name,color=color)
 axs[2].plot(a['qpos'][:,0],a['qpos'][:,1],label=name,color=color)
axs[0].set(xlabel='Elapsed actual branch time (s)',ylabel='Goal progress (m)',title='Solid: renewed control; dashed: retained tail')
axs[1].axhline(.155,color='black',ls='--',label='0.155 m gate');axs[1].set(xlabel='Candidate decision time (s)',ylabel='Full 328-tick certificate minimum (m)',title='All three eventually reject a new contract')
axs[2].plot([initial[0]],[initial[1]],'ko',label='Shared original state 32');axs[2].set(xlabel='World x (m)',ylabel='World y (m)',title='Actual paths (shared old development state)');axs[2].axis('equal')
for ax in axs:ax.grid(alpha=.2);ax.legend(fontsize=7)
fig.suptitle('RP-CCR V753: three fixed component conditions; no four-leg qualification',fontsize=12)
fig.savefig(root/'coupled_progress.png',dpi=200);fig.savefig(root/'coupled_progress.pdf');plt.close(fig)
