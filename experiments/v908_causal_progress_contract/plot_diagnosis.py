"""Recreate diagnostic figure from actual archived V907 state records."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
R=Path(__file__).resolve().parents[2];raw=R/'runs/v858_nav2_verified/v907/main_we'
with np.load(raw/'physics/NATIVE_TRACE.npz')as z:t=z['time'];q=z['qpos'];clear=z['clearance']
known=json.loads((raw/'physics/SETUP.json').read_text())['known'];events=json.loads((raw/'REFUGE_SUPERVISION.json').read_text())['events']
fig,(ax,bx)=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#6b7280',alpha=.6))
for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,color='#6b7280',alpha=.6))
ax.plot(q[:,0],q[:,1],color='#2563eb',lw=1.8,label='Actual vehicle trajectory')
ax.scatter([-4,4],[-2,-2],c=['#16a34a','#dc2626'],marker='*',s=130,zorder=5);ax.add_patch(Circle((4,-2),.45,fill=False,ec='#dc2626',ls='--'))
requests=[e for e in events if e['event']=='REFUGE_REQUEST']
for i,e in enumerate(requests,1):
 x,y=e['body'][:2];ax.scatter([x],[y],c='#d97706',s=25,zorder=6);ax.annotate(str(i),(x,y),xytext=(6,6+12*(i-1)),textcoords='offset points',fontsize=10,color='#92400e')
ax.set(xlim=(-4.8,4.9),ylim=(-3.3,.7),xlabel='x [m]',ylabel='y [m]',title='Three recoveries return to the same bottleneck');ax.set_aspect('equal');ax.legend(loc='upper left',fontsize=8)
bx.plot(t,np.linalg.norm(q[:,:2]-[4.,-2.],axis=1),color='#2563eb',label='Distance to original goal')
bx.axhline(.45,ls='--',color='#dc2626',label='Strict arrival threshold')
for i,e in enumerate(requests,1):bx.axvline(e['native_tick']*.01,color='#d97706',ls=':',alpha=.8)
bx.set(xlabel='Physical time [s]',ylabel='Distance [m]',title='Motion continues; goal progress does not');bx.grid(alpha=.2);bx.legend(fontsize=8)
fig.suptitle('V907 failed dynamic development — actual data, no confirmation claim',fontsize=12)
fig.savefig(R/'docs/paper_ras/figures/dynamic_recovery_cycle_20261109.png',dpi=180)
