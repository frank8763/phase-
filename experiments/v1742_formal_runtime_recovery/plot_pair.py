"""Export saved phase02 trajectories; no engine, planner, audit or replay."""
import hashlib,json,os,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1643_formal_parent_metadata';D=R/'runs/v1742_formal_runtime_recovery/phase_02__full/figures'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert os.sched_getaffinity(0)=={4},'FIGURE_NON_MODEL_MATH_CPU4_ONLY'
 import numpy as np
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Rectangle,Circle
 ids=['phase_02__no_onward','phase_02__full'];data=[]
 for aid in ids:
  O=ROOT/'rounds'/aid;assert read(O/'COMPLETION.json')['closed']and(O/'RUNTIME_CLOSED_REVIEW.json').exists()
  out=O/'actual';result=read(out/'RESULT.json');task=read(O/'FORMAL_TASK.json');setup=read(out/'physics/SETUP.json')
  with np.load(out/'physics/NATIVE_TRACE.npz')as z:xy=z['qpos'][:,:2].copy();clear=z['clearance'].copy()
  initial=read(out/'CANONICAL_INITIAL_PACKET.json');final=read(out/'ACTUAL_FINAL_PACKET.json')
  # Original Vehicle.body source returns qpos[0:2]; no model is reconstructed.
  assert 'return float(q[0]),float(q[1])'in(R/'experiments/v858_nav2_verified/vehicle.py').read_text()
  assert np.max(abs(xy[-1]-np.asarray(final['body'][:2])))<=1e-8
  xy=np.vstack([initial['body'][:2],xy]);native=np.arange(len(xy));distance=np.linalg.norm(xy-np.asarray(task['goal_xy']),axis=1)
  data.append(dict(id=aid,task=task,setup=setup,result=result,xy=xy,native=native,distance=distance,clear=clear))
 D.mkdir(parents=True,exist_ok=False)
 colors=['#d97706','#2563eb'];labels=['No onward precheck','Full method'];fig,axes=plt.subplots(1,3,figsize=(14,4.4),layout='constrained')
 ax=axes[0];known=data[0]['setup']['known']
 for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,facecolor='#d1d5db',edgecolor='#9ca3af',lw=.5))
 for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,facecolor='#d1d5db',edgecolor='#9ca3af',lw=.5))
 for d,color,label in zip(data,colors,labels):
  ax.plot(d['xy'][:,0],d['xy'][:,1],c=color,lw=1.4,label=label);ax.scatter(*d['xy'][-1],c=color,marker='x',s=35)
  axes[1].plot(d['native'],d['distance'],c=color,lw=1.2,label=label)
  axes[2].plot(d['native'][1:],d['clear'],c=color,lw=1.1,label=label)
 ax.scatter(*data[0]['task']['start_xy'],c='#111827',marker='o',s=25,label='Start');ax.scatter(*data[0]['task']['goal_xy'],c='#111827',marker='*',s=80,label='Goal')
 ax.set(xlim=(-5,5),ylim=(-5,5),xlabel='World x (m)',ylabel='World y (m)',title='Saved actual trajectories');ax.set_aspect('equal');ax.legend(fontsize=8,loc='upper left')
 axes[1].set(xlabel='Native step (0.01 s simulation)',ylabel='Distance to original goal (m)',title='Task completion boundary');axes[1].axhline(.45,c='#6b7280',ls='--',lw=.9,label='Original goal radius')
 axes[2].set(xlabel='Native step (0.01 s simulation)',ylabel='Recorded actual clearance (m)',title='Physical telemetry');axes[2].axhline(.15,c='#991b1b',ls='--',lw=.9,label='Original 0.15 m floor');axes[2].legend(fontsize=8)
 for ax in axes:ax.grid(alpha=.18)
 fig.suptitle('Locked phase02 pair — same known course, phase 4.551718764234382',fontsize=12)
 fig.savefig(D/'phase02_pair.png',dpi=220);fig.savefig(D/'phase02_pair.pdf');plt.close(fig)
 # Exact saved initial-state provenance, not a second numerical audit.
 origins={}
 for aid in ids:
  path=ROOT/'rounds'/aid/'actual/INITIAL_FULL_STATE.npz'
  with zipfile.ZipFile(path)as z:origins[aid]={n:hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()}
 initial_equal=origins[ids[0]]==origins[ids[1]];assert initial_equal,'PAIR_INITIAL_STATE_BYTES_DIFFER'
 summary=dict(figure_only_no_model_or_audit_calls=True,source_vehicle_body_sha256=sha(R/'experiments/v858_nav2_verified/vehicle.py'),initial_state_uncompressed_members_SHA_equal=initial_equal,initial_member_SHA256=origins,rows=[dict(assignment=d['id'],scientific_passed=d['result']['passed'],actual_native=d['result']['new_actual_native'],own_replay_native=d['result']['own_replay_native'],goal_distance_m=float(d['distance'][-1]),actual_min_clearance_m=float(d['clear'].min()),first_error=d['result']['first_error'])for d in data],limitations='Same known course/new phase only; independent audit outcomes remain original machine results; no statistical/realtime/generalization claim')
 (D/'PAIR_FIGURE_PROVENANCE.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['rows']))
if __name__=='__main__':main()
