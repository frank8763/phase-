"""Joint final-section steering and explicit initial hold, exact full propagation."""
import sys,json,time,signal,hashlib,traceback,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];JOB=json.loads(Path(sys.argv[1]).read_text())if len(sys.argv)>1 else None;O=Path(JOB['output'])if JOB else R/'runs/v1135_causal_batch/worker_entry_check'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'));from timed_source import Solver
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'));from timed_source import Timed,ref,REQUIRED,initial,python_replay,final_gate,COUNTS
from source import Engine
sys.path.insert(0,str(C))
from geometry import Geometry,pg
import types
from recovery_source import forecast_packet
import numpy as np
class BudgetEnd(Exception):pass
class FeasibleFound(Exception):pass

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def schedule(s,z,u,factor=1.):
 z=z.copy();z[36:48]=u[:12];rows,events=s.schedule(z);assert rows[:41]==s.prefix_rows,'PREFIX_COMMAND_CHANGED';assert factor in [1.,1.25,1.5]
 if factor!=1.:
  rows=[(t,v*factor,max(1,int(round(n/factor))),m)if i>=42 and v>0 else(t,v,n,m)for i,(t,v,n,m)in enumerate(rows)];begin=events[-1][0];moving=begin+sum(r[2]for r in rows[42:54]);events[-1]=(begin,moving,moving+2200)
 assert max(v for t,v,n,m in rows)<=.12+1e-12;wait=int(round(float(u[12])*100));assert 0<=wait<=1963;return ([(0.,0.,wait,0)]if wait else[])+rows,wait,events

def group_min(values,bins=64):
 ix=np.minimum(np.arange(len(values))*bins//len(values),bins-1);v=np.full(bins,np.inf);np.minimum.at(v,ix,values);return v

def main():
 assert not(O/'DRIVER_STARTED.json').exists();start=time.monotonic();dump(O/'DRIVER_STARTED.json',{'pid':__import__('os').getpid(),'proc_start':Path('/proc/self/stat').read_text().split()[21],'started_unix':time.time()});dump(O/'ROUND_WINDOW.json',{'software_only':True,'root_limit_s':600,'started_unix':time.time(),'hard_stop_monotonic':start+600});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('SOFTWARE_ROOT600')));signal.alarm(600);freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items());engine=None;best=None;error=None;backups=[];err=None;calls=0;exit=None;source_passed=False;model_error=None
 try:
  task=json.loads((C/'TASK.json').read_text());x=json.loads((R/task['input']).read_text());x['safe_terminal_pose']=json.loads((R/task['terminal']).read_text())['selected_body_pose'];path=json.loads((R/task['path']).read_text());s=Solver(x,np.array(path['path']),path['gear']);z=np.array(json.loads((R/'runs/v1133_terminal_spatial_corridor/TERMINAL_REACHABILITY.json').read_text())['selected_z'])if JOB['seed']=='saved'else s.seed();s.prefix_rows=s.schedule(z)[0][:41];speed_factor=float(JOB['speed_factor']);u0=np.r_[z[36:48],float(JOB['wait_seconds'])];lower=np.r_[s.lower[36:48],0.];upper=np.r_[s.upper[36:48],19.63];engine=Engine(x['setup']);assert sha(Path(JOB['table']))==JOB['table_sha256'],'CAUSAL_TABLE_SHA_CHANGED';table_data=np.load(JOB['table']);table={k:table_data[k]for k in ['bounds','centers']};timed=Geometry(x,table);cycle=types.SimpleNamespace(clearances=lambda p:(timed.static.clearances(p)[0],pg.distances(np.asarray(p),timed.cycle_polygon)-.1-2e-6));target=np.array(x['safe_terminal_pose']);deadline=time.monotonic()+120;cache={}
  def evaluate(u):
   nonlocal calls,best
   if calls>=1700 or time.monotonic()>deadline:raise BudgetEnd()
   rows,wait,events=schedule(s,z,u,speed_factor);key=(np.asarray(u[:12]).tobytes(),wait)
   if key in cache:return cache[key]
   ss,uu=engine.simulate(initial(x['packet']),rows);calls+=1;a,b=timed.components(ss[:,:3],np.arange(len(ss)));static=group_min(a);dynamic=group_min(b);p=ss[wait+9388:,:3];rect=x['setup']['known']['known_rectangles'][9];face=p[:,1]-.44*abs(np.sin(p[:,2]))-.375*abs(np.cos(p[:,2]))-(rect[1]+rect[3]);face=group_min(face);delta=ss[-1,:2]-target[:2];yaw=float(np.arctan2(np.sin(ss[-1,2]-target[2]),np.cos(ss[-1,2]-target[2])));st,dy=cycle.clearances(ss[-1:,:3]);terminal_cycle=float(min(st[0],dy[0]));mode=[]
   for begin,moving,end in events[1:]:
    st,dy=cycle.clearances(ss[wait+begin-600:wait+begin-599,:3]);mode.append(float(min(st[0],dy[0]))-.02-np.hypot(.44,.375)*.1)
   r=np.r_[delta/.025,yaw/.1,.001*(u[:12]-u0[:12]),.001*np.diff(u[:12]),np.maximum(0.,REQUIRED+.001-static)/(.01*8),np.maximum(0.,REQUIRED+.001-dynamic)/(.01*8),np.maximum(0.,REQUIRED+.001-face)/(.01*8),np.maximum(0.,REQUIRED+x['mode_reserve']-np.array(mode))/.01,max(0.,REQUIRED+.001-terminal_cycle)/.01];violation=max(0.,float(np.linalg.norm(delta))-.025,abs(yaw)-.1,REQUIRED+.001-float(a.min()),REQUIRED+.001-float(b.min()),REQUIRED+.001-terminal_cycle);rank=(violation,float(r@r));report={'u':u.copy(),'rows':rows,'initial_wait_native':wait,'minimum_static_m':float(a.min()),'minimum_timed_dynamic_m':float(b.min()),'terminal_distance_m':float(np.linalg.norm(delta)),'terminal_yaw_error_rad':abs(yaw),'terminal_full_cycle_m':terminal_cycle,'rank':rank}
   if best is None or rank<best['rank']:best=report;dump(O/'PROGRESS.json',{k:v for k,v in report.items()if k not in ['rows','u']}|{'calls':calls,'optimizer_cpp_native':engine.native})
   cache[key]=r
   if len(cache)>64:cache.pop(next(iter(cache)))
   if a.min()>=REQUIRED and b.min()>=REQUIRED and np.linalg.norm(delta)<=.025 and abs(yaw)<=.1 and terminal_cycle>=REQUIRED:
    proof,_=timed.final(x,ss,uu,rows)
    if proof['passed']:best=report;raise FeasibleFound()
   return r
  def jac(u):
   f=evaluate(u);j=np.empty((len(f),13))
   for i in range(13):
    step=.0001 if i<12 else .10;left=u.copy();right=u.copy();left[i]=max(lower[i],u[i]-step);right[i]=min(upper[i],u[i]+step);j[:,i]=(evaluate(right)-evaluate(left))/(right[i]-left[i])
   return j
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.optimize import least_squares
  try:
   result=least_squares(evaluate,u0,jac=jac,bounds=(lower,upper),max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9);exit={'status':int(result.status),'message':str(result.message),'nfev':int(result.nfev),'deterministic':True}
  except FeasibleFound:exit={'status':'FULL_SOURCE_FEASIBLE','deterministic':True}
  except BudgetEnd:exit={'status':'SOFTWARE_BUDGET','deterministic':calls>=1700}
  assert best is not None;rows=best['rows'];ss,uu=engine.simulate(initial(x['packet']),rows);proof,_=timed.final(x,ss,uu,rows);proof['checks']['deterministic_work_or_feasible']=exit['deterministic'];proof['checks']['registered_initial_mode_headroom']=all(m['raw_envelope_lower']>=REQUIRED+x['mode_reserve']-1e-10 for m in proof['mode_envelopes']);proof['passed']=bool(all(proof['checks'].values()));source_passed=proof['passed'];dump(O/'OPTIMIZATION.json',{k:v for k,v in best.items()}|{'proof':proof,'calls':calls,'optimizer_exit':exit,'optimizer_cpp_native':engine.native});np.savez_compressed(O/'SELECTED_SOURCE.npz',states=ss,controls=uu)
  ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);model_error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert model_error<=1e-8,'INDEPENDENT_MODEL_MISMATCH'
  if source_passed:
   for i in range(0,len(pu)-2200,125):
    origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};bs,bu=engine.simulate(origin,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=timed.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'failed_checks':[k for k,v in bp['checks'].items()if not v]});dump(O/'BACKUPS.json',backups)
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',error)
 finally:signal.alarm(0)
 answer={'closed':True,'passed':bool(source_passed and backups and all(b['passed']for b in backups)and error is None),'full_source_passed':source_passed,'optimizer_exit':exit,'optimizer_calls':calls,'best':{k:v for k,v in best.items()if k not in ['rows','u']}if best else None,'maximum_model_error':model_error,'backup_count':len(backups),'counts':{'analytical_cpp_native':engine.native if engine else 0,'cpp_inflight_work_unknown':bool(engine and getattr(engine,'in_call',False)),'independent_python_native':COUNTS['python_native']},'error':error,'wall_s':time.monotonic()-start,'models':0,'physical_integrations':0,'source_unchanged':all(sha(R/p)==h for p,h in freeze.items()),'no_physical_launch':True,'profile':JOB['id'],'seed_scope':JOB['seed'],'forward_speed_request_m_s':.08*float(JOB['speed_factor']),'physical_response_for_new_speed_not_claimed':JOB['speed_factor']!=1.};dump(O/'COMPLETION.json',answer);print(json.dumps(answer),flush=True)
if __name__=='__main__':main()
