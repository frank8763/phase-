"""Standalone diagnosis figures from completed recorded evidence only."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());summary=read(repo/'runs/v676_dynamic_canonical_commands/FINAL_ANALYSIS.json');probe=read(repo/'runs/v676_dynamic_canonical_commands/WITNESS_CAUSAL_GATE_OFFLINE.json');branches=[b for b in summary['branches']if not b['is_repeat']]
fig,ax=plt.subplots(1,3,figsize=(15,4.5),layout='constrained');oracle=next(x for x in branches if x['version']=='V677');pair=repo/oracle['run'];protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
for x,y,hx,hy in protocol['known_rectangles']:ax[0].add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='.75',alpha=.6))
for x,y,r in protocol['known_circles']:ax[0].add_patch(Circle((x,y),r,color='.65',alpha=.6))
ax[0].add_patch(Circle(config['anchor_xy'],.35,fc='#d9813215',ec='#bd702e',ls='--',label='True full sweep (evaluator)'))
colors={'V676':'#287591','V677':'#40845b','V678':'#b66b31'}
for b in branches:
 trace=read(repo/b['run']/'geometry_memory/trace.json');xy=np.asarray([t['pose'][:2]for t in trace]);label=b['version']+(' privileged'if b['version']=='V677'else' causal');style='--'if b['version']=='V677'else'-';ax[0].plot(xy[:,0],xy[:,1],style,color=colors[b['version']],lw=1.6,label=label);ax[1].plot([(t['step']+1)*.08 for t in trace],[t['goal_distance_m']for t in trace],style,color=colors[b['version']],label=label)
start=np.asarray(protocol['start_qpos'])[:2];goal=protocol['goal_xy'];ax[0].plot(*start,'o',color='black',ms=4);ax[0].plot(*goal,'*',color='black',ms=9);ax[0].set(xlim=(-3.,.5),ylim=(-3.8,4.5),xlabel='x (m)',ylabel='y (m)',title='Same physical scene; recorded center paths');ax[0].set_aspect('equal');ax[0].annotate('Full sweep\n(evaluator only)',xy=config['anchor_xy'],xytext=(-2.9,1.0),fontsize=7,color='#98551e',arrowprops={'arrowstyle':'-','color':'#bd702e','lw':.7})
ax[1].axhline(.45,color='black',ls=':',label='Strict arrival threshold');ax[1].set(xlabel='Simulated time (s)',ylabel='Goal distance (m)',title='Privileged witness is a separate diagnostic');ax[1].legend(fontsize=8)
rows=probe['records'];ax[2].plot([r['step']for r in rows],[r['minimum_causal_future_clearance_lower_bound_m']for r in rows],label='Causal uncertainty gate',color='#287591');ax[2].plot([r['step']for r in rows],[r['minimum_known_full_sweep_clearance_m']for r in rows],label='Known full-sweep geometry',color='#40845b',ls='--');ax[2].axhline(.155,color='black',ls=':',label='Original admission floor');ax[2].set(xlabel='Recorded privileged trajectory step',ylabel='Future pose-sample clearance lower bound (m)',title='Same successful poses; different information');ax[2].legend(fontsize=7)
for a in ax:a.grid(alpha=.18)
fig.suptitle('V676–V678: actuator-consistent navigation and algorithm-versus-scene diagnosis',fontsize=12)
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(out/f'dynamic_command_scene_v676.{ext}',dpi=180)
print(out/'dynamic_command_scene_v676.png')
