"""Plot five completed actual trajectories, without model construction."""
import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
repo=Path(__file__).resolve().parents[2];root=repo/'runs/v805_static_five_continuation';read=lambda p:json.loads(p.read_text());s=read(root/'FINAL_INDEPENDENT_AUDIT.json');assert s['completed'];out=repo/'runs/v805_five_static_plots';assert not out.exists();out.mkdir();fig,axes=plt.subplots(2,3,figsize=(16,10));colors=['#246db5','#dd7744','#4d965b','#a76ab1','#c4a029'];comparison=[]
for i,row in enumerate(s['rows']):
 pair=(repo/'runs/v804_no_dynamic_static_contact'/row['name']/'paired')if row['name']=='round01'else root/row['name']/'paired';p=read(pair/'STATIC_PROTOCOL.json');cell=pair/'geometry_memory';ex=list(map(json.loads,(cell/'v648_execution.jsonl').read_text().splitlines()));xy=np.asarray([x['qpos_full'][:2]for x in ex]);plan=np.asarray(read(cell/'planning_0000.json')['path']);ax=axes.flat[i]
 for x,y,hx,hy in p['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#899da8',alpha=.85))
 for x,y,r in p['known_circles']:ax.add_patch(Circle((x,y),r,color='#899da8',alpha=.85))
 ax.plot(plan[:,0],plan[:,1],'--',c='#49a561',lw=2,label='Original A*');ax.plot(xy[:,0],xy[:,1],c=colors[i],lw=2.5,label='Actual');ax.plot(*p['start_qpos'][:2],'ks',ms=5);ax.plot(*p['goal_xy'],'*',c='#e5b632',ms=13);ax.plot(*xy[-1],'o',c=colors[i],ms=4);ax.set(xlim=(-5.5,5.5),ylim=(-5.5,5.5),xlabel='x (m)',ylabel='y (m)');ax.set_aspect('equal');ax.grid(alpha=.2);m=row['metrics'];ax.set_title(f"{row['name']} / seed {row['seed']} / {'REACHED'if row['strict_static_success']else row['outcome']}\nremaining {m['goal_remaining_m']:.3f}m, max contour {m['max_native_contour_m']:.4f}m");ax.legend(loc='upper right',fontsize=8)
 if i:
  base=comparison[0]['execution'];equal_length=len(ex)==len(base);errors={k:float(np.max(abs(np.asarray([x[k]for x in ex])-np.asarray([x[k]for x in base]))))if equal_length else None for k in ['qpos_full','qvel_full','ctrl']};comparison.append(dict(round=row['name'],execution=ex,equal_length=equal_length,errors=errors))
 else:comparison.append(dict(round=row['name'],execution=ex,equal_length=True,errors={k:0. for k in ['qpos_full','qvel_full','ctrl']}))
ax=axes.flat[-1];ax.axis('off');text=['Known-static full-field path tracking',f"Audited reaches: {s['successes']} / 5",'Same map and route; five noise seeds','No dynamic actor / no unknown-motion prior','Original planner/controller and static gates','Not dynamic acceptance or map generalization','',f"Actual native: {s['navigation_native']}",f"Private native: {s['private_native']}",f"Replay native: {s['replay_native']}"]
ax.text(.02,.95,'\n'.join(text),va='top',fontsize=12,linespacing=1.7);fig.suptitle('Five prelocked no-dynamic navigation rounds | Actual saved trajectories',fontsize=17);fig.tight_layout(rect=(0,0,1,.95));fig.savefig(out/'five_actual_routes.png',dpi=160);plt.close(fig)
for x in comparison:x.pop('execution')
(out/'CROSS_ROUND_VEHICLE_TRACE_COMPARISON.json').write_text(json.dumps(dict(scope='same static route and declared measurement noise seeds; exact traces are repetitions, not five maps',rows=comparison,new_models=0,new_integrations=0),indent=2)+'\n');print(str(out/'five_actual_routes.png'))
