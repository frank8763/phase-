"""Saved-only explanatory scientific figure, no model or rerendered physics."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Polygon,Circle
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1033_saved_task_diagnosis';sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from geometry_model import ref
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';row=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());proof=json.loads((O/'FULL_CYCLE_SEPARATION_PROOF.json').read_text());poly=ref._old.Geometry(setup['known'],row['source']['periodic']).center_polygon;curve=np.asarray(proof['curve']);fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
for x,y,hx,hy in setup['known']['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,fc='#566273',ec='#263346'))
for x,y,r in setup['known']['known_circles']:ax.add_patch(Circle((x,y),r,fc='#566273'))
ax.add_patch(Polygon(poly,fc='#f7b65b',ec='#a25a07',label='Causal full-period center set'))
closed=np.vstack([curve,curve[0]]);ax.plot(closed[:,0],closed[:,1],color='#c23535',lw=3,label='Continuous forbidden separating curve')
rad=proof['static_forbidden_ball_radius_m'];ar=proof['actor_forbidden_ball_radius_m'];
for ix,rr in [(1,rad),(2,ar),(3,ar),(4,rad),(5,rad),(6,rad)]:ax.add_patch(Circle(curve[ix],rr,fc='#e05b5b',ec='#be3535',alpha=.13))
start=np.asarray(row['packet']['body'][:3]);goal=np.asarray(row['plan']['original_goal']);ax.scatter(*start[:2],s=70,c='#197f9a',label='Saved stopped vehicle');ax.arrow(start[0],start[1],.45*np.cos(start[2]),.45*np.sin(start[2]),width=.015,color='#197f9a');ax.scatter(*goal,s=100,marker='*',c='#146f46',label='Original goal');ax.add_patch(Circle(goal,.45,fill=False,ec='#146f46',lw=2));ax.text(4.,-1.47,'Goal radius 0.45 m',ha='center',fontsize=10)
ax.text(.1,-3.3,'This spatial-union contract has no continuous certified route.\nThe real moving task requires time-aligned occupancy; it is not proved impossible.',fontsize=11,bbox=dict(facecolor='white',alpha=.9,edgecolor='#bbb'))
ax.set(xlim=(-.6,5.15),ylim=(-3.6,.75),xlabel='x (m)',ylabel='y (m)',title='Original difficult task: why full-period spatial certification blocks the goal')
ax.set_aspect('equal');ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=9);fig.savefig(O/'FULL_CYCLE_CUT.png',dpi=160)
print(O/'FULL_CYCLE_CUT.png')
