"""Scientific geometry qualification figure, not a navigation/video result."""
import json,math,os
from pathlib import Path
repo=Path(__file__).resolve().parents[2];out=repo/'runs/joint_geometry_review_20261103';out.mkdir(exist_ok=True)
os.environ['MPLCONFIGDIR']=str(out/'mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
import numpy as np
read=lambda p:json.loads(p.read_text())
known=read(repo/'experiments/v706_global_field_qualification/KNOWN_FIELD.json');cases=read(repo/'experiments/v706_global_field_qualification/SCENE_CASES.json')
fig,axes=plt.subplots(1,3,figsize=(15,5.6),constrained_layout=True)
for ax,case in zip(axes,cases):
 result=read(repo/'runs/v709_joint_reference_certificate'/case['id']/'RESULT.json');selection=result['selection'];anchor=np.array(selection['anchor_xy']);path=np.array(selection['certificate']['reference_path']);axis=np.array(selection['axis_xy'])
 for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='.35'))
 for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,color='.35'))
 ax.add_patch(Rectangle((-.8,-.8),1.6,1.6,facecolor='none',edgecolor='purple',linestyle='--',label='Protected junction'))
 ax.add_patch(Circle(anchor,.35,color='orange',alpha=.35,label='Whole swept envelope'))
 endpoints=np.array([anchor-.25*axis,anchor+.25*axis]);ax.plot(*endpoints.T,color='orangered',lw=2,label='Actor centre motion')
 ax.plot(*path[:,:2].T,color='teal',lw=1.6,label='Full-body clearance witness')
 ax.scatter(*case['start_xy'],marker='o',color='royalblue',s=40,label='Start');ax.scatter(*case['goal_xy'],marker='*',color='crimson',s=90,label='Goal')
 ax.add_patch(Circle(case['start_xy'],3.,fill=False,color='royalblue',ls=':',alpha=.5))
 ax.set(xlim=(-5,5),ylim=(-5,5),xlabel='x (m)',ylabel='y (m)',title=case['id']+'\ncertified lower bound %.3f m'%selection['certificate']['continuous_polygonal_pose_clearance_lower_bound_m']);ax.set_aspect('equal');ax.grid(alpha=.15)
axes[0].legend(loc='lower left',fontsize=7)
fig.suptitle('Original field: geometric qualification only, before dynamic navigation\nNorth-south: nearby observation course; the actor need not obstruct the original reference.',fontsize=12)
for suffix in ['png','pdf']:fig.savefig(out/('joint_geometry_v709.'+suffix),dpi=180)
print(out/'joint_geometry_v709.png')
