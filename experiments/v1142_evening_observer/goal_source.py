"""Two fixed goal-suffix software profiles from the NEW actual stopped source."""
import sys,time,signal,traceback,importlib.abc
from evening_tools import *
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());import numpy as np
sys.path.insert(0,str(R/'experiments/v1135_causal_batch'));from geometry import Geometry,REQUIRED
from source import Engine,initial,python_replay,remaining_rows
from recovery_source import forecast_packet
class BudgetEnd(Exception):pass
class Found(Exception):pass

def group(a,n=64):
 b=np.full(n,np.inf);np.minimum.at(b,np.minimum(np.arange(len(a))*n//len(a),n-1),a);return b

def schedule(base,u,speed):
 n=len(base)-1;assert len(u)==2*n+1 and base[-1]==(0.,0.,2200,0);assert np.isfinite(u).all()and np.all(abs(u[:n])<=.42722137342572125+1e-12)and np.all((u[n:2*n]>=.4)&(u[n:2*n]<=1.8));wait=int(round(float(u[-1])*100));assert 0<=wait<=1963;rows=([(0.,0.,wait,0)]if wait else[])+[(float(u[i]),speed,max(1,int(round(base[i][2]*u[n+i]*.12/speed))),0)for i in range(n)]+[(0.,0.,2200,0)];assert sum(r[2]for r in rows)<=40000;return rows

def main():
 job=json.loads(Path(sys.argv[1]).read_text());out=Path(job['output']);out.mkdir();begun=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('GOAL_WORKER1800')));signal.alarm(min(1800,max(1,int(remaining()-120))));error=None;engine=None;calls=0;python_native=0;partial=False;best=None;exit=None;backups=[];proof=None;modelerr=None
 try:
  assert source_ok();x=json.loads((O/'post_observation/FRESH_INPUT.json').read_text());tab=np.load(O/'post_observation/JOINT_TABLE.npz');g=Geometry(x,{k:tab[k]for k in ['bounds','centers']});old=json.loads((R/'runs/v1136_route_clock_restore/dynamic_seed_v120/OPTIMIZATION.json').read_text());base=[tuple(r)for r in remaining_rows(old['rows'],12500)];assert all(not r[3]for r in base)and base[-1]==(0.,0.,2200,0);n=len(base)-1;u0=np.r_[[r[0]for r in base[:-1]],np.ones(n),0.];lower=np.r_[np.full(n,-.42722137342572125),np.full(n,.4),0.];upper=np.r_[np.full(n,.42722137342572125),np.full(n,1.8),19.63];engine=Engine(x['setup']);target=np.array([4.,-1.85,0.]);x['safe_terminal_pose']=target.tolist();x['mode_reserve']=.015;cache={};deadline=time.monotonic()+600.;speed=job['speed'];origin=initial(x['packet'])
  def evaluate(u):
   nonlocal best,calls,partial
   if calls>=2400 or time.monotonic()>deadline or remaining()<180:raise BudgetEnd()
   rows=schedule(base,u,speed);key=(u[:n].tobytes(),tuple(r[2]for r in rows))
   if key in cache:return cache[key]
   partial=True;ss,uu=engine.simulate(origin,rows);partial=False;calls+=1;a,b=g.components(ss[:,:3],np.arange(len(ss)));cycle=g.cycle(ss[:,:3]);delta=ss[-1,:2]-target[:2];yaw=float(np.arctan2(np.sin(ss[-1,2]),np.cos(ss[-1,2])));backup_lows=[];moving=sum(r[2]for r in rows)-2200
   # Fixed fractions, not selected after seeing a collision. Dynamic state and memory
   # for the stop origins are independently recovered only for final admission;
   # cycle-clearance of every moving native supplies conservative optimizer guidance.
   residual=np.r_[delta/.025,yaw/.1,np.maximum(0.,REQUIRED+.005-group(a))/.01,np.maximum(0.,REQUIRED+.005-group(b))/.01,np.maximum(0.,REQUIRED+.015-group(cycle))/.01,.002*np.diff(u[:n]),.001*(u[n:2*n]-1.)];violation=max(0.,REQUIRED+.001-float(a.min()),REQUIRED+.001-float(b.min()),REQUIRED+.005-float(cycle.min()),float(np.linalg.norm(delta))-.025,abs(yaw)-.1);rank=(violation,float(residual@residual));candidate={'u':u.copy(),'rows':rows,'minimum_static_m':float(a.min()),'minimum_dynamic_m':float(b.min()),'minimum_cycle_pose_m':float(cycle.min()),'terminal_position_error_m':float(np.linalg.norm(delta)),'terminal_yaw_error_rad':abs(yaw),'rank':rank}
   if best is None or rank<best['rank']:best=candidate;dump(out/'PARTIAL.json',{k:v for k,v in candidate.items()if k not in ['u','rows']}|{'calls':calls,'analytical_cpp_native':engine.native})
   cache[key]=residual
   if len(cache)>80:cache.pop(next(iter(cache)))
   if violation<=.001 and g.final(x,ss,uu,rows)[0]['passed']:best=candidate;raise Found()
   return residual
  def jac(u):
   f=evaluate(u);j=np.empty((len(f),len(u)))
   for k in range(len(u)):
    step=.0001 if k<n else max(.002,2./base[k-n][2])if k<2*n else .1;l=u.copy();r=u.copy();l[k]=max(lower[k],u[k]-step);r[k]=min(upper[k],u[k]+step);j[:,k]=(evaluate(r)-evaluate(l))/(r[k]-l[k])
   return j
  sys.path.insert(0,str(R/'runs/v1111_solver_dependencies/site'));from scipy.optimize import least_squares
  try:
   r=least_squares(evaluate,u0,jac=jac,bounds=(lower,upper),max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9);exit={'status':int(r.status),'deterministic':True,'nfev':int(r.nfev)}
  except Found:exit={'status':'FEASIBLE_STOP','deterministic':True}
  except BudgetEnd:exit={'status':'SOFTWARE_BUDGET','deterministic':calls>=2400}
  assert best is not None;rows=best['rows'];partial=True;ss,uu=engine.simulate(origin,rows);partial=False;proof,_=g.final(x,ss,uu,rows);proof['checks']['deterministic_work_or_feasible']=exit['deterministic'];proof['passed']=bool(all(proof['checks'].values()));ps,pu,mem,episodes,active=python_replay(x['setup'],origin,rows);python_native=len(pu);modelerr=max(float(abs(ps-ss).max()),float(abs(pu-uu).max()));assert modelerr<=1e-8,'INDEPENDENT_MODEL_MISMATCH';dump(out/'SOURCE_PROOF.json',proof);dump(out/'ROWS.json',{'rows':rows,'input':x,'original_goal':[4.,-2.],'safe_terminal':[4.,-1.85,0.]});np.savez_compressed(out/'SOURCE.npz',states=ps,controls=pu,memory=mem,coupled=episodes,active=active)
  if proof['passed']:
   nodes=list(range(0,len(pu)-2200+1,8));nodes.append(len(pu)-2200)
   for i in sorted(set(nodes)):
    assert remaining()>60;inp={'state':ps[i].copy(),'last_ctrl':mem[i,:4].copy(),'integral':float(mem[i,4]),'coupled_episode':bool(episodes[i]),'steering_motion_active':bool(active[i])};partial=True;bs,bu=engine.simulate(inp,[(0.,0.,2200,0)]);partial=False;packet=forecast_packet(x['packet'],ps[i],mem[i],i);packet.update(body_lateral=float(ps[i,4]),coupled_episode=bool(episodes[i]),steering_motion_active=bool(active[i]));bp,_=g.final(dict(x,packet=packet,goal=bs[-1,:2].tolist(),safe_terminal_pose=bs[-1,:3].tolist()),bs,bu,[(0.,0.,2200,0)]);backups.append({'native':i,'passed':bp['passed'],'minimum_raw_m':bp['minimum_raw_m'],'terminal_cycle_m':bp['terminal_full_cycle_raw_m'],'failed_checks':[k for k,v in bp['checks'].items()if not v],'states_sha256':hashlib.sha256(bs.tobytes()).hexdigest(),'ctrl_sha256':hashlib.sha256(bu.tobytes()).hexdigest()})
    if len(backups)%64==0:dump(out/'AUDIT_PARTIAL.json',{'backups':len(backups),'failed':sum(not b['passed']for b in backups)})
   dump(out/'ALL8_BACKUPS.json',backups)
 except BaseException as e:error={'error':repr(e),'traceback':traceback.format_exc()};dump(out/'ERROR.json',error)
 finally:signal.alarm(0)
 result={'closed':True,'passed':bool(proof and proof['passed']and backups and all(b['passed']for b in backups)and error is None),'full_source_passed':bool(proof and proof['passed']),'backup_count':len(backups),'failed_backups':sum(not b['passed']for b in backups),'optimizer_calls':calls,'optimizer_exit':exit,'counts':{'analytical_cpp_native':engine.native if engine else 0,'cpp_inflight_work_unknown':partial,'independent_python_native':python_native},'maximum_independent_error':modelerr,'best':{k:v for k,v in best.items()if k not in ['rows','u']}if best else None,'error':error,'physical_integrations':0,'models':0,'original_goal_physical_arrival':False,'wall_s':time.monotonic()-begun};dump(out/'RESULT.json',result);print(encode(result));return 0 if error is None else 1
if __name__=='__main__':sys.exit(main())
