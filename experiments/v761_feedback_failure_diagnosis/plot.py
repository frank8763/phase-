import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
repo=Path(__file__).resolve().parents[2];raw=repo/'runs/v759_state_feedback_execution';out=repo/'runs/v761_feedback_failure_diagnosis';read=lambda p:json.loads(p.read_text());r=read(raw/'RESULT.json');b=r['branches'][0];base=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz')['qpos'][-1];goal=np.asarray(read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json')['goal_xy'])
def progress(q):return np.linalg.norm(base[:2]-goal)-np.linalg.norm(q[:,:2]-goal,axis=1)
def yaw(q):return np.unwrap(np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2)))
fig,ax=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for profile,color in [('STRAIGHT','#6688aa'),('LEFT_RIGHT','#aa8866'),('RIGHT_LEFT','#66aa88')]:
 z=np.load(repo/('runs/v753_coupled_progress_repaired/'+profile+'_MAIN_ACTUAL.npz'));t=np.arange(1,len(z['qpos'])+1)*.01;ax[0,0].plot(t,progress(z['qpos']),label='Fixed '+profile,color=color,lw=1.3)
z=np.load(raw/'FEEDBACK_MAIN_ACTUAL.npz');t=np.arange(1,len(z['qpos'])+1)*.01;ax[0,0].plot(t,progress(z['qpos']),label='State feedback',color='#992244',lw=2);ax[0,0].set(title='Actual goal progress from the same checkpoint',xlabel='Elapsed simulated time (s)',ylabel='Net goal progress (m)');ax[0,0].legend(fontsize=8)
ax[0,1].plot(t,np.rad2deg(yaw(np.vstack([base,z['qpos']]))[1:]-yaw(base[None,:])[0]),color='#992244');ax[0,1].set(title='Actual heading: only 2.82 deg range before rejection',xlabel='Elapsed simulated time (s)',ylabel='Relative heading (deg)')
xs=[d['local_public']*.08 for d in b['decisions']];targets=[d['target'][2]-d['target'][3]for d in b['decisions']];ax[1,0].step(xs,targets,where='post',label='Selected target differential',color='#992244');ax[1,0].plot(t,z['controls'][:,2]-z['controls'][:,3],label='Actually applied differential',color='#3366aa');ax[1,0].set(title='Frequent target changes vs applied commands',xlabel='Elapsed simulated time (s)',ylabel='Rear left minus right command');ax[1,0].legend(fontsize=8)
ax[1,1].step(xs,[len(d['ranking'])for d in b['decisions']],where='post',color='#3366aa');ax[1,1].scatter(xs,[len(d['ranking'])for d in b['decisions']],s=18,color='#3366aa');ax[1,1].set(title='Certified candidates out of the fixed 15',xlabel='Elapsed simulated time (s)',ylabel='Admissible actions',ylim=(-.5,16))
for aa in ax.flat:aa.axvline(52*.08,ls='--',lw=1,color='#777777');aa.grid(alpha=.2)
fig.suptitle('V759: 0.738 m final progress; sustained component NOT PASSED',fontsize=14)
for suffix in ['png','pdf']:fig.savefig(out/('feedback_diagnosis.'+suffix),dpi=180)
