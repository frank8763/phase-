"""One cold timed safe-terminal source; full independent replay and stops."""
import sys,json,time,hashlib,signal,traceback,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1128_timed_terminal_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from timed_source import Solver,final_gate,initial,python_replay,COUNTS,REQUIRED,ref
from source import Engine,deterministic_admission
from recovery_source import forecast_packet
import numpy as np

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(O/'COMPLETION.json').exists();start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_ROOT600')));signal.alarm(600);dump(O/'ROUND_WINDOW.json',{'software_only':True,'started_unix':time.time(),'hard_stop_monotonic':start+600,'root_limit_s':600,'does_not_extend_old_window':True});freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];error=None;proof=None;backups=[];solver=None;engine=None;model_error=None;calls=0;work0=0
 try:
  task=json.loads((C/'TASK.json').read_text());x=json.loads((R/task['input']).read_text());selection=json.loads((R/task['terminal']).read_text());x['safe_terminal_pose']=selection['selected_body_pose'];path=json.loads((R/task['path']).read_text());solver=Solver(x,np.array(path['path']),path['gear']);best,iterations=solver.solve();ss,uu,rows,events=solver.simulate(best['z'],reserved_final=True);proof,requests=final_gate(x,ss,uu,rows);proof['checks']['registered_initial_mode_headroom']=all(m['raw_envelope_lower']>=REQUIRED+x['mode_reserve']-1e-10 for m in proof['mode_envelopes']);proof['checks']['deterministic_work_or_feasible']=deterministic_admission(solver.optimizer_exit,solver.calls);proof['passed']=bool(all(proof['checks'].values()));result={'passed':proof['passed'],'proof':proof,'rows':rows,'selected_z':best['z'].tolist(),'constraints':best['constraints'],'optimizer_exit':solver.optimizer_exit,'optimizer_calls':solver.calls,'optimizer_cpp_native':solver.native,'iterations':iterations};dump(O/'OPTIMIZATION.json',result)
  if proof['passed']:
   ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);model_error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));independent,_=final_gate(x,ps,pu,rows);assert model_error<=1e-8 and independent['passed'],'INDEPENDENT_FULL_SOURCE_FAILURE';np.savez_compressed(O/'QUALIFIED_SOURCE.npz',states=ps,controls=pu,requests=requests);engine=Engine(x['setup'])
   for i in range(0,len(pu)-2200,125):
    state={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};bs,bu=engine.simulate(state,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));sx=dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist());bp,_=final_gate(sx,bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'minimum_timed_raw_m':bp['minimum_timed_raw_m'],'terminal_full_cycle_raw_m':bp['terminal_full_cycle_raw_m'],'failed_checks':[k for k,v in bp['checks'].items()if not v]});dump(O/'BACKUPS.json',backups)
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',error)
 finally:signal.alarm(0)
 counts={'optimizer_cpp_native':solver.native if solver else 0,'optimizer_partial_work_unknown':bool(solver and solver.in_call),'backup_cpp_native':engine.native if engine else 0,'python_native':COUNTS['python_native']};answer={'closed':True,'passed':bool(proof and proof['passed']and model_error is not None and backups and all(b['passed']for b in backups)),'complete_source_passed':bool(proof and proof['passed']and model_error is not None),'proof':proof,'maximum_model_error':model_error,'backup_count':len(backups),'all_backups_passed':bool(backups and all(b['passed']for b in backups)),'counts':counts,'error':error,'wall_s':time.monotonic()-start,'models':0,'physical_integrations':0,'source_unchanged':all(sha(R/p)==h for p,h in freeze.items()),'no_physical_launch':True};dump(O/'COMPLETION.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
