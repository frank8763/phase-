"""Standalone scientific development figure from finalized recorded evidence."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=Path(__file__).resolve().parents[2];out=repo/'docs/figures';out.mkdir(exist_ok=True)
base=repo/'runs/v659_dynamic_scene_repair/dev31_95000011_instant/paired'
pred=repo/'runs/v660_dynamic_audit_recovery/dev31_95000011_predictive/paired'
corrected=repo/'runs/v661_dynamic_corridor_consistency/dev32_95000011_predictive/paired'
def read(p):return json.loads(p.read_text())
p=read(base/'STATIC_PROTOCOL.json');c=read(base/'DYNAMIC_PROTOCOL.json');anchor=np.array(c['anchor_xy']);axis=np.array(c['axis_xy'])
fig=plt.figure(figsize=(12,7.3),layout='constrained');gs=fig.add_gridspec(2,3,width_ratios=[1.2,1.2,1])
ax=fig.add_subplot(gs[:,0]);zoom=fig.add_subplot(gs[0,1]);clear=fig.add_subplot(gs[1,1]);progress=fig.add_subplot(gs[:,2])
for a in [ax,zoom]:
 for x,y,hx,hy in p['known_rectangles']:a.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#475569',alpha=.7))
 for x,y,r in p['known_circles']:a.add_patch(Circle((x,y),r,color='#475569',alpha=.7))
 a.add_patch(Rectangle((-.8,-.8),1.6,1.6,facecolor='#f59e0b',edgecolor='#d97706',alpha=.18,label='Protected junction'))
 a.add_patch(Circle(anchor,.35,facecolor='#ef4444',edgecolor='#dc2626',alpha=.18,label='Full motion envelope'))
 ends=np.array([anchor-.25*axis,anchor+.25*axis]);a.plot(ends[:,0],ends[:,1],color='#dc2626',lw=2,label='Actor centre motion')
 a.add_patch(Circle(anchor,.1,color='#dc2626',alpha=.75))
 route=np.array(c['swept_envelope_reference']['reference_path']);a.plot(route[:,0],route[:,1],color='#94a3b8',ls=':',lw=1.5,label='Offline full-envelope bypass')
 a.plot(p['start_qpos'][0],p['start_qpos'][1],'o',color='black',ms=5);a.plot(*p['goal_xy'],'*',color='black',ms=11)
 a.set_aspect('equal');a.grid(alpha=.15);a.set_xlabel('x (m)');a.set_ylabel('y (m)')
colors={'instant':'#2563eb','predictive gate only':'#dc2626','consistent forecast route':'#16a34a'}
branches=[('instant',base),('predictive gate only',pred)]
if (corrected/'geometry_memory/result.json').exists():branches.append(('consistent forecast route',corrected))
for name,root in branches:
 cell=root/'geometry_memory';result=read(cell/'result.json');trace=read(cell/'trace.json');xy=np.array([r['pose'][:2]for r in trace]);t=np.array([r['physical_step']*.01 for r in trace]);goal=np.array([r['goal_distance_m']for r in trace])
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as stream:native=[json.loads(s)for s in stream]
 nt=np.array([r['time']for r in native]);nc=np.array([r['actual_clearance_m']for r in native])
 for a in [ax,zoom]:a.plot(xy[:,0],xy[:,1],color=colors[name],lw=1.7,label=f'{name} (not arrived)');a.plot(*xy[-1],marker='x',color=colors[name],ms=7)
 clear.plot(nt,nc,color=colors[name],label=name,lw=1.2)
 progress.plot(t,goal,color=colors[name],label=name,lw=1.5)
ax.set(xlim=(-5,5),ylim=(-5,5),title='Known map and recorded navigation')
ax.legend(fontsize=7,loc='upper left',bbox_to_anchor=(0,1.42))
zoom.set(xlim=(-2.4,.3),ylim=(.4,3.2),title='Interaction area (not a blocked junction)')
clear.axhline(.15,color='black',ls='--',lw=1,label='Native hard floor 0.15 m');clear.set(xlabel='Simulation time (s)',ylabel='Actual full-body clearance (m)',title='Native sampled safety');clear.grid(alpha=.2);clear.legend(fontsize=7)
progress.axhline(.45,color='black',ls='--',lw=1,label='Arrival radius 0.45 m');progress.set(xlabel='Simulation time (s)',ylabel='Distance to goal (m)',title='Same-task development outcome');progress.grid(alpha=.2);progress.legend(fontsize=8)
fig.suptitle('First dynamic unknown-obstacle development | actor diameter 0.20 m, amplitude 0.25 m, vmax 0.08 m/s',fontsize=12)
for suffix in ['png','pdf']:fig.savefig(out/f'dynamic_v660_development.{suffix}',dpi=180)
print(out/'dynamic_v660_development.png')
