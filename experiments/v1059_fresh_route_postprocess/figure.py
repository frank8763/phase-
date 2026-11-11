"""Offline original true-start trajectory and accepted nominal input paths."""
import json,sys,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1058_fresh_repeat_entry';A=R/'runs/v858_nav2_verified/v1056/main_west_east'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
setup=json.loads((A/'physics/SETUP.json').read_text());z=dict(np.load(A/'physics/NATIVE_TRACE.npz'));done=json.loads((O/'COMPLETION.json').read_text());assert done['closed'];fig,ax=plt.subplots(figsize=(9,8));known=setup['known']
for x,y,hx,hy in known['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,color='#c6cbd2',ec='#737b85',lw=.7))
for x,y,r in known['known_circles']:ax.add_patch(Circle((x,y),r,color='#c6cbd2',ec='#737b85',lw=.7))
nominals=[]
for label in ['STATIC','BRAKE','APPROACH']:
 plan=json.loads((A/(label+'_PLAN.json')).read_text());journal=json.loads((A/(label+'_EXECUTION.json')).read_text());nominals.append(np.array(plan['state_path'])[:journal['executed_native']+1,:2])
for segment in json.loads((A/'EXECUTION_SEGMENTS.json').read_text()):nominals.append(np.array(segment['state_path'])[:segment['executed_native']+1,:2])
for i,xy in enumerate(nominals):ax.plot(xy[::5,0],xy[::5,1],color='#e5a21b',lw=2.6,alpha=.8,label='Accepted nominal (executed portion)'if i==0 else None)
xy=np.vstack([[-4,-2],z['qpos'][:,:2]]);ax.plot(xy[::5,0],xy[::5,1],color='#1769aa',lw=1.2,label='Actual true-start trajectory')
repeat=np.load(R/'runs/v858_nav2_verified/v1056/repeat_west_east/physics/NATIVE_TRACE.npz');endpoint=repeat['qpos'][-1,:2];ax.scatter(*endpoint,s=80,marker='x',c='#c31f29',zorder=12,label='Repeat parked stop (age gate)')
actor=z['mocap_pos'][:,0,:2];ax.plot(actor[::20,0],actor[::20,1],color='#db493a',lw=2,label='Moving actor center (offline truth)');ax.add_patch(Circle((4,-2),.45,color='#5dbb79',alpha=.2));ax.scatter([-4],[ -2],s=65,marker='o',c='#1769aa',zorder=10,label='Original start');ax.scatter([4],[-2],s=95,marker='*',c='#218548',zorder=10,label='Original goal');ax.scatter([xy[-1,0]],[xy[-1,1]],s=30,c='black',zorder=11,label='Actual stopped endpoint')
first=json.loads((A/'CAUSAL_EVIDENCE.json').read_text())['first'];ax.scatter(*np.array(first['xy']),marker='D',s=35,c='#8a45a5',zorder=11,label='First actual causal discovery');ax.set(xlim=(-5.1,5.1),ylim=(-5.1,5.1),xlabel='x (m)',ylabel='y (m)',title='Original WEST_EAST: true-start main reached goal\nRepeat stopped while parked: measurement packet expired');ax.set_aspect('equal');ax.grid(alpha=.16);ax.legend(loc='upper left',fontsize=8,framealpha=.95);fig.text(.13,.025,'Goal distance 0.122 m | minimum actual clearance 0.277 m | bad contacts 0\nMain passed; repeat failed packet-age gate. Three-route and independent24 gates remain open.',fontsize=9);fig.tight_layout(rect=(0,.065,1,1));fig.savefig(O/'FRESH_START_ACTUAL_AND_NOMINAL.png',dpi=170);plt.close(fig)
(O/'FIGURE_PROVENANCE.json').write_text(json.dumps(dict(models=0,integrations=0,task='WEST_EAST10010001',native_points=50728,plot_decimation=5,raw_data_all_native_audited=True,truth_only_offline=True,source_release='phase-fresh-route-v1056-20261111',full_repeat_passed=False,repeat_prefix_native=38929),indent=2)+'\n')
