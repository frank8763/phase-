"""Saved synthetic original/PhaseG2 paths only; no query, model or physical audit."""
import os
os.sched_setaffinity(0,{4})
import hashlib,importlib.util,json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
os.environ['MPLCONFIGDIR']=str(O/'mpl_cache')
def main():
 assert os.sched_getaffinity(0)=={4};(O/'mpl_cache').mkdir(exist_ok=True)
 sp=importlib.util.spec_from_file_location('v1762_plot_guard',R/'experiments/v1504_priest_namespace_worker/common.py');guard=importlib.util.module_from_spec(sp);sp.loader.exec_module(guard);guard.guard(O)
 read=lambda p:json.loads(p.read_text());old=read(R/'runs/v1754_sccr_numpy_dependency/ORIGINAL_QUERY_RESPONSE.json');new=read(O/'ADAPTED_QUERY_RESPONSE.json');account=read(O/'ADAPTED_SEARCH_ACCOUNTING.json')
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
 oldp=old['selected_path'];axes[0].plot([p[0]for p in oldp],[p[1]for p in oldp],c='#d97706',lw=1.3,label='Original core (saved prior result)')
 if new['candidate_found']:
  p=new['selected_path'];axes[0].plot([v[0]for v in p],[v[1]for v in p],c='#2563eb',lw=1.4,label='SCCR-PhaseG2 (new query)');axes[0].set_ylim(min(min(v[1]for v in p),min(v[1]for v in oldp))-.15,.25)
 else:axes[0].text(.5,.05,'No PhaseG2-admissible candidate',transform=axes[0].transAxes,ha='center',color='#991b1b')
 axes[0].set(xlim=(-.1,6.1),xlabel='x (m)',ylabel='y (m)',title='Same exposed synthetic input');axes[0].legend(fontsize=8);axes[0].grid(alpha=.2)
 rows=account['candidate_rows'];x=[v['index']for v in rows];y=[math.degrees(v['phase_gate']['max_abs_sampled_center_steering_rad'])for v in rows];axes[1].scatter(x,y,s=5,alpha=.45,c='#94a3b8',label='All non-null adapted candidates')
 eligible=[v for v in rows if v['original_geometric_feasible']and v['phase_gate']['passed']]
 if eligible:axes[1].scatter([v['index']for v in eligible],[math.degrees(v['phase_gate']['max_abs_sampled_center_steering_rad'])for v in eligible],s=10,c='#2563eb',label='Pass original + Phase gates')
 axes[1].axhline(math.degrees(.42722137342572125),ls='--',c='#dc2626',lw=1,label='Original Phase steering cap');axes[1].set(xlabel='Registered finite candidate evaluation',ylabel='Max sampled steering (deg)',title=f"{account['phase_feasible']} / {account['evaluations']} Phase-feasible candidates");axes[1].grid(alpha=.2);axes[1].legend(fontsize=7)
 fig.suptitle('SCCR-PhaseG2 component only — new adaptation; no vehicle or navigation test',fontsize=11);fig.savefig(O/'phase_g2_comparison.png',dpi=180);fig.savefig(O/'phase_g2_comparison.pdf');plt.close(fig)
 print(json.dumps(dict(saved_data_plot_only=True,models=0,planner_calls=0,physical_native=0)))
if __name__=='__main__':main()
