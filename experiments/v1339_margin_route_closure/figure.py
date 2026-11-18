"""Recorded RPP trajectory and declared geometry, no models/propagation."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
R=Path(__file__).resolve().parents[2];D=R/'records/v1337_margin_route_20261118'
t=json.loads((R/'experiments/v1337_euclidean_margin_static_route/TASKS.json').read_text())[0];p=R/'runs/v858_nav2_verified/v1337/rpp_main';setup=json.loads((p/'physics/SETUP.json').read_text());z=np.load(p/'physics/NATIVE_TRACE.npz');q=z['qpos'][-1];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));rear=q[:2]-.3*np.array([np.cos(yaw),np.sin(yaw)]);rot=np.array([[np.cos(yaw),-np.sin(yaw)],[np.sin(yaw),np.cos(yaw)]])
ref=np.array(t['center_reference_path']);fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
for a in [ax,bx]:
 for x,y,hx,hy in setup['known']['known_rectangles']:a.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#888888',alpha=.45))
 for x,y,r in setup['known']['known_circles']:a.add_patch(Circle((x,y),r,color='#888888',alpha=.45))
 a.plot(ref[:,0],ref[:,1],'--',color='#218c72',label='Public center reference')
 a.plot(z['qpos'][:,0],z['qpos'][:,1],color='#165a9f',label='Recorded RPP actual')
 a.scatter(*q[:2],marker='x',s=50,color='#b51d32',label='Safe stop, goal not reached');a.grid(alpha=.2);a.set_aspect('equal');a.set(xlabel='World x (m)',ylabel='World y (m)')
old=np.array([[.89,.525],[.89,-.525],[-.29,-.525],[-.29,.525]]);new=np.array(json.loads((R/'experiments/v1336_euclidean_costmap_margin/GEOMETRY_QUALIFICATION.json').read_text())['polygon'])
bx.add_patch(Polygon(old@rot.T+rear,fill=False,color='#c64646',label='Old axis padding 0.15m'))
bx.add_patch(Polygon(new@rot.T+rear,fill=False,color='#22956d',label='Outer Euclidean 0.15m buffer'))
ax.scatter(4,-2,marker='*',s=80,color='#218c72');ax.set(xlim=(-4.6,4.6),ylim=(-3.5,.7),title='V1337: center passage reached, raw curvature rejected')
bx.set(xlim=(-.8,1.),ylim=(-1.6,.1),title='Recorded stop in central passage')
ax.legend(fontsize=7,loc='lower left');bx.legend(fontsize=7,loc='upper left')
fig.savefig(D/'rpp_center_and_curvature_stop.png',dpi=170);fig.savefig(D/'rpp_center_and_curvature_stop.pdf');plt.close(fig)
