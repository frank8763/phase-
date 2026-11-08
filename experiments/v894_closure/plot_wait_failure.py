"""Static scientific figure from closed actual states; no synthetic motion."""
import json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v894_20261108'
def main():
    import sys
    sys.path.insert(0,str(R/'experiments/v891_dynamic_consistency_software'))
    from reproduce import pose,footprint
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon,Circle
    p=R/'runs/v858_nav2_verified/v894/main_we';source=json.loads((REC/'STOPPED_ACTOR_ANALYSIS.json').read_text());cfg=json.loads((R/'experiments/v894_wait_map_validation/A_motion.yaml').read_text());vertices=json.loads(cfg['local_costmap']['local_costmap']['ros__parameters']['footprint'])
    z=np.load(p/'physics/NATIVE_TRACE.npz');f=np.load(p/'physics/FAILED_NATIVE_STATE.npz');setup=json.loads((p/'physics/SETUP.json').read_text());fig,axes=plt.subplots(1,3,figsize=(12,4),constrained_layout=True)
    for ax,target in zip(axes[:2],[126.,129.95]):
        row=min(source['wait_pose_geometry_witnesses'],key=lambda x:abs(x['sim_time']-target));i=int(np.argmin(abs(z['time']-row['sim_time'])));body=footprint(pose(*row['vehicle_xy'],row['yaw']),vertices)
        ax.add_patch(Polygon(np.asarray(row['forecast_polygon']),color='tab:red',alpha=.22,label='Causal future occupancy'))
        ax.add_patch(Polygon(body,fill=False,edgecolor='tab:blue',linewidth=2,label='Safety-padded body'))
        c=z['mocap_pos'][i,0,:2];ax.add_patch(Circle(c,.1,color='black',label='Actual actor (evaluation only)'))
        ax.set(aspect='equal',xlim=(2.,3.7),ylim=(-2.55,-.5),title=f"Actual t={row['sim_time']:.2f}s\nclearance={row['actual_clearance_m']:.4f}m",xlabel='x(m)',ylabel='y(m)')
    axes[0].legend(fontsize=7,loc='lower left')
    mask=z['time']>=120.;axes[2].plot(z['time'][mask],z['clearance'][mask],label='Actual native clearance')
    axes[2].scatter(float(f['time']),source['minimum_actual_clearance_m'],color='red',s=22,label='Failed final native step')
    axes[2].axhline(.15,color='red',linestyle='--',label='Unchanged0.15m floor');axes[2].axvline(source['final_slow_interval_start_sim_s'],color='0.4',linestyle=':',label='Speed<=0.03m/s from here')
    axes[2].set(xlabel='Simulation time(s)',ylabel='Clearance(m)',title='Approaching actor despite stopped vehicle');axes[2].legend(fontsize=7)
    fig.savefig(REC/'STOPPED_WAIT_FAILURE.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
