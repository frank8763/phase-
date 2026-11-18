"""Separate terminal controllability, spatial feasibility, then finite timing."""
import sys,json,time,signal,hashlib,traceback,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1132_terminal_timing_split'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_PHYSICAL_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1131_final_section_restore'));from restore import Solver
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'));from timed_source import final_gate,initial,python_replay,COUNTS,REQUIRED
from source import Engine
from recovery_source import forecast_packet
import numpy as np
class BudgetEnd(Exception):pass

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(O/'DRIVER_STARTED.json').exists();start=time.monotonic();dump(O/'DRIVER_STARTED.json',{'pid':__import__('os').getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time()});dump(O/'ROUND_WINDOW.json',{'software_only':True,'root_limit_s':600,'started_unix':time.time(),'hard_stop_monotonic':start+600});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_ROOT600')));signal.alarm(600);freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());s=None;engine=None;err=None;best=None;phase_probes=[];backups=[];terminal_passed=False;final_source=False;model_error=None;exit=None
 try:
  task=json.loads((C/'TASK.json').read_text());x=json.loads((R/task['input']).read_text());x['safe_terminal_pose']=json.loads((R/task['terminal']).read_text())['selected_body_pose'];path=json.loads((R/task['path']).read_text());s=Solver(x,np.array(path['path']),path['gear']);z=np.array(json.loads((C/'WARM_START.json').read_text())['selected_z']);free=np.arange(36,48);u0=z[free].copy();target=np.array(x['safe_terminal_pose']);deadline=time.monotonic()+120;cache={}
  def evaluate(u):
   nonlocal best
   if s.calls>=1700 or time.monotonic()>deadline:raise BudgetEnd()
   k=np.asarray(u).tobytes()
   if k in cache:return cache[k]
   full=z.copy();full[free]=u;ss,uu,rows,events=s.simulate(full,reserved_final=True);delta=ss[-1,:2]-target[:2];yaw=float(np.arctan2(np.sin(ss[-1,2]-target[2]),np.cos(ss[-1,2]-target[2])));r=np.r_[delta/.025,yaw/.1,.001*(u-u0),.001*np.diff(u)];violation=max(0.,float(np.linalg.norm(delta))-.025,abs(yaw)-.1);rank=(violation,float(r@r))
   if best is None or rank<best['rank']:best={'rank':rank,'z':full.copy(),'terminal_distance_m':float(np.linalg.norm(delta)),'terminal_yaw_error_rad':abs(yaw)}
   cache[k]=r
   if len(cache)>64:cache.pop(next(iter(cache)))
   return r
  def jac(u):
   n=len(u);r=evaluate(u);j=np.empty((len(r),n))
   for i in range(n):
    a=u.copy();b=u.copy();a[i]=max(s.lower[free[i]],u[i]-.0001);b[i]=min(s.upper[free[i]],u[i]+.0001);j[:,i]=(evaluate(b)-evaluate(a))/(b[i]-a[i])
   return j
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.optimize import least_squares
  try:
   result=least_squares(evaluate,u0,jac=jac,bounds=(s.lower[free],s.upper[free]),max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9);exit={'status':int(result.status),'message':str(result.message),'nfev':int(result.nfev),'normal_deterministic_termination':True}
  except BudgetEnd:exit={'status':'SOFTWARE_BUDGET','normal_deterministic_termination':s.calls>=1700}
  assert best is not None;ss,uu,rows,events=s.simulate(best['z'],reserved_final=True);proof,_=final_gate(x,ss,uu,rows);terminal_passed=all(proof['checks'][k]for k in ['safe_terminal_position','safe_terminal_heading','terminal_full_cycle_hold','full2200tail','full_200_stop','legal_ctrl','legal_slew','speed_yaw','coupled_mode_envelopes','parked_ready']);diagnostic={'terminal_component_passed':terminal_passed,'full_source_passed':proof['passed'],'proof':proof,'selected_z':best['z'],'rows':rows,'fixed_last_duration_multiplier':float(z[51]),'free_last_angles':12,'optimizer_exit':exit,'optimizer_calls':s.calls,'optimizer_cpp_native':s.native,'scope':'Terminal-only least squares deliberately excludes path collisions in objective; full source gates reported separately and never bypassed'};dump(O/'TERMINAL_REACHABILITY.json',diagnostic)
  # Independent same full dynamics even for diagnostic-only candidates.
  ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);model_error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert model_error<=1e-8,'INDEPENDENT_MODEL_MISMATCH';np.savez_compressed(O/'TERMINAL_COMPONENT.npz',states=ps,controls=pu)
  engine=Engine(x['setup'])
  eligible=terminal_passed and proof['minimum_static_m']>=REQUIRED and bool(exit['normal_deterministic_termination']);dump(O/'TIMING_ELIGIBILITY.json',{'eligible':eligible,'static_lower_m':proof['minimum_static_m'],'required_m':REQUIRED,'reason':'Timing cannot repair static geometry; never sweep phases on spatially invalid source'})
  if eligible:
   for wait in json.loads((C/'TIMING_TICKS.json').read_text()):
    schedule=([(0.,0.,wait,0)]if wait else[])+rows;fs,fu=engine.simulate(initial(x['packet']),schedule);fp,_=final_gate(x,fs,fu,schedule);phase_probes.append({'initial_wait_native':wait,'passed':fp['passed'],'minimum_timed_raw_m':fp['minimum_timed_raw_m'],'minimum_static_m':fp['minimum_static_m'],'failed_checks':[k for k,v in fp['checks'].items()if not v]});dump(O/'TIMING_PROBES.json',phase_probes)
    if fp['passed']:
     final_source=True;rows=schedule;ss=fs;uu=fu;proof=fp;break
  if final_source:
   ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);model_error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert model_error<=1e-8,'TIMED_SOURCE_MODEL_MISMATCH';dump(O/'QUALIFIED_ROWS.json',rows)
   for i in range(0,len(pu)-2200,125):
    origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};bs,bu=engine.simulate(origin,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=final_gate(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'failed_checks':[k for k,v in bp['checks'].items()if not v]});dump(O/'BACKUPS.json',backups)
 except BaseException as e:err={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',err)
 finally:signal.alarm(0)
 counts={'optimizer_cpp_native':s.native if s else 0,'optimizer_partial_work_unknown':bool(s and s.in_call),'timing_and_backup_cpp_native':engine.native if engine else 0,'python_native':COUNTS['python_native']};answer={'closed':True,'passed':bool(final_source and backups and all(b['passed']for b in backups)and err is None),'terminal_component_passed':terminal_passed,'full_source_passed':final_source,'maximum_model_error':model_error,'timing_probes':len(phase_probes),'backup_count':len(backups),'counts':counts,'optimizer_exit':exit,'error':err,'wall_s':time.monotonic()-start,'models':0,'physical_integrations':0,'source_unchanged':all(sha(R/p)==h for p,h in freeze.items()),'no_physical_launch':True};dump(O/'COMPLETION.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
