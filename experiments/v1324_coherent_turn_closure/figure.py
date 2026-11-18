"""Draw recorded component, no replay/model/synthetic trajectory."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

R=Path(__file__).resolve().parents[2]; D=R/'records/v1323_coherent_turn_20261118'; D.mkdir(exist_ok=True)
t=json.loads((R/'experiments/v1323_coherent_mppi_turn_component/TASKS.json').read_text())[0]
with np.load(R/'runs/v858_nav2_verified/v1323/left_main/physics/NATIVE_TRACE.npz') as trace:
    q=trace['qpos']; yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2)); xy=q[:,:2]
reference=np.array(t['center_reference_path']); fig,ax=plt.subplots(figsize=(7,4.5),layout='constrained')
ax.plot(reference[:,0],reference[:,1],'--',color='#555555',label='Mechanical center reference')
ax.plot(xy[:,0],xy[:,1],color='#1769aa',label='Actual main (full repeat identical)')
ax.scatter([-4],[ -2],color='black',s=25,label='Start'); ax.scatter([xy[-1,0]],[xy[-1,1]],color='#1769aa',s=25)
goal=t['component_goal_xy']; ax.add_patch(Circle(goal,.15,color='#2a9d8f',alpha=.14,label='Component goal tolerance 0.15m'))
ax.scatter([goal[0]],[goal[1]],marker='*',s=90,color='#18816c',label='Component goal')
for i in [400,1000,1600]: ax.arrow(xy[i,0],xy[i,1],.1*np.cos(yaw[i]),.1*np.sin(yaw[i]),width=.0015,head_width=.018,color='#1769aa',length_includes_head=True)
ax.set(xlabel='World x (m)',ylabel='World y (m)',title='V1323 left-turn component: main and full repeat passed')
ax.set_aspect('equal'); ax.grid(alpha=.2); ax.legend(fontsize=8,loc='upper left')
fig.text(.02,.01,'Static component only; right arc rejected in geometric screening; no whole-route/dynamic claim.',fontsize=8)
fig.savefig(D/'left_turn_recorded.png',dpi=180); fig.savefig(D/'left_turn_recorded.pdf'); plt.close(fig)
