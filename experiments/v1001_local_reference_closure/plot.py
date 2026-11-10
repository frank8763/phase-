"""Original causal supports and proposed references; not a new actual trajectory."""
import importlib.util,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1000_local_progress_reference'))
from reference import ref
def main():
    q=json.loads((R/'runs/v1000_local_progress_reference/QUALIFICATION.json').read_text());saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
    known=json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text());fig,axes=plt.subplots(1,2,figsize=(11,4.8))
    for i,ax in enumerate(axes):
        row=q['rows'][i];plan=row['plan'];p=np.array(plan['path']);source=saved['rows'][i]['search_source'];geom=ref._old.Geometry(known,source['periodic'])
        for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='gray',alpha=.5))
        for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,color='gray',alpha=.5))
        if geom.center_polygon is not None:ax.add_patch(Polygon(geom.center_polygon,closed=True,color='orange',alpha=.3,label='causal actor center cycle'))
        ax.plot(p[:,0],p[:,1],color='green',lw=3,label='proposed0.6m recovery reference')
        for index in [0,len(p)//2,len(p)-1]:
            x,y,a=p[index];rect=np.array([[-.44,-.375],[.44,-.375],[.44,.375],[-.44,.375]])
            rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
            ax.add_patch(Polygon(rect@rot.T+[x,y],closed=True,fill=False,edgecolor='green',alpha=.35))
        ax.scatter(p[0,0],p[0,1],c='blue',s=25,label='original saved stopped state');ax.scatter(4.,-2.,marker='*',c='red',s=90,label='unchanged final goal')
        ax.set_title(f"State{[6083,7814][i]}: geometry lower{row['audit']['independent_full_cycle_lower_m']:.3f}m\nprogress lower{row['audit']['actual_progress_lower_m']:.3f}m",fontsize=10)
        ax.set_xlim(-.6,4.7);ax.set_ylim(-3.,.7);ax.set_aspect('equal');ax.grid(alpha=.2);ax.set_xlabel('x [m]');ax.set_ylabel('y [m]')
    axes[1].legend(fontsize=7,loc='upper right')
    fig.suptitle('V1000 source-qualified finite-progress references\nAnalytical proposals only: no new physical tracking or final-goal success',fontsize=11)
    fig.tight_layout(rect=[0,0,1,.91]);p=R/'docs/figures/V1000_CAUSAL_LOCAL_REFERENCES.png';fig.savefig(p,dpi=160);plt.close(fig)
    print(json.dumps(dict(figure=str(p.relative_to(R)),models=0,integrations=0,proposed_reference_only=True)))
if __name__=='__main__':main()
