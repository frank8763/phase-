"""Offline scientific figure; the right panel uses evaluation truth only."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[2]/'runs/v648_static_unknown';fig,axes=plt.subplots(1,2,figsize=(10,4),sharex=True,sharey=True)
for ax,name,title in zip(axes,['map_connectivity_probe_16','truth_connectivity_probe_16'],['Remembered noisy endpoints','Physical geometry (evaluation only)']):
 d=json.loads((root/name/'paired/connectivity.json').read_text());x=np.array(d['x']);y=np.array(d['y']);v=np.array(d['best_clearance']);im=ax.imshow(v.T,origin='lower',extent=[x[0],x[-1],y[0],y[-1]],vmin=0,vmax=.3,cmap='viridis',aspect='equal');ax.contour(x,y,v.T,levels=[.15],colors='red',linewidths=1.2);ax.scatter(1.679,.946,c='white',edgecolors='black',s=25);ax.set(title=title,xlabel='x [m]',xlim=(-.8,2.2),ylim=(-.6,2.3))
axes[0].set_ylabel('y [m]');fig.subplots_adjust(right=.86,bottom=.16,top=.83,wspace=.12);fig.colorbar(im,cax=fig.add_axes([.89,.18,.02,.6]),label='Best clearance over 72 headings [m]');fig.suptitle('Static single obstacle / saved causal map at failure state',fontsize=12);fig.text(.5,.035,'Red contour: 0.15 m. Orientation-relaxed discrete diagnostic; not a dynamic feasibility certificate.',ha='center',fontsize=9)
out=root/'map_connectivity_probe_16/paired';fig.savefig(out/'map_bottleneck.png',dpi=200);fig.savefig(out/'map_bottleneck.svg')
