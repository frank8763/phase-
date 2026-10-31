import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
import numpy as np
p=argparse.ArgumentParser();p.add_argument('planning');a=p.parse_args();src=Path(a.planning);x=json.loads(src.read_text());w=x['causal_input'];fig,ax=plt.subplots(figsize=(7,7))
for cx,cy,hx,hy in w['rectangles']:ax.add_patch(Rectangle((cx-hx,cy-hy),2*hx,2*hy,color='.65'))
for cx,cy,r in w['circles']:ax.add_patch(Circle((cx,cy),r,color='.65'))
pts=np.array(w['sensor_points']);ax.scatter(pts[:,0],pts[:,1],s=5,c='tab:red',label='Causal remembered returns')
path=np.array(x['path']);ax.plot(path[:,0],path[:,1],color='tab:blue',label='Planned prefix')
ax.scatter(*w['goal'],marker='*',s=150,c='green',label='Goal');ax.scatter(*x['pose'][:2],s=40,c='black',label='Robot')
protocol=json.loads((src.parents[1]/'STATIC_PROTOCOL.json').read_text());ax.add_patch(Circle(protocol['event_xy'],protocol['event_radius'],fill=False,color='purple',lw=2,label='Unknown obstacle (evaluation only)'))
ax.set(xlim=(-5,5),ylim=(-5,5),aspect='equal',xlabel='x [m]',ylabel='y [m]');ax.legend(loc='lower right',fontsize=8);fig.tight_layout();fig.savefig(src.parent/'map_diagnostic.png',dpi=140)
