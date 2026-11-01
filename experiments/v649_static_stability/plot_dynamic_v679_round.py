"""Figures from frozen logs only; zero simulation."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];read=lambda p:json.loads(p.read_text());base=repo/'runs/v679_dynamic_forward_reserve';early=read(base/'pre_navigation/COMPLETION.json');late=read(base/'later_stop_diagnostic/COMPLETION.json');fig,ax=plt.subplots(1,3,figsize=(14,4.2),layout='constrained')
x=np.arange(3);old=[];forward=[]
for row in early['records']:
 old.append(max(c['minimum_clearance_m']for c in row['original_attempt']['candidates']));forward.append(max(c['minimum_clearance_m']for c in row['new_attempt']['candidates']if c['kind']=='FORWARD_BRAKE'))
for shift,values,label,color in [(-.25,old,'Original stop/reverse','#767c84'),(0,forward,'Forward; brake at 1.6 s','#5083a5'),(.25,[r['minimum_causal_clearance_m']for r in late['records']],'Locked low-speed; brake at 2.4 s','#d18a43')]:ax[0].bar(x+shift,values,width=.24,label=label,color=color)
ax[0].axhline(.155,color='black',ls=':',label='Unchanged admission floor');ax[0].set(xticks=x,xticklabels=['217','227','686'],xlabel='Locked V676 decision',ylabel='Minimum predicted clearance (m)',title='One feasible private tail is insufficient');ax[0].legend(fontsize=6.7)
for folder,name,label,style,color in [('v676_dynamic_canonical_commands','dev43_95000011_canonical','V676 canonical','-','#767c84'),('v680_dynamic_later_stop_reserve','dev47_95000011_laterstop','V680 forward reserve','-','#5083a5'),('v677_dynamic_scene_witness','witness44_95000011_fullsweep','V677 privileged witness','--','#60945d')]:
 trace=read(repo/'runs'/folder/name/'paired/geometry_memory/trace.json');ax[1].plot([(r['step']+1)*.08 for r in trace],[r['goal_distance_m']for r in trace],style,label=label,color=color)
ax[1].axhline(.45,color='black',ls=':');ax[1].set(xlabel='Simulated time (s)',ylabel='Goal distance (m)',title='Causal navigation remains unsuccessful');ax[1].legend(fontsize=7)
v=read(repo/'runs/v681_dynamic_prefix_guidance/PRE_NAV_VALIDATION.json');colors=['#767c84','#d18a43'];y=[];labels=[]
for row in v['routes']:
 y.append(row['stats']['goal_distance_m']);labels.append(str(row['step'])+' '+('current'if row['role']=='CURRENT_ONLY'else'0.8 s'))
ax[2].bar(np.arange(4),y,color=colors*2);ax[2].set(xticks=np.arange(4),xticklabels=labels,ylabel='Geometric endpoint to goal (m)',title='Prefix projection rejected before navigation');ax[2].axhline(.28,color='black',ls=':');ax[2].text(3,y[-1]+.12,'Safe prefix only',ha='center',fontsize=7);ax[2].set_ylim(0,4.5)
for a in ax:a.grid(axis='y',alpha=.15)
fig.suptitle('V679–V681: measured increment, navigation failure, and a rejected route proposal',fontsize=12)
for ext in ['png','pdf']:fig.savefig(repo/f'docs/figures/dynamic_forward_reserve_v679.{ext}',dpi=180)
print(repo/'docs/figures/dynamic_forward_reserve_v679.png')
