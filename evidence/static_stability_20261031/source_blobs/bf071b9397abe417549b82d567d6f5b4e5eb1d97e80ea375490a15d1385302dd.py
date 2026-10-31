"""Offline benchmark geometry and recorded trajectories, never control inputs."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
p=argparse.ArgumentParser();p.add_argument('runs');p.add_argument('out');p.add_argument('names',nargs='+');a=p.parse_args();root=Path(a.runs);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
columns=min(2,len(a.names));rows=(len(a.names)+columns-1)//columns
fig,axes=plt.subplots(rows,columns,figsize=(5.3*columns,5.3*rows),squeeze=False)
for ax,name in zip(axes.flat,a.names):
    paired=root/name/'paired';protocol=json.loads((paired/'STATIC_PROTOCOL.json').read_text());cell=paired/('geometry_memory'if(paired/'geometry_memory/result.json').exists()else'range_memory');res=json.loads((cell/'result.json').read_text());trace=json.loads((cell/'trace.json').read_text())
    for x,y,hx,hy in protocol['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='.7'))
    for x,y,r in protocol['known_circles']:ax.add_patch(Circle((x,y),r,color='.7'))
    for i,u in enumerate(protocol['physical_unknown_obstacles']):ax.add_patch(Circle(u['xy'],u['radius'],color='#da674e',label='Unknown (evaluation truth)'if i==0 else None))
    ax.plot([x['pose'][0]for x in trace],[x['pose'][1]for x in trace],color='#2675ad',lw=2,label='Executed trajectory')
    start=protocol['start_qpos'];ax.plot(start[0],start[1],'o',color='k',label='Start');ax.plot(*protocol['goal_xy'],'*',color='#218d62',ms=12,label='Goal')
    transitions=cell/'gear_transitions.jsonl'
    if transitions.exists():
        entries=[json.loads(x)for x in transitions.read_text().splitlines()]
        for i,e in enumerate(entries):
            point=trace[max(0,e['step']-1)]['pose'];ax.plot(point[0],point[1],'x',color='#8d397e',ms=9,label='Stopped gear switch'if i==0 else None)
    ax.set(xlim=(-5,5),ylim=(-5,5),aspect='equal',xlabel='x (m)',ylabel='y (m)',title=f"Seed {protocol['seed']} / {protocol['scene']}\n{res['outcome']}; contacts={res['contacts']['robot_obstacle_contact_records']}")
    ax.grid(alpha=.2);ax.legend(fontsize=7,loc='lower left')
for ax in list(axes.flat)[len(a.names):]:ax.set_visible(False)
fig.suptitle('Development trials: static unknown cylinders (not held-out confirmation)',fontsize=12);fig.tight_layout()
fig.savefig(out/'development_trajectories.png',dpi=160);fig.savefig(out/'development_trajectories.svg')
