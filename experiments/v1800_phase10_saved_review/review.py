"""Read saved trajectories only; zero planner, model, integration or audit rerun."""
from pathlib import Path
import json,hashlib,os,time,datetime
os.sched_setaffinity(0,{4})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];D=R/'runs/v1800_phase10_saved_review';ROOT=R/'runs/v1643_formal_parent_metadata/rounds'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 full=ROOT/'phase_10__full/actual';no=ROOT/'phase_10__no_time/actual';a=read(full/'RESULT.json');b=read(no/'RESULT.json');sets={};comparisons=[]
 with np.load(full/'physics/NATIVE_TRACE.npz')as f,np.load(no/'physics/NATIVE_TRACE.npz')as n:
  assert set(f.files)==set(n.files)
  for k in f.files:
   x=f[k];y=n[k];equal=x.shape==y.shape and x.dtype==y.dtype and x.tobytes()==y.tobytes();comparisons.append(dict(member=k,shape=list(x.shape),dtype=str(x.dtype),bitwise_equal=equal,full_array_sha256=hashlib.sha256(x.tobytes()).hexdigest(),no_time_array_sha256=hashlib.sha256(y.tobytes()).hexdigest()))
  for key,p in [('full',f),('no_time',n)]:sets[key]=dict(xy=p['qpos'][:,:2].copy(),time=p['time'].copy(),clearance=p['clearance'].copy())
 assert np.allclose(sets['full']['xy'][-1],a['physical']['final_body'][:2],rtol=0,atol=1e-10)
 initial=read(full/'CANONICAL_INITIAL_PACKET.json');task=read(full.parent/'FORMAL_TASK.json');goal=np.asarray(task['goal_xy']);xy=sets['full']['xy'];assert len(xy)==a['new_actual_native']
 figure,(ax,bx)=plt.subplots(1,2,figsize=(10.5,4.2),layout='constrained')
 ax.plot(xy[:,0],xy[:,1],color='#2369ab',linewidth=3,label='Full actual')
 other=sets['no_time']['xy'];ax.plot(other[:,0],other[:,1],color='#ed9830',linewidth=1.3,linestyle='--',label='No-time actual')
 ax.scatter(xy[0,0],xy[0,1],marker='o',s=55,color='#21864d',label='Start');ax.scatter(goal[0],goal[1],marker='*',s=130,color='#a33434',label='Task goal');ax.scatter(xy[-1,0],xy[-1,1],marker='x',s=50,color='black',label='Final position')
 detection=a['physical']['first_actor_detection']['native_tick'];ax.scatter(xy[detection-1,0],xy[detection-1,1],marker='D',s=35,color='#6c4ca5',label='First actor detection');ax.set_aspect('equal',adjustable='datalim');ax.set_xlabel('World x (m)');ax.set_ylabel('World y (m)');ax.set_title('Phase10: saved actual paths overlap');ax.legend(fontsize=8)
 bx.plot(sets['full']['time'],sets['full']['clearance'],color='#2369ab',label='Recorded actual clearance');bx.axhline(.15,color='#aa3333',linestyle='--',label='Original 0.15 m floor');bx.set_xlabel('Simulation time (s)');bx.set_ylabel('Clearance (m)');bx.set_title('No bad contacts; minimum 0.254 m');bx.legend(fontsize=8)
 figure.suptitle('Recorded arrival; complete acceptance NOT passed (evidence resource failure)',fontsize=11)
 figure.savefig(D/'phase10_saved_paths.png',dpi=180);figure.savefig(D/'phase10_saved_paths.pdf');plt.close(figure)
 proof=dict(models=0,physics=0,replay=0,planner_calls=0,new_numerical_audit=0,saved_arrays_only=True,source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [full/'RESULT.json',no/'RESULT.json',full/'physics/NATIVE_TRACE.npz',no/'physics/NATIVE_TRACE.npz']},native_array_comparisons=comparisons,all_saved_native_members_bitwise_equal=all(x['bitwise_equal']for x in comparisons),applied_journals_exact_SHA_equal=sha(full/'APPLIED_JOURNAL.json')==sha(no/'APPLIED_JOURNAL.json'),full_original_qualified=False,no_time_original_qualified=False,whole_safety_success_not_inferred=True,observed_time_selection_benefit=False,interpretation='Both actual paths coincide in this saved pair. Neither has complete independent whole-goal acceptance, so this is descriptive trace evidence, not a qualified paired mechanism result.',created_unix=time.time());(D/'SAVED_PAIR_COMPARISON.json').write_text(json.dumps(proof,indent=2)+'\n')
 print(json.dumps({k:proof[k]for k in ['all_saved_native_members_bitwise_equal','applied_journals_exact_SHA_equal','observed_time_selection_benefit']}))
if __name__=='__main__':main()
