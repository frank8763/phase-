"""Render only saved physical trajectory; no models or replay."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
R=Path(__file__).resolve().parents[2];D=R/'records/v1329_static_route_20261118'
t=json.loads((R/'experiments/v1329_coherent_mppi_static_route/TASKS.json').read_text())[0]
s=json.loads((R/'runs/v858_nav2_verified/v1329/static_main/physics/SETUP.json').read_text())
z=np.load(R/'runs/v858_nav2_verified/v1329/static_main/physics/NATIVE_TRACE.npz');f=np.load(R/'runs/v858_nav2_verified/v1329/static_main/physics/FAILED_NATIVE_STATE.npz')
xy=np.vstack([z['qpos'][:,:2],f['qpos'][:2]]);q=f['qpos'];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
ref=np.array(t['center_reference_path']);fig,(ax,bx)=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
for p in [ax,bx]:
 for x,y,hx,hy in s['known']['known_rectangles']:p.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#888888',alpha=.55))
 for x,y,r in s['known']['known_circles']:p.add_patch(Circle((x,y),r,color='#888888',alpha=.55))
 p.plot(ref[:,0],ref[:,1],'--',color='#218c72',lw=1.5,label='Public reference')
 p.plot(xy[:,0],xy[:,1],color='#165a9f',lw=1.6,label='Recorded actual main')
 p.scatter(*xy[-1],color='#b81c31',marker='x',s=65,label='Safety gate: 0.149854 m')
 p.set_aspect('equal');p.grid(alpha=.2);p.set(xlabel='World x (m)',ylabel='World y (m)')
ax.set(xlim=(-5,5),ylim=(-4,1.2),title='V1329 static route: failed; repeat unexecuted');ax.scatter(4,-2,marker='*',color='#218c72',s=90,label='Original goal');ax.legend(fontsize=8,loc='lower left')
local=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])
rot=np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]])
bx.add_patch(Polygon(local@rot.T+q[:2],fill=False,color='#b81c31',lw=1.4,label='Nominal body enclosure'))
bx.set(xlim=(.1,2.1),ylim=(-1,.65),title='Near right-side wall: reference deviation 0.576 m');bx.legend(fontsize=8,loc='lower right')
fig.savefig(D/'static_failure_recorded.png',dpi=170);fig.savefig(D/'static_failure_recorded.pdf');plt.close(fig)
