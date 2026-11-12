"""Scientific plot of saved responses only, zero physics."""
import json,sys,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import numpy as np
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
D=R/'records/navigation_review_20261112';a=json.loads((R/'runs/navigation_review_20261112/LATEST_REJECTION_REPRODUCED.json').read_text());fig,ax=plt.subplots(1,2,figsize=(11.8,4.2),layout='constrained')
for version,color,label in [('v1080','#b33c38','V1080 actual: speed limit breach'),('v1082','#176b9a','V1082 actual: command rejected')]:
 p=R/'runs/v858_nav2_verified'/version/'remaining3555';z=np.load(p/'physics/NATIVE_TRACE.npz');q=z['qpos'][18074:];v=z['qvel'][18074:];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));vel=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);tt=np.arange(1,len(vel)+1)*.01;ax[0].plot(tt,vel,'o-',color=color,label=label,markersize=3)
 ss=np.load(p/'PLAN.npz')['states'];ax[0].plot(tt,ss[1:len(vel)+1,3],'--',color=color,alpha=.7,label=version.upper()+' prediction')
ax[0].axhline(.13,color='#333',lw=1.2,label='Original actual longitudinal cap');ax[0].set(xlabel='Time since saved-state handoff (s)',ylabel='Body longitudinal speed (m/s)',title='1. Response prediction gap');ax[0].legend(fontsize=7.2,loc='upper left');ax[0].grid(alpha=.18)
rows=a['rows'];tt=np.arange(1,len(rows)+1)*.01;gap=np.array([r['predicted_next_upper']-.129 for r in rows])*1e6;ax[1].plot(tt,gap,'o-',color='#176b9a',markersize=3,label='Chosen command: bound minus 0.129');reject=(a['minimum_legal_next_speed_upper']-.129)*1e6;ax[1].scatter([.15],[reject],color='#b33c38',marker='x',s=60,zorder=4);ax[1].annotate(f'Rejected at next request\n+{reject:.3f} micrometres/s',(.15,reject),xytext=(.075,-1800),arrowprops=dict(arrowstyle='->',color='#b33c38'),fontsize=9);ax[1].axhline(0,color='#333',lw=1.2);ax[1].set(xlabel='Time / requested command position (s)',ylabel='Predicted speed upper minus new guard (um/s)',title='2. New one-step guard loses feasibility');ax[1].grid(alpha=.18);ax[1].legend(fontsize=7.2,loc='lower left');fig.suptitle('Same saved NS failure state; original failures retained',fontsize=12);fig.savefig(D/'LATEST_FAILURES.png',dpi=180);plt.close(fig)
