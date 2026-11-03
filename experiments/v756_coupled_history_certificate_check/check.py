"""Closed trajectories: persistent certificates plus independent full-history max."""
import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'))
sys.path.insert(0,str(repo/'experiments/v742_persistent_clearance_envelope'))
sys.path.insert(2,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V756_INITIALIZATION_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from recursive_domain import RecursiveDomain,AXIS,LOWER,GRID,SPEED,HALF_DIAGONAL,SLACK
from renewal_state import encode
from envelope import Envelope
from free_certificate import body_points,old_lower
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v756_coupled_history_certificate_check';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False);dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V756_600S_ABSOLUTE_STOP')));signal.alarm(600);status='RUNNING'
def clone(d):
 c=RecursiveDomain(d.origin);c.time=d.time;c.possible=d.possible.copy();c.distance=d.distance.copy();c.last=dict(d.last);return c
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 raw=repo/'runs/v753_coupled_progress_repaired';r=read(raw/'RESULT.json');assert read(repo/'runs/v754_coupled_progress_repaired_audit/RESULT.json')['status']=='COUPLED_PROGRESS_SAVED_EVIDENCE_VERIFIED'
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f][:33]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 def truth(when):
  t=when+np.linspace(0,3.28,329);return np.asarray(cfg['anchor_xy'])+np.sin(t*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy']),t
 allpoints=[];observations={}
 for b in r['branches']:
  with gzip.open(raw/(b['name']+'_OBSERVATIONS.json.gz'),'rt')as f:observations[b['name']]=json.load(f)
  for d in b['decisions']:
   z=np.load(raw/(d['label']+'_PRIVATE.npz'));pts,_=body_points(z['poses']);allpoints.append(pts.reshape(-1,2))
 for o in old:allpoints.append(truth(o['time'])[0])
 for rows in observations.values():
  for o in rows:allpoints.append(truth(o['packet']['time'])[0])
 indices=np.rint((np.vstack(allpoints)-LOWER)/GRID).astype(int);assert ((indices>=0)&(indices<len(AXIS))).all();grid=np.unique(indices,axis=0);flats=grid[:,0]*len(AXIS)+grid[:,1]
 def fresh(d):return np.maximum(0.,d.distance[grid[:,0],grid[:,1]]-HALF_DIAGONAL-SLACK)
 def direct_points(points,times,when,h):
  pp=np.asarray(points);flat=pp.reshape(-1,2);tt=np.broadcast_to(times,pp.shape[:-1]).reshape(-1);ix=np.rint((flat-LOWER)/GRID).astype(int);slots=np.searchsorted(flats,ix[:,0]*len(AXIS)+ix[:,1]);assert np.array_equal(grid[slots],ix);used,reverse=np.unique(slots,return_inverse=True);ages=when-np.asarray([x[0]for x in h]);assert np.all(ages>=-1e-10)and np.all(tt>=when-1e-10)
  values=np.asarray([x[1][used]for x in h])-SPEED*ages[:,None];maximum=np.maximum(0.,values.max(axis=0));distance=np.linalg.norm(LOWER+ix*GRID-flat,axis=1);return(np.maximum(0.,maximum[reverse]-distance)-SPEED*np.maximum(0.,tt-when)).reshape(pp.shape[:-1])
 def direct_body(poses,times,when,h,origin):
  pts,cover=body_points(poses);return np.maximum(direct_points(pts,np.asarray(times)[:,None],when,h).min(axis=1)-cover-.10,old_lower(poses,times,origin))
 count=0;maximum_error=0.;maxcoverage=-float('inf');records=[]
 def coverage(e,d,h):
  global count,maximum_error,maxcoverage
  pts,times=truth(e.time);a=e.point_lower(pts,times);b=direct_points(pts,times,e.time,h);error=float(np.max(abs(a-b)));maximum_error=max(maximum_error,error);assert error<=1e-12 and a.max()<=1e-7 and np.all(a>=d.point_lower(pts,times)-1e-12);maxcoverage=max(maxcoverage,float(a.max()));count+=1
 base=RecursiveDomain(p['start_qpos'][:2]);env=Envelope(base.origin);history=[]
 for packet in old:base.update(packet);assert encode(base)==beliefs[packet['step']]['free_space_renewal'];env.update(base);history.append((base.time,fresh(base)));coverage(env,base,history)
 for branch in r['branches']:
  d=clone(base);e=env.copy();h=list(history);rows=observations[branch['name']];decisions={x['local_public']:x for x in branch['decisions']}
  for k in range(len(rows)+1):
   if k in decisions:
    c=decisions[k];z=np.load(raw/(c['label']+'_PRIVATE.npz'));times=e.time+np.arange(1,329)*.01;known=pose_values(static,z['poses']);oldvals=np.minimum(known,d.body_lower(z['poses'],times));newvals=np.minimum(known,e.body_lower(z['poses'],times));direct=np.minimum(known,direct_body(z['poses'],times,e.time,h,d.origin));error=float(np.max(abs(newvals-direct)));maximum_error=max(maximum_error,error);assert error<=1e-12 and np.all(newvals>=oldvals-1e-12)and abs(oldvals.min()-c['minimum_causal_clearance_m'])<=1e-10
    margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));reason='TIME_CLEARANCE'if newvals.min()<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
    records.append(dict(profile=branch['profile'],label=c['label'],local_public=k,old_reason=c['reason'],new_reason=reason,old_admissible=c['admissible'],new_admissible=reason is None,old_min_m=float(oldvals.min()),new_min_m=float(newvals.min()),gain_m=float(newvals.min()-oldvals.min()),direct_history_error=error,not_used_for_physics=True));np.savez_compressed(root/(c['label']+'_GEOMETRY.npz'),old_values=oldvals,new_values=newvals,direct_values=direct)
   if k<len(rows):o=rows[k];d.update(o['packet']);assert encode(d)==o['domain'];e.update(d);h.append((d.time,fresh(d)));coverage(e,d,h)
 assert len(records)==32 and count==260
 rejected=0
 for offset in [.0001,.08,3.28]:
  try:e.point_lower([[0.,0.]],[e.time-offset])
  except AssertionError:rejected+=1
 assert rejected==3 and e.point_lower([[100.,100.]],[e.time])[0]==0.
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='COUPLED_HISTORY_CERTIFICATES_AND_DIRECT_HISTORY_VERIFIED';dump('RECORDS.json',records);dump('RESULT.json',dict(status=status,saved_trajectories=len(records),newly_admissible=[x for x in records if x['new_admissible']and not x['old_admissible']],all_actual_packets=count,forecast_coverage_samples=count*329,queried_grid_points=len(grid),maximum_direct_history_error=maximum_error,maximum_actual_coverage_excess_m=maxcoverage,noncausal_queries_rejected=rejected,all_saved_controls_unchanged=True,new_fields_used_for_physics=False,new_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0))
except BaseException as err:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(err).__name__,message=str(err),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
