"""Offline evaluator: geometry below is for visualization only, never planner input."""
import argparse,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
p=argparse.ArgumentParser();p.add_argument('paired');p.add_argument('--output',required=True);a=p.parse_args();root=Path(a.paired)
protocol=json.loads((root/'STATIC_PROTOCOL.json').read_text())
fig,ax=plt.subplots(figsize=(8,8))
for x,y,hx,hy in protocol['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='.72'))
for x,y,r in protocol['known_circles']:ax.add_patch(Circle((x,y),r,color='.72'))
unknowns=protocol.get('physical_unknown_obstacles',[{'xy':protocol['event_xy'],'radius':protocol['event_radius']}])
addendum=root/'EVALUATION_SCENE_ADDENDUM.json'
if addendum.exists():unknowns=json.loads(addendum.read_text())['physical_unknown_obstacles']
for i,u in enumerate(unknowns):ax.add_patch(Circle(u['xy'],u['radius'],color='tab:red',label='Static unknown (evaluation truth)'if i==0 else None))
for name,color in zip(['frozen_sac','legacy_memory','no_memory','memory','memory_repeat','circle_memory','circle_repeat'],['black','tab:orange','tab:red','tab:purple','tab:pink','tab:blue','tab:cyan']):
 f=root/name/'trace.json'
 if not f.exists():continue
 t=json.loads(f.read_text());res=json.loads((f.parent/'result.json').read_text())
 if not t:continue
 poses=np.array([r['pose'] for r in t]);ax.plot(poses[:,0],poses[:,1],color=color,lw=1.7,label=f"{name}: {res['outcome']} ({len(t)} steps)")
 if name in ('memory','circle_memory'):
  lo,bot,hi,top=protocol['footprint_bounds'];corners=np.array([[lo,bot],[hi,bot],[hi,top],[lo,top]])
  for x,y,yaw in poses[::max(1,len(poses)//12)]:
   rot=np.array([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]]);ax.add_patch(Polygon(corners@rot.T+[x,y],fill=False,ec=color,alpha=.45,lw=.7))
start=protocol['start_qpos'][:2];ax.scatter(*start,c='green',s=50,marker='o',label='Start');ax.scatter(*protocol['goal_xy'],c='green',s=150,marker='*',label='Goal')
ax.set(xlim=(-5,5),ylim=(-5,5),aspect='equal',xlabel='x [m]',ylabel='y [m]',title=f"Pure physics / causal sensing / seed {protocol['seed']}")
ax.legend(loc='lower right',fontsize=8);fig.tight_layout();fig.savefig(a.output,dpi=160)
