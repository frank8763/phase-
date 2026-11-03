import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());out=repo/'runs/v766_commitment_release_diagnosis';base=np.load(repo/'runs/v762_observation_commitment/ORIGINAL_256_NATIVE_REPLAY.npz')['qpos'][-1];goal=np.asarray(read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json')['goal_xy'])
def yaw(q):return np.unwrap(np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2)))
fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for folder,label,color in [('v759_state_feedback_execution','V759 greedy feedback','#888888'),('v764_observation_progress_cycle','V764 committed observation','#3377aa'),('v767_certified_progress_release','V767 certified release','#aa3355')]:
 raw=repo/'runs'/folder;b=read(raw/'FEEDBACK_MAIN_SUMMARY.json');z=np.load(raw/'FEEDBACK_MAIN_ACTUAL.npz');t=np.arange(1,len(z['qpos'])+1)*.01;prog=np.linalg.norm(base[:2]-goal)-np.linalg.norm(z['qpos'][:,:2]-goal,axis=1);active=b['scheduled_public_completed'];dec=b['decisions'];xs=np.array([d['local_public']*.08 for d in dec]);modes=[d.get('selection_evidence',{}).get('mode','PROGRESS')=='OBSERVE'for d in dec]
 ax[0,0].plot(t[:active*8],prog[:active*8],color=color,label=label,lw=1.8);ax[0,0].plot(t[active*8-1:],prog[active*8-1:],color=color,ls='--',lw=1.3)
 ax[0,1].plot(t,np.rad2deg(yaw(np.vstack([base,z['qpos']]))[1:]-yaw(base[None,:])[0]),color=color,label=label,lw=1.5)
 ax[1,0].step(xs,[len(d['ranking'])for d in dec],where='post',color=color,label=label)
 if folder!='v759_state_feedback_execution':
  hold=[d['unknown_hold_m']for d in dec];ax[1,1].plot(xs,hold,color=color,label=label)
  for d in dec:
   if 'ACTUAL_SWEEP_AND_INFORMATION_RENEWED'in d['selection_evidence']['events']:
    ax[0,0].axvline(d['local_public']*.08,ls=':',color=color,lw=.8);ax[1,1].scatter([d['local_public']*.08],[d['unknown_hold_m']],color=color,marker='*',s=100)
ax[0,0].set(title='Actual goal progress; dashed = final retained tail',xlabel='Simulated elapsed time (s)',ylabel='Net goal progress from old checkpoint (m)');ax[0,0].legend(fontsize=8)
ax[0,1].set(title='Actual relative heading',xlabel='Simulated elapsed time (s)',ylabel='Heading (deg)')
ax[1,0].set(title='Full safety-certified candidates / fixed 15',xlabel='Simulated elapsed time (s)',ylabel='Admissible actions',ylim=(-.5,16))
ax[1,1].axhline(.45,color='#aaaaaa',ls='--',label='Observation trigger (scheduling only)');ax[1,1].set(title='Current unknown-domain hold reference; star = release',xlabel='Simulated elapsed time (s)',ylabel='3.28 s geometric reference bound (m)');ax[1,1].legend(fontsize=8)
for a in ax.flat:a.grid(alpha=.2)
fig.suptitle('RP-CCR finite observation/progress diagnostics: one reused development task',fontsize=13)
for suffix in ['png','pdf']:fig.savefig(out/('observation_round.'+suffix),dpi=180)
