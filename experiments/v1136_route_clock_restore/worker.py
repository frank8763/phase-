"""Final-leg nonuniform segment timing and steering; no new physical model."""
import sys,json,time,signal,hashlib,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];JOB=json.loads(Path(sys.argv[1]).read_text());O=Path(JOB['output'])
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry,REQUIRED
from source import Engine,initial,python_replay,COUNTS
from recovery_source import forecast_packet
import numpy as np
class BudgetEnd(Exception):pass
class FeasibleFound(Exception):pass

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def minima(values,bins=64):
 ix=np.minimum(np.arange(len(values))*bins//len(values),bins-1);out=np.full(bins,np.inf);np.minimum.at(out,ix,values);return out

def schedule(base,u,speed):
 assert len(u)==25 and np.isfinite(u).all();assert speed in [.08,.12];assert np.all(abs(u[:12])<=.42722137342572125+1e-12);assert np.all((u[12:24]>=.4)&(u[12:24]<=1.8));wait=int(round(u[-1]*100));assert 0<=wait<=1963
 rows=[tuple(row)for row in base];assert len(rows)==55 and rows[41][3]==1 and rows[-1]==(0.,0.,2200,0)
 rows[41]=(float(u[0]),0.,600,1)
 for j in range(12):rows[42+j]=(float(u[j]),speed,max(1,int(round(base[42+j][2]*u[12+j]*.08/speed))),0)
 assert rows[:41]==[tuple(r)for r in base[:41]] and rows[-1]==(0.,0.,2200,0)
 rows=([(0.,0.,wait,0)]if wait else[])+rows;assert sum(r[2]for r in rows)<=40000,'SOURCE_NATIVE_CAP';return rows,wait

def main():
 start=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('WORKER600')));signal.alarm(600);engine=None;best=None;error=None;proof=None;calls=0;backups=[];model_error=None;exit=None
 freeze=json.loads((C/'SOURCE_FREEZE.json').read_text())['files'];assert all(sha(R/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_CHANGED'
 try:
  x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());x['safe_terminal_pose']=json.loads((R/'runs/v1125_safe_goal_region/TERMINAL_SELECTION.json').read_text())['selected_body_pose'];selected=json.loads((R/JOB['seed_file']).read_text());base=[tuple(r)for r in selected['rows']];wait=0.
  if len(base)==56:wait=base.pop(0)[2]*.01
  else:wait=18.5
  assert len(base)==55
  u0=np.r_[[r[0]for r in base[42:54]],np.ones(12),wait];lower=np.r_[np.full(12,-.42722137342572125),np.full(12,.4),0.];upper=np.r_[np.full(12,.42722137342572125),np.full(12,1.8),19.63];engine=Engine(x['setup']);assert sha(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz')==JOB['table_sha256'];z=np.load(R/'runs/v1135_causal_batch/domain/JOINT_TABLE.npz');g=Geometry(x,{k:z[k]for k in ['bounds','centers']});target=np.array(x['safe_terminal_pose']);cache={};deadline=time.monotonic()+300
  def evaluate(u):
   nonlocal calls,best
   if calls>=5000 or time.monotonic()>deadline:raise BudgetEnd()
   rows,wait=schedule(base,u,JOB['speed']);key=(u[:12].tobytes(),tuple(r[2]for r in rows))
   if key in cache:return cache[key]
   ss,uu=engine.simulate(initial(x['packet']),rows);calls+=1;a,b=g.components(ss[:,:3],np.arange(len(ss)));sa=minima(a);dy=minima(b);delta=ss[-1,:2]-target[:2];yaw=float(np.arctan2(np.sin(ss[-1,2]-target[2]),np.cos(ss[-1,2]-target[2])));cycle=float(g.cycle(ss[-1:,:3])[0]);cursor=0;modes=[]
   for t,v,n,m in rows:
    if m:modes.append(float(g.cycle(ss[cursor:cursor+1,:3])[0])-.02-np.hypot(.44,.375)*.1)
    cursor+=int(n)
   # Fixed bins retain EVERY native minimum. High obstacle weight avoids trading clearance for endpoint fit.
   r=np.r_[delta/.025,yaw/.1,np.maximum(0.,REQUIRED+.001-sa)/.01,np.maximum(0.,REQUIRED+.001-dy)/.01,np.maximum(0.,REQUIRED+x['mode_reserve']-np.array(modes))/.01,max(0.,REQUIRED+.001-cycle)/.01,.002*(u[:12]-u0[:12]),.002*np.diff(u[:12]),.001*(u[12:24]-1.)]
   violation=max(0.,REQUIRED+.001-float(a.min()),REQUIRED+.001-float(b.min()),float(np.linalg.norm(delta))-.025,abs(yaw)-.1,REQUIRED+.001-cycle);rank=(violation,float(r@r));report={'u':u.copy(),'rows':rows,'initial_wait_native':wait,'minimum_static_m':float(a.min()),'minimum_dynamic_m':float(b.min()),'terminal_distance_m':float(np.linalg.norm(delta)),'terminal_yaw_rad':abs(yaw),'terminal_cycle_m':cycle,'rank':rank}
   if best is None or rank<best['rank']:best=report;dump(O/'PROGRESS.json',{k:v for k,v in report.items()if k not in ['u','rows']}|{'calls':calls,'analytical_cpp_native':engine.native})
   cache[key]=r
   if len(cache)>80:cache.pop(next(iter(cache)))
   if violation<=.001 and g.final(x,ss,uu,rows)[0]['passed']:best=report;raise FeasibleFound()
   return r
  def jac(u):
   f=evaluate(u);j=np.empty((len(f),25))
   for i in range(25):
    step=.0001 if i<12 else max(.002,2./base[42+i-12][2])if i<24 else .10;left=u.copy();right=u.copy();left[i]=max(lower[i],u[i]-step);right[i]=min(upper[i],u[i]+step);j[:,i]=(evaluate(right)-evaluate(left))/(right[i]-left[i])
   return j
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.optimize import least_squares
  try:
   result=least_squares(evaluate,u0,jac=jac,bounds=(lower,upper),max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9,x_scale=np.r_[np.full(12,.15),np.full(12,.4),5.]);exit={'status':int(result.status),'message':str(result.message),'nfev':int(result.nfev),'deterministic':True}
  except FeasibleFound:exit={'status':'FULL_SOURCE_FEASIBLE','deterministic':True}
  except BudgetEnd:exit={'status':'SOFTWARE_BUDGET','deterministic':calls>=5000}
  assert best is not None;rows=best['rows'];ss,uu=engine.simulate(initial(x['packet']),rows);proof,_=g.final(x,ss,uu,rows);proof['checks']['deterministic_work_or_feasible']=exit['deterministic'];proof['checks']['registered_mode_headroom']=all(m['raw_envelope_lower']>=REQUIRED+x['mode_reserve']-1e-10 for m in proof['mode_envelopes']);proof['passed']=bool(all(proof['checks'].values()));dump(O/'OPTIMIZATION.json',dict(best,proof=proof,optimizer_exit=exit));np.savez_compressed(O/'SELECTED_SOURCE.npz',states=ss,controls=uu)
  ps,pu,mem,episodes,active=python_replay(x['setup'],initial(x['packet']),rows);COUNTS['python_native']+=len(pu);model_error=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert model_error<=1e-8,'INDEPENDENT_MODEL_MISMATCH'
  if proof['passed']:
   for i in range(0,len(pu)-2200+1,125):
    origin={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};bs,bu=engine.simulate(origin,[(0.,0.,2200,0)]);packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=g.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'failed_checks':[k for k,v in bp['checks'].items()if not v]});dump(O/'BACKUPS.json',backups)
 except BaseException as e:
  import traceback
  error={'error':repr(e),'traceback':traceback.format_exc()};dump(O/'ERROR.json',error)
 finally:signal.alarm(0)
 result={'closed':True,'passed':bool(proof and proof['passed']and backups and all(b['passed']for b in backups)and not error),'full_source_passed':bool(proof and proof['passed']),'optimizer_exit':exit,'optimizer_calls':calls,'best':{k:v for k,v in best.items()if k not in ['u','rows']}if best else None,'failed_checks':[k for k,v in proof['checks'].items()if not v]if proof else None,'backup_count':len(backups),'maximum_model_error':model_error,'counts':{'analytical_cpp_native':engine.native if engine else 0,'cpp_inflight_work_unknown':bool(engine and getattr(engine,'in_call',False)),'independent_python_native':COUNTS['python_native']},'error':error,'models':0,'physical_integrations':0,'wall_s':time.monotonic()-start,'source_unchanged':all(sha(R/p)==h for p,h in freeze.items()),'speed':JOB['speed'],'higher_speed_requires_physical_response_qualification':JOB['speed']>.08};dump(O/'COMPLETION.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
