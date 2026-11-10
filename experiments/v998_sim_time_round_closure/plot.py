"""Publication-style diagnostic figure from saved actual data, no model calls."""
import gzip,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2]
def yaw(q):return np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))
def main():
    d=json.loads((R/'runs/v996_response_decomposition/RESPONSE_DECOMPOSITION.json').read_text());a=d['coefficient_gain_a'];b=d['coefficient_steer_rate_b']
    tasks=json.loads((R/'experiments/v995_sim_time_response/TASKS.json').read_text());fig,axes=plt.subplots(4,3,figsize=(12,10),sharex=True)
    for i,task in enumerate(tasks):
        p=Path(task['output'])/'physics';setup=json.loads((p/'SETUP.json').read_text());origin=task['origin_native_tick']
        with np.load(p/'NATIVE_TRACE.npz')as z:q=z['qpos'][origin-1:];v=z['qvel'][origin-1:]
        y=yaw(q);speed=v[:,0]*np.cos(y)+v[:,1]*np.sin(y);midv=(speed[:-1]+speed[1:])/2
        z=np.tan(q[:,setup['steering_qpos_addresses']]);k=np.c_[z[:,0]/(.6+.27*z[:,0]),z[:,1]/(.6-.27*z[:,1])].mean(axis=1);delta=np.arctan(.6*k)
        observed=np.unwrap(y-y[0]);ideal=np.r_[0.,np.cumsum(midv*(k[:-1]+k[1:])/2*.01)]
        estimated=a*ideal+b*(delta-delta[0]);time=np.arange(801)*.01
        rows=json.loads(gzip.decompress((p/'ALLOCATION.json.gz').read_bytes()));target=np.array([x['proof']['selected_curvature']for x in rows])
        axes[i,0].plot(time[1:],np.rad2deg(np.arctan(.6*target)),label='target');axes[i,0].plot(time,np.rad2deg(delta),label='actual encoder')
        axes[i,1].plot(time,np.rad2deg(observed),label='actual yaw');axes[i,1].plot(time,np.rad2deg(ideal),'--',label='encoder bicycle');axes[i,1].plot(time,np.rad2deg(estimated),':',linewidth=2,label='2-coefficient measured-input fit')
        axes[i,2].plot(time,np.rad2deg(observed-ideal),label='bicycle error');axes[i,2].plot(time,np.rad2deg(observed-estimated),label='fit error')
        for ax in axes[i]:ax.axvline(6,color='gray',alpha=.5,linestyle=':');ax.grid(alpha=.2)
        axes[i,0].set_ylabel(task['name'].replace('_',' ')+'\nangle [deg]',fontsize=8)
    for j,title in enumerate(['Virtual steering','Body yaw change','Integrated yaw residual']):axes[0,j].set_title(title)
    for ax in axes[-1]:ax.set_xlabel('new simulation time [s]')
    for ax in axes[0]:ax.legend(fontsize=6)
    fig.suptitle('V995 fixed steering responses: all 4 complete, no navigation acceptance\nFit calibrated on rows1/2; rows3/4 held out. Uses future measured inputs; not a causal predictor.',fontsize=10)
    fig.tight_layout(rect=[0,0,1,.945]);out=R/'docs/figures/V995_STEERING_RESPONSE_DECOMPOSITION.png';fig.savefig(out,dpi=160);plt.close(fig)
    print(json.dumps(dict(figure=str(out.relative_to(R)),models=0,integrations=0,actual_saved_traces_only=True)))
if __name__=='__main__':main()
