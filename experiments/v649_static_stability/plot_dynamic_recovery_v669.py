"""Finalized recorded evidence only; standalone scientific figure."""
import gzip,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
repo=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
roots=[('Dense search edges',repo/'runs/v666_dynamic_dense_navigation/dev35_95000011_dense/paired','#2563eb'),('First-hit constraints',repo/'runs/v667_dynamic_first_hit/dev36_95000011_firsthit/paired','#dc2626'),('Retained recovery tail',repo/'runs/v669_dynamic_reserved_recovery/dev37_95000011_reserve/paired','#16a34a')]
p=read(roots[-1][1]/'STATIC_PROTOCOL.json');c=read(roots[-1][1]/'DYNAMIC_PROTOCOL.json')
fig,axes=plt.subplots(2,2,figsize=(12,8.5),layout='constrained');scene,goal,clear,belief=axes.ravel()
for x,y,hx,hy in p['known_rectangles']:scene.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#475569',alpha=.65))
for x,y,r in p['known_circles']:scene.add_patch(Circle((x,y),r,color='#475569',alpha=.65))
scene.add_patch(Circle(c['anchor_xy'],.35,color='#ef4444',alpha=.18,label='Full actor sweep'))
reference=np.asarray(c['swept_envelope_reference']['reference_path']);scene.plot(*reference[:,:2].T,':',color='#64748b',label='Offline full-sweep bypass')
for label,root,color in roots:
 cell=root/'geometry_memory';t=read(cell/'trace.json');xy=np.asarray([r['pose'][:2]for r in t]);time=np.asarray([r['physical_step']*.01 for r in t])
 scene.plot(*xy.T,color=color,lw=1.6,label=label+' (not arrived)');scene.plot(*xy[-1],'x',color=color,ms=7)
 goal.plot(time,[r['goal_distance_m']for r in t],color=color,label=label,lw=1.5)
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
 clear.plot([r['time']for r in native],[r['actual_clearance_m']for r in native],color=color,lw=1.4)
cell=roots[-1][1]/'geometry_memory';motion=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()]
belief.plot([r['time']for r in motion],[np.prod(np.asarray(r['position_upper'])-r['position_lower'])for r in motion],color='#16a34a',label='Position interval area')
sensor=belief.twinx();sensor.scatter([r['time']for r in motion],[r['certified_unknown_rays']for r in motion],s=8,color='#64748b',alpha=.5,label='Certified unknown rays');sensor.set_ylabel('Valid unknown returns per decision',color='#64748b')
with gzip.open(next((cell/'recovery_contracts').glob('*.gz')),'rt')as f:contract=json.load(f)
begin=contract['start_time'];end=begin+3.2
for ax in [goal,clear,belief]:ax.axvspan(begin,end,color='#a855f7',alpha=.12,label='Executed recovery tail (3.2 s)')
trace=read(cell/'trace.json')
for step,color in [(contract['activation_step']-1,'#a855f7'),(contract['activation_step']+39,'#059669')]:
 pose=np.asarray(trace[step]['pose']);b=np.asarray(p['footprint_bounds']);local=np.array([[b[0],b[1]],[b[2],b[1]],[b[2],b[3]],[b[0],b[3]]]);co,si=np.cos(pose[2]),np.sin(pose[2]);corners=local@np.array([[co,si],[-si,co]])+pose[:2]
 scene.add_patch(Polygon(corners,facecolor=color,edgecolor=color,alpha=.22))
scene.set(xlim=(-2.8,.4),ylim=(.4,4.3),aspect='equal',xlabel='x (m)',ylabel='y (m)',title='Interaction area; goal y = -2.959 m is below this zoom')
scene.legend(fontsize=7,loc='lower left')
goal.axhline(.45,color='black',ls='--',lw=1);goal.set(xlabel='Simulation time (s)',ylabel='Goal distance (m)',title='All three development branches did not arrive');goal.legend(fontsize=7,loc='lower right')
clear.axhline(.15,color='black',ls='--',lw=1);clear.set(xlabel='Simulation time (s)',ylabel='Actual full-body clearance (m)',title='All native ticks; hard floor 0.15 m')
belief.set(xlabel='Simulation time (s)',ylabel='Position interval area (m²)',title='Safe stopping did not renew sufficient observation');belief.legend(fontsize=7,loc='upper left')
for ax in axes.ravel():ax.grid(alpha=.2)
fig.suptitle('Dynamic unknown obstacle | diameter 0.20 m, amplitude 0.25 m, vmax 0.08 m/s | development only',fontsize=12)
out=repo/'docs/figures';out.mkdir(exist_ok=True)
for suffix in ['png','pdf']:fig.savefig(out/f'dynamic_recovery_v669.{suffix}',dpi=180)
print(out/'dynamic_recovery_v669.png')
