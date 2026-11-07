"""Closed V787 arrays only: factor failure and test a conservative historical norm envelope."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v787_declared_speed_global'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V788_MODEL_AND_INTEGRATION_FORBIDDEN')
for name in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
from renewal_state import decode
from recursive_domain import AXIS,GRID,LOWER,HALF_DIAGONAL,SLACK,SPEED
from free_certificate import body_points
from refined_body import refined
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v788_global_information_diagnosis';root.mkdir(exist_ok=False)
def dump(name,value):
 p=root/name;tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False,ensure_ascii=False)+'\n');tmp.replace(p)
start=time.time();deadline=min(start+600,1793750400.);window=dict(started_unix=start,absolute_deadline_unix=deadline,round_closed=False,new_models=0,new_integrations=0)
dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V788_ABSOLUTE_STOP')));signal.alarm(max(1,math.floor(deadline-start)))
class Persistent:
 def __init__(self,domain,lower):self.origin=domain.origin;self.time=domain.time;self.lower=lower
 def point_lower(self,points,times):
  pp=np.asarray(points,float);flat=pp.reshape(-1,2);tt=np.broadcast_to(times,pp.shape[:-1]).reshape(-1);assert np.all(tt>=self.time-1e-10),'NONCAUSAL_QUERY'
  ix=np.rint((flat-LOWER)/GRID).astype(int);valid=((ix>=0)&(ix<len(AXIS))).all(axis=1);ix=np.clip(ix,0,len(AXIS)-1)
  value=np.maximum(0.,self.lower[ix[:,0],ix[:,1]]-np.linalg.norm(LOWER+ix*GRID-flat,axis=1));value[~valid]=0.
  return(value-SPEED*np.maximum(0.,tt-self.time)).reshape(pp.shape[:-1])
 def body_lower(self,poses,times):return refined(self,poses,times)
status='RUNNING'
try:
 assert (repo/'REVIEW_PENDING').exists()
 lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
 assert read(repo/'runs/v787_declared_speed_global/FINALIZED.json')['status']=='GLOBAL_DYNAMIC_NOT_PASSED'
 pair=repo/'runs/v787_declared_speed_global/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json')
 bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
 beliefs=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()];assert len(packets)==len(beliefs)==271
 checkpoints=[116,196,228,268];records=[];history=[];maximum_history_error=0.;maximum_coverage=-float('inf');maximum_original_error=0.;lower=None;last=None
 rng=np.random.default_rng(788);sample=rng.integers(0,len(AXIS),size=(512,2))
 # Fixed random test lattice is independent of future actor evaluation.
 for packet,state in zip(packets,beliefs):
  assert packet['step']==state['step'] and packet['time']==state['time'];d=decode(state['free_space_renewal']);fresh=np.maximum(0.,d.distance-HALF_DIAGONAL-SLACK)
  lower=fresh.copy() if lower is None else np.maximum(fresh,np.maximum(0.,lower-SPEED*(d.time-last)))
  history.append((d.time,fresh[sample[:,0],sample[:,1]].copy()))
  independent=np.maximum(0.,np.max(np.asarray([v-SPEED*(d.time-t)for t,v in history]),axis=0));maximum_history_error=max(maximum_history_error,float(np.max(abs(independent-lower[sample[:,0],sample[:,1]]))));assert maximum_history_error<=1e-12
  e=Persistent(d,lower);times=d.time+np.arange(329)*.01;truth=np.asarray(cfg['anchor_xy'])+np.sin(times*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy']);values=e.point_lower(truth,times);maximum_coverage=max(maximum_coverage,float(values.max()));assert values.max()<=1e-7,'ACTUAL_CENTER_EXCLUDED'
  if packet['step'] in checkpoints:
   checkpoint=read(cell/'retained_reentry'/f"step{packet['step']:04}.json");assert len(checkpoint['records'])==15
   for c in checkpoint['records']:
    z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));poses=z['poses'];t=d.time+np.arange(1,329)*.01;known=pose_values(field,poses);old=d.body_lower(poses,t);new=np.maximum(old,e.body_lower(poses,t));a=np.minimum(known,old);b=np.minimum(known,new);err=abs(float(a.min())-c['minimum_causal_clearance_m']);maximum_original_error=max(maximum_original_error,err);assert err<=1e-8 and np.all(b>=a-1e-12)
    j=int(np.argmin(a));positive=bool(np.mean(c['target'][2:])>=1. and c['goal_progress_m']>=.05)
    margin=float(np.minimum(z['self_bounds'][:,:2]-bounds[:2],bounds[2:]-z['self_bounds'][:,2:]).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));all_other=bool(margin>=.002 and speed<=.025 and angular<=.025)
    records.append(dict(step=packet['step'],label=c['label'],original_reason=c['reason'],original_minimum_m=float(a.min()),persistent_minimum_m=float(b.min()),known_static_minimum_m=float(known.min()),unknown_minimum_m=float(old.min()),minimum_at_native_tick=j+1,unknown_at_same_pose_without_future_aging_m=float(old[j]+SPEED*(j+1)*.01),target=c['target'],goal_progress_m=c['goal_progress_m'],positive_progress=positive,newly_admitted=bool(c['reason']=='TIME_CLEARANCE'and b.min()>=.155 and all_other),not_executed=True))
   dump('RECORDS.partial.json',records)
  last=d.time
 # Reject time travel and ensure out-of-domain observations cannot create clearance.
 rejected=0
 for age in [.0001,.08,3.28]:
  try:e.point_lower([[0.,0.]],[e.time-age])
  except AssertionError:rejected+=1
 assert rejected==3 and e.point_lower([[100.,100.]],[e.time])[0]==0.
 assert len(records)==60 and all(sha(repo/p)==h for p,h in freeze['files'].items())
 useful=[r for r in records if r['newly_admitted']and r['positive_progress']]
 status='PERSISTENT_NORM_CERTIFICATE_QUALIFIED'if useful else'PERSISTENT_NORM_CERTIFICATE_NOT_QUALIFIED'
 execution=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];dist=np.asarray([np.linalg.norm(np.asarray(x['qpos_full'])[:2]-protocol['goal_xy'])for x in execution]);plans=[read(p)for p in sorted(cell.glob('planning_*.json'))]
 result=dict(status=status,original_global_outcome=read(cell/'result.json')['outcome'],actual_goal_arrival=False,checkpoints=checkpoints,saved_predictions=len(records),new_positive_progress_admissions=useful,maximum_original_clearance_error=maximum_original_error,maximum_independent_history_error=maximum_history_error,forecast_coverage_samples=len(packets)*329,maximum_actual_coverage_excess_m=maximum_coverage,negative_noncausal_rejected=rejected,maximum_actual_goal_distance_reduction_m=8.-float(dist.min()),final_actual_goal_distance_reduction_m=8.-float(dist[-1]),all_planning_attempts_found_path=all(p['path']is not None for p in plans),new_models=0,new_integrations=0,new_predictions=0,new_navigation=0,declared_norm_speed_cap_m_s=.08,broader_motion_class_not_solved=True)
 dump('RECORDS.json',records);dump('RESULT.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-start);dump('ROUND_WINDOW.json',window)
