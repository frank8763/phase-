"""Plot persisted actual vehicle/physical actor and online reference paths, zero models."""
import gzip,json,pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=pathlib.Path(__file__).resolve().parents[2];root=repo/'runs/v807_reactive_single_task_continuation';cell=root/'main_slot01/paired/geometry_memory';pair=cell.parent;read=lambda p:json.loads(p.read_text());lines=lambda p:[json.loads(s)for s in p.read_text().splitlines()]
assert read(root/'ROUND_WINDOW.json')['round_closed']
p=read(pair/'STATIC_PROTOCOL.json');r=read(cell/'result.json')if(cell/'result.json').exists()else read(cell/'interrupted.json');e=lines(cell/'v648_execution.jsonl');xy=np.asarray([x['qpos_full'][:2]for x in e]);speed=np.asarray([np.linalg.norm(np.asarray(x['qvel_full'])[:2])for x in e]);time=np.arange(1,len(e)+1)*.08
with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
actor=np.asarray([x['actor_xy']for x in native]);truthmin=min(x['actual_clearance_m']for x in native)
fig,(ax,bt)=plt.subplots(1,2,figsize=(15,7),gridspec_kw={'width_ratios':[1.1,1]})
for x,y,hx,hy in p['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#a6b4c4'))
for x,y,rad in p['known_circles']:ax.add_patch(Circle((x,y),rad,color='#a6b4c4'))
plans=[read(x)for x in sorted(cell.glob('planning_*.json'))];valid=[x for x in plans if x['path']is not None]
if valid:
 path=np.asarray(valid[0]['path']);ax.plot(path[:,0],path[:,1],color='#20a56a',lw=3,label='Initial online global route')
 for row in valid[1:]:
  path=np.asarray(row['path']);ax.plot(path[:,0],path[:,1],color='#ac52c9',lw=1.7,alpha=.55,label='Subsequent online route'if row is valid[1]else None)
ax.plot(xy[:,0],xy[:,1],color='#1761ab',lw=2.5,label='Actual vehicle trace');ax.plot(actor[:,0],actor[:,1],color='#d97716',lw=4,label='Actual scene actor (evaluation only)')
ax.scatter(*p['start_qpos'][:2],s=70,c='#1f394a',marker='s',label='Start');ax.scatter(*p['goal_xy'],s=110,c='#e7bc19',marker='*',label='Goal');ax.set(xlim=(-5,5),ylim=(-5,5),aspect='equal',xlabel='World x (m)',ylabel='World y (m)');ax.grid(alpha=.2);ax.legend(loc='upper left',fontsize=8)
bt.plot(time,speed,color='#1761ab');bt.set(xlabel='Actual simulation time (s)',ylabel='Actual planar speed (m/s)');bt.grid(alpha=.2)
discovery=read(cell/'FIRST_DISCOVERY.json')if(cell/'FIRST_DISCOVERY.json').exists()else None;done=read(cell/'DISCOVERY_BRAKE_COMPLETION.json')if(cell/'DISCOVERY_BRAKE_COMPLETION.json').exists()else None
if discovery:
 bt.axvline(discovery['time'],ls='--',c='#d97716',label='First causal range detection');ax.scatter(*discovery['qpos'][:2],s=100,c='#d97716',marker='x',zorder=6)
if done:bt.axvline((done['finished_step']+1)*.08,ls='--',c='#ac52c9',label='Complete physical brake')
bt.legend(fontsize=8);fig.suptitle(f"V807 actual reactive dynamic development: {r.get('outcome','INTERRUPTED')}\nPhysical min clearance {truthmin:.6f} m; no simulated/interpolated new trajectory",fontsize=13)
fig.tight_layout();out=repo/'runs/v807_actual_analysis';out.mkdir(exist_ok=True);fig.savefig(out/'actual_global_dynamic_and_speed.png',dpi=170);plt.close(fig)
result=dict(status='SAVED_ACTUAL_TRAJECTORY_ANALYSIS',outcome=r.get('outcome'),public=len(e),navigation_native=len(native),private_native=r.get('prediction_steps'),first_discovery=None if discovery is None else {k:discovery[k]for k in ['step','time','speed_before_m_s','forward_progress_before_m','trigger']},actual_brake_completion=done,planning_attempts=len(plans),successful_paths=len(valid),actual_min_clearance=truthmin,actual_path_length=float(np.linalg.norm(np.diff(np.vstack([p['start_qpos'][:2],xy]),axis=0),axis=1).sum()),goal_remaining=r.get('goal_distance_m'),new_models=0,new_integrations=0)
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
