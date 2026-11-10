"""Scientific figure from already saved states only; zero model steps."""
import json,math,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
C=Path(__file__).parent;R=C.resolve().parents[1];O=R/'runs/v983_saved_transient_diagnosis'
sys.path.insert(0,str(C));from analyze import NoModel
sys.path.insert(0,str(R/'experiments/v982_precise_recovery_gate'))
from tracking import TrackingGuard
def main():
    saved=json.loads((O/'COMPONENT_REFERENCE.json').read_text());result=json.loads((O/'DIAGNOSIS.json').read_text());plan=saved['proposal'];origin=result['exact_accounting']['historical_restore_native']
    with np.load(O/'physics/NATIVE_TRACE.npz')as z:
        q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));actual=np.c_[q[origin:,:2],yaw[origin:]]
    g=TrackingGuard(plan);g.mode='FOLLOW_RECOVERY';error=[]
    for pose in actual:
        try:g.monitor_body(dict(body=pose.tolist()))
        except AssertionError:pass
        error.append(g.last_proof['heading_error_rad']*180/math.pi)
    ref=g.dense;start=ref[0,:2];index=result['fault_tick']-origin-1;stop=(index+1)*.01
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11.8,4.7),layout='constrained')
    local=ref[np.linalg.norm(ref[:,:2]-start,axis=1)<=.09]
    ax=axes[0];ax.plot((local[:,0]-start[0])*1000,(local[:,1]-start[1])*1000,label='Committed reference',lw=2,color='#2f68a0')
    ax.plot((actual[:,0]-start[0])*1000,(actual[:,1]-start[1])*1000,label='Actual native trace',color='#bd4b3f',lw=2)
    ax.scatter((actual[index,0]-start[0])*1000,(actual[index,1]-start[1])*1000,color='#bd4b3f',s=35,zorder=5,label='Guard requests stop')
    ax.set(xlabel='x from reference start (mm)',ylabel='y displacement (mm; expanded scale)',title='Position follows closely: maximum error 2.66 mm')
    ax.set_xlim(-3,92);ax.set_ylim(-5,7);ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=8)
    ax=axes[1];times=np.arange(1,len(actual)+1)*.01
    ax.plot(times,error,color='#bd4b3f',lw=2,label='Actual heading error')
    ax.axhline(.035*180/math.pi,color='#2f68a0',ls='--',label='Original 0.035 rad limit')
    ax.axvline(stop,color='#666666',ls=':',label=f'Stop request at {stop:.2f} s')
    ax.axvspan(stop,times[-1],color='#aaaaaa',alpha=.12,label='Recorded finite stop tail')
    ax.set(xlabel='New-branch simulation time (s)',ylabel='Nearest-reference heading error (degrees)',title='Heading error continues to grow during stopping',ylim=(0,2.6))
    ax.grid(alpha=.2);ax.legend(loc='lower right',fontsize=8)
    fig.suptitle('V982 component 0: NOT PASSED — saved-state diagnosis, no rerun',fontsize=13,weight='bold')
    fig.savefig(O/'V982_SAVED_TRACKING.png',dpi=160)
    fig.savefig(O/'V982_SAVED_TRACKING.pdf')
    plt.close(fig)
    print(json.dumps(dict(figure=str(O/'V982_SAVED_TRACKING.png'),models=0,integrations=0)))
if __name__=='__main__':main()
