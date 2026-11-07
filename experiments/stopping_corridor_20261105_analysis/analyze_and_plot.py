"""Saved-input diagnosis and scientific figure. No new control/path searches."""
import hashlib,importlib.abc,importlib.util,json,sys
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2]
class NoModels(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name=='mujoco'or name.startswith('mujoco.'):
            raise RuntimeError('SAVED_STOPPING_CORRIDOR_ANALYSIS_FORBIDS_MODELS')
sys.meta_path.insert(0,NoModels())
for p in ['runtime/mk-mini/experiments/phase_rpccr_p0b68_v1','experiments/v816_stopping_corridor_global']:
    sys.path.insert(0,str(repo/p))
from exact_footprint import build,pose_values
from independent_soft_reference import dense_path
from independent_time_reference import field as current_field
read=lambda p:json.loads(p.read_text())
root=repo/'runs/v815_stopping_corridor_qualification'
dest=repo/'runs/report_materials_v815_20261105';dest.mkdir(exist_ok=False)
protocol=read(repo/'runs/v812_soft_global_reference/main_slot01/paired/STATIC_PROTOCOL.json')
rows=read(root/'RESULTS.json');stats=[]
spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
oldpair=repo/'runs/v812_soft_global_reference/main_slot01/paired/geometry_memory'
component=read(repo/'runs/v814_stop_wait_entry_continuation/physical/RESULT.json')['records']
oldpaths=[read(oldpair/'planning_0303.json')['path'],read(oldpair/'planning_0375.json')['path'],component[0]['searches'][0]['path'],component[1]['searches'][0]['path']]
for r,p in zip(rows,oldpaths):
    old=np.asarray(p);dense=dense_path(old)
    f=build(F,r['corridor_world']);newvalues=f.pose_values(dense);current=pose_values(current_field(protocol,r['state']),dense)
    bad=np.flatnonzero(newvalues<.155-1e-8)
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(dense[:,:2],axis=0),axis=1))]
    stats.append(dict(label=r['label'],original_current_reference_nodes=len(old),original_reference_reverse_nodes=int(np.sum(old[:,3]<0)),
        old_reference_current_minimum_m=float(current.min()),old_reference_stopping_corridor_minimum_m=float(newvalues.min()),
        first_old_reference_point_below_stopping_gate=None if not len(bad)else dense[int(bad[0])].tolist(),
        first_old_reference_arc_below_stopping_gate_m=None if not len(bad)else float(arc[int(bad[0])]),
        old_reference_endpoint_clears_stopping_horizon=bool(newvalues[-1]>=.155),
        new_status=r['stats']['status'],new_endpoint_goal_m=r.get('endpoint_goal_m'),new_reverse_nodes=r.get('reverse_nodes'),
        fine_search_expansions=r['stats'].get('expanded'),fine_forward_search_expansions=r['stats']['spatial_soft_reference']['preferred_expanded'],
        explicit_search_budget_reached=bool(r['stats'].get('expanded')==16000),
        no_new_model=True,no_new_integrations=True,no_additional_path_search=True))
(dest/'SAVED_DIAGNOSIS.json').write_text(json.dumps(dict(status='FIXED_SAVED_REFERENCE_CONTRAST_COMPLETE',records=stats,models=0,integrations=0,
    no_general_infeasibility_claim=True,all_new_paths_are_geometric_proposals_not_executed=True),indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle
fig,axes=plt.subplots(1,2,figsize=(15,7),layout='constrained')
for ax,r,oldpath in zip(axes,rows[:2],oldpaths[:2]):
    for x,y,hx,hy in protocol['known_rectangles']:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,fc='#c3ccd5',ec='#657281',lw=.8))
    for x,y,rad in protocol['known_circles']:ax.add_patch(Circle((x,y),rad,fc='#c3ccd5',ec='#657281',lw=.8))
    sweeps=r['corridor_world']['rectangles'][11:]
    for x,y,hx,hy in sweeps:ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,fc='#ffb450',ec='#d77a14',alpha=.17,lw=.5))
    x,y,hx,hy=r['state']['current_outer_rectangle'];ax.add_patch(Rectangle((x-hx,y-hy),2*hx,2*hy,fc='#e66b48',ec='#b03822',alpha=.7,label='Current causal actor envelope'))
    p=np.asarray(oldpath);ax.plot(p[:,0],p[:,1],'--',color='#277abc',lw=2,label='Previous current-only reference')
    if r['path']is not None:
        p=np.asarray(r['path']);ax.plot(p[:,0],p[:,1],color='#00977c',lw=2.6,label='New stopping-corridor prefix')
        rev=p[:,3]<0
        if rev.any():ax.scatter(p[rev,0],p[rev,1],s=17,c='#bf46a9',zorder=5,label='Reverse nodes')
        ax.scatter(*p[-1,:2],marker='s',c='#00977c',s=50,zorder=6)
    ax.scatter(*np.asarray(r['start'])[:2],c='#212b36',s=55,zorder=6,label='Saved vehicle start')
    ax.scatter(*protocol['goal_xy'],marker='*',s=190,c='#e3a008',ec='#735300',zorder=7,label='Original goal')
    ax.set(xlim=(-.5,4.8),ylim=(-4.3,1.),xlabel='x (m)',ylabel='y (m)',aspect='equal')
    ax.grid(alpha=.15);ax.set_title(f"{r['label']}: {r['stats']['status']}\nremaining {r.get('endpoint_goal_m',float('nan')):.3f} m; reverse nodes {r.get('reverse_nodes',0)}")
axes[0].legend(loc='lower left',fontsize=8,framealpha=.94)
fig.suptitle('RP-CCR stopping-corridor qualification: NO PHYSICAL NAVIGATION\nOrange: same causal joint cells swept over original 3.28 s braking horizon',fontsize=13)
file=dest/'v815_stopping_corridor_qualification.png';fig.savefig(file,dpi=150);plt.close(fig)
provenance=dict(status='SAVED_GEOMETRY_AND_PROPOSED_REFERENCES_ONLY',sources=['runs/v815_stopping_corridor_qualification/RESULTS.json','runs/v812_soft_global_reference/main_slot01/paired/STATIC_PROTOCOL.json'],
    source_sha256={n:hashlib.sha256((repo/n).read_bytes()).hexdigest()for n in ['runs/v815_stopping_corridor_qualification/RESULTS.json','runs/v812_soft_global_reference/main_slot01/paired/STATIC_PROTOCOL.json']},
    image=str(file.relative_to(repo)),image_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),no_MuJoCo_render=True,new_models=0,new_integrations=0,not_success_video=True)
(dest/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps(dict(status='SAVED_DIAGNOSIS_AND_FIGURE_COMPLETE',records=stats,figure=str(file.relative_to(repo)),models=0,integrations=0)))
