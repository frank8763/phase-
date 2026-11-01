"""Plots from completed dynamic interval branches only; zero integration."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
roots=[('32-step observation',repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe32/paired','#2563eb'),('0-step observation',repo/'runs/v663_dynamic_interval_tracking/dev33_95000011_observe0/paired','#dc2626')]
extra=repo/'runs/v664_dynamic_causal_proposals/dev34_95000011_proposal/paired'
if (extra/'geometry_memory/result.json').exists():roots.append(('Current proposal + full future gate',extra,'#16a34a'))
p=read(roots[0][1]/'STATIC_PROTOCOL.json');c=read(roots[0][1]/'DYNAMIC_PROTOCOL.json')
fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained');scene,progress,clear,width=axs.ravel()
for x,y,hx,hy in p['known_rectangles']:scene.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#475569',alpha=.7))
for x,y,r in p['known_circles']:scene.add_patch(Circle((x,y),r,color='#475569',alpha=.7))
scene.add_patch(Circle(c['anchor_xy'],.35,color='#dc2626',alpha=.18,label='Full actor motion envelope'))
scene.add_patch(Rectangle((-.8,-.8),1.6,1.6,color='#f59e0b',alpha=.18,label='Protected junction'))
reference=np.asarray(c['swept_envelope_reference']['reference_path']);scene.plot(*reference[:,:2].T,':',color='#64748b',label='Offline full-sweep bypass')
scene.plot(*p['goal_xy'],'k*',ms=12);scene.plot(*p['start_qpos'][:2],'ko',ms=5)
for name,root,color in roots:
 cell=root/'geometry_memory';trace=read(cell/'trace.json');result=read(cell/'result.json')
 xy=np.asarray([r['pose'][:2]for r in trace]);t=np.asarray([r['physical_step']*.01 for r in trace]);distance=np.asarray([r['goal_distance_m']for r in trace])
 scene.plot(*xy.T,color=color,label=name+(' (arrived)'if result['strict_safe_arrival']else' (not arrived)'));scene.plot(*xy[-1],'x',color=color)
 progress.plot(t,distance,color=color,label=name)
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
 clear.plot([r['time']for r in native],[r['actual_clearance_m']for r in native],color=color)
 estimates=[json.loads(s)for s in (cell/'motion_estimate.jsonl').read_text().splitlines()]
 width.plot([r['time']for r in estimates],[np.linalg.norm(np.asarray(r['position_upper'])-r['position_lower'])for r in estimates],color=color)
scene.set(xlim=(-3,2),ylim=(-4.7,4.7),aspect='equal',xlabel='x (m)',ylabel='y (m)',title='Same development task; actor diameter 0.20 m');scene.legend(fontsize=6.5,loc='lower left')
progress.axhline(.45,color='black',ls='--');progress.set(xlabel='Simulation time (s)',ylabel='Goal distance (m)',title='Progress and actual outcome');progress.legend(fontsize=7)
clear.axhline(.15,color='black',ls='--');clear.set(xlabel='Simulation time (s)',ylabel='Actual full-body clearance (m)',title='All native ticks; hard floor 0.15 m')
width.set(xlabel='Simulation time (s)',ylabel='Position interval diagonal (m)',title='Causal uncertainty; coverage checked separately')
for ax in axs.ravel():ax.grid(alpha=.2)
fig.suptitle('Dynamic development: covering uncertainty still requires a feasible execution strategy')
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for suffix in ['png','pdf']:fig.savefig(out/f'dynamic_interval_development.{suffix}',dpi=170)
print(out/'dynamic_interval_development.png')
