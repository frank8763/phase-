"""Direct max over all past certificates at every queried lattice point."""
import gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation';sys.path.insert(0,str(source))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V743_NO_MODEL_INITIALIZATION_OR_INTEGRATION')
for n in['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from recursive_domain import RecursiveDomain,GRID,LOWER,AXIS,HALF_DIAGONAL,SLACK,SPEED
from renewal_state import encode
from free_certificate import body_points,old_lower
from exact_footprint import pose_values
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();root=repo/'runs/v743_persistent_envelope_audit';root.mkdir(exist_ok=False);started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V743_FIXED_300S_STOP')));signal.alarm(300);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});dump('ROUND_WINDOW.json',window);status='RUNNING'
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(repo/'experiments/v742_persistent_clearance_envelope/INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());out=repo/'runs/v742_persistent_clearance_envelope';res=read(out/'RESULT.json');assert res['status']=='PERSISTENT_CERTIFICATE_SAVED_ELIGIBILITY_COMPLETE'
 raw=repo/'runs/v740_preemptive_observation_cycles';run=read(raw/'RESULT.json');pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 allpoints=[]
 for r in res['records']:
  z=np.load(raw/(r['label']+'_PRIVATE.npz'));points,_=body_points(z['poses']);allpoints.append(points.reshape(-1,2))
 def truth(when):
  t=when+np.linspace(0,3.28,329);return np.asarray(config['anchor_xy'])+np.sin(t*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']),t
 for packet in old:allpoints.append(truth(packet['time'])[0])
 for file in raw.glob('*_OBSERVATIONS.json.gz'):
  with gzip.open(file,'rt')as f:
   for row in json.load(f):allpoints.append(truth(row['packet']['time'])[0])
 indices=np.rint((np.vstack(allpoints)-LOWER)/GRID).astype(int);assert ((indices>=0)&(indices<len(AXIS))).all();grid=np.unique(indices,axis=0);flats=grid[:,0]*len(AXIS)+grid[:,1]
 def clone(d):
  c=RecursiveDomain(d.origin);c.time=d.time;c.possible=d.possible.copy();c.distance=d.distance.copy();c.last=dict(d.last);return c
 def fresh(d):return np.maximum(0.,d.distance[grid[:,0],grid[:,1]]-HALF_DIAGONAL-SLACK)
 def points_lower(points,times,when,history):
  pp=np.asarray(points);flat=pp.reshape(-1,2);tt=np.broadcast_to(times,pp.shape[:-1]).reshape(-1);ix=np.rint((flat-LOWER)/GRID).astype(int);slots=np.searchsorted(flats,ix[:,0]*len(AXIS)+ix[:,1]);assert np.array_equal(grid[slots],ix);used,reverse=np.unique(slots,return_inverse=True);ages=when-np.asarray([h[0]for h in history]);assert np.all(ages>=-1e-10)and np.all(tt>=when-1e-10)
  values=np.asarray([h[1][used]for h in history])-SPEED*ages[:,None];direct=np.maximum(0.,np.max(values,axis=0));distance=np.linalg.norm(LOWER+ix*GRID-flat,axis=1);return(np.maximum(0.,direct[reverse]-distance)-SPEED*np.maximum(0.,tt-when)).reshape(pp.shape[:-1])
 def body_lower(poses,times,when,history):
  points,cover=body_points(poses);return np.maximum(points_lower(points,np.asarray(times)[:,None],when,history).min(axis=1)-cover-.10,old_lower(poses,times,np.asarray(p['start_qpos'][:2])))
 base=RecursiveDomain(p['start_qpos'][:2]);history=[];bases={};histories={};count=0;max_coverage=-float('inf');max_error=0.;checked=[];beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 def coverage(when,h):
  global count,max_coverage
  point,times=truth(when);excess=float(points_lower(point,times,when,h).max());assert excess<=1e-7;max_coverage=max(max_coverage,excess);count+=1
 for packet in old:
  base.update(packet);assert encode(base)==beliefs[packet['step']]['free_space_renewal'];history.append((base.time,fresh(base)));coverage(base.time,history)
  if packet['step']in[73,90,130]:
   step=packet['step'];bases[step]=clone(base);histories[step]=list(history);saved=np.load(out/('BASE_%03d.npz'%step));direct=np.maximum(0.,np.max(np.asarray([h[1]for h in history])-SPEED*(base.time-np.asarray([h[0]for h in history]))[:,None],axis=0));error=float(np.max(abs(direct-saved['lower'][grid[:,0],grid[:,1]])));assert error<=1e-12;max_error=max(max_error,error)
 def check(record,d,h):
  global max_error
  z=np.load(raw/(record['label']+'_PRIVATE.npz'));when=float(d.time);times=when+np.arange(1,329)*.01;known=pose_values(static,z['poses']);values=np.minimum(known,body_lower(z['poses'],times,when,h));saved=np.load(out/(record['label']+'_GEOMETRY.npz'));error=float(np.max(abs(values-saved['new_values'])));max_error=max(max_error,error);assert error<=1e-12;summary=next(x for x in res['records']if x['label']==record['label']);assert abs(values.min()-summary['new_minimum_clearance_m'])<=1e-12;checked.append(dict(label=record['label'],direct_history_error=error))
 def actual(record,d,h):
  with gzip.open(raw/(record['label']+'_OBSERVATIONS.json.gz'),'rt')as f:rows=json.load(f)
  for row in rows:d.update(row['packet']);assert encode(d)==row['domain'];h.append((d.time,fresh(d)));coverage(d.time,h)
 for branch in run['branches']:
  d=clone(bases[branch['step']]);h=list(histories[branch['step']])
  for cycle in branch['cycles']:
   scan=cycle['scan'];check(scan,d,h)
   if not scan['admissible']:break
   actual(scan,d,h)
   for candidate in cycle['successors']:check(candidate,d,h)
   if cycle['selected_successor']is None:break
   selected=next(c for c in cycle['successors']if c['index']==cycle['selected_successor']);actual(selected,d,h)
 assert count==423 and len(checked)==35 and all(sha(repo/n)==h for n,h in freeze['files'].items());status='DIRECT_ALL_HISTORY_CERTIFICATES_VERIFIED';dump('RESULT.json',dict(status=status,queried_grid_points=len(grid),complete_trajectories=len(checked),all_actual_packets=count,forecast_coverage_samples=count*329,maximum_direct_history_error=max_error,maximum_actual_coverage_excess_m=max_coverage,checks=checked,new_initializations=0,new_integrations=0,new_fields_used_for_physics=False))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
