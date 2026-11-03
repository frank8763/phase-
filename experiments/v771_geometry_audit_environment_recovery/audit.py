"""Independent numpy propagation/scipy distances, no candidate module import."""
import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback,gc
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'runs/v771_audit_dependencies/site'))
from scipy.ndimage import distance_transform_edt
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def no(*a,**k):raise RuntimeError('V771_NO_MODEL_OR_INTEGRATION')
for k in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,k,no)
from recursive_domain import RecursiveDomain,AXIS,GRID,LOWER,HALF_DIAGONAL,SLACK,exclusion
from renewal_state import encode
from free_certificate import body_points,old_lower
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v771_geometry_audit_environment_recovery';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0);dump('ROUND_WINDOW.json',window);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V771_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});status='RUNNING'
def grow(a,mask=None):
 pad=np.pad(a,1,constant_values=True);out=np.zeros_like(a)
 for dx in range(3):
  for dy in range(3):out|=pad[dx:dx+a.shape[0],dy:dy+a.shape[1]]
 if mask is not None:out&=mask
 out[[0,-1],:]=True;out[:,[0,-1]]=True;return out

def unpack(row,shape):return np.unpackbits(row,bitorder='little')[:np.prod(shape)].reshape(shape).astype(bool)
def dist(a):return distance_transform_edt(~a,sampling=GRID)
def lower(field,points):
 shape=points.shape[:-1];flat=points.reshape(-1,2);idx=np.rint((flat-LOWER)/GRID).astype(int);inside=((idx>=0)&(idx<len(AXIS))).all(axis=1);idx=np.clip(idx,0,len(AXIS)-1);d=field[idx[:,0],idx[:,1]]-np.linalg.norm(flat-(LOWER+idx*GRID),axis=1)-HALF_DIAGONAL-SLACK;d[~inside]=0.;return np.maximum(d,0).reshape(shape)
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 dependency_frozen=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/n)==h for n,h in dependency_frozen.items())
 frozen=read(repo/'experiments/v769_geometry_reachability_qualification/INPUT_FREEZE.json')['files'];assert all(sha(repo/n)==h for n,h in frozen.items())
 raw=repo/'runs/v769_geometry_reachability_qualification';result=read(raw/'RESULT.json');assert result['status']=='SAVED_GEOMETRY_REACHABILITY_QUALIFICATION_COMPLETE'
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json');x,y=np.meshgrid(AXIS,AXIS,indexing='ij');mask=np.ones_like(x,dtype=bool)
 for cx,cy,hx,hy in p['known_rectangles']:
  dx=abs(x-cx)-hx;dy=abs(y-cy)-hy;point_distance=np.where((dx<=0)&(dy<=0),np.maximum(dx,dy),np.sqrt(np.maximum(dx,0)**2+np.maximum(dy,0)**2));mask&=point_distance+HALF_DIAGONAL>=.1-SLACK
 for cx,cy,r in p['known_circles']:mask&=np.sqrt((x-cx)**2+(y-cy)**2)-r+HALF_DIAGONAL>=.1-SLACK
 for boundary in [x+5,5-x,y+5,5-y]:mask&=boundary+HALF_DIAGONAL>=.1-SLACK
 mask[[0,-1],:]=True;mask[:,[0,-1]]=True;z=np.load(raw/'ALLOWED_CELLS.npz');assert np.array_equal(mask,unpack(z['bits'],z['shape']))
 del x,y,dx,dy,point_distance;gc.collect()
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f][:33]
 worker=repo/'runs/v767_certified_progress_release';branch=read(worker/'FEEDBACK_MAIN_SUMMARY.json');decisions={d['local_public']:d for d in branch['decisions']}
 with gzip.open(worker/'FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as f:obs=json.load(f)
 bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 def truth(ts):return np.asarray(cfg['anchor_xy'])+np.sin(np.asarray(ts)*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy'])
 d=RecursiveDomain(p['start_qpos'][:2]);current=None;states={}
 for packet in old+[o['packet']for o in obs]:
  d.update(packet);free,_,_=exclusion(packet,d.origin);current=(np.ones_like(free)if current is None else grow(current,mask))&~free&mask;current[[0,-1],:]=True;current[:,[0,-1]]=True
  loc=packet['step']-32
  if loc in [64,96,116]:
   z=np.load(raw/('STATE_%03d.npz'%loc));assert np.array_equal(current,unpack(z['map_bits'],z['shape']))and np.array_equal(d.possible,unpack(z['old_bits'],z['shape']));states[loc]=(current.copy(),d.possible.copy(),d.time)
 assert len(states)==3
 checked=0;maxerr=0.;newrecords=[]
 for local,(mapped,original,when)in states.items():
  candidates=decisions[local]['candidates'];saved=[np.load(worker/(c['label']+'_PRIVATE.npz'))for c in candidates];allpoints=[];cover=None
  for zz in saved:pt,cover=body_points(zz['poses']);allpoints.append(pt)
  points=np.stack(allpoints);times=when+np.arange(1,329)*.01;known=np.stack([pose_values(static,zz['poses'])for zz in saved]);vals={};oldfield=dist(original);mapfield=dist(mapped)
  for variant,field in [('A',oldfield),('B',mapfield)]:
   centers=lower(field,points)-np.sqrt(2)*.12*(times-when)[None,:,None];new=centers.min(axis=2)-cover-.1;new=np.maximum(new,np.stack([old_lower(zz['poses'],times,p['start_qpos'][:2])for zz in saved]));vals[variant]=np.minimum(known,new)
  for variant,initial,allowed in [('C',mapped,mask),('D',original,None)]:
   savedfields=np.load(raw/('FUTURE_%03d_%s.npz'%(local,variant)));future=initial;values=np.empty((15,328));truthpoints=truth(times);bucket=np.ceil(np.arange(1,329)/8).astype(int)
   for b in range(42):
    if b:future=grow(future,allowed)
    assert np.array_equal(future,unpack(savedfields['bits'][b],savedfields['shape'])),'INDEPENDENT_FUTURE_PROPAGATION_DIFFERENCE';checked+=1
    if b:
     sel=bucket==b;field=dist(future);values[:,sel]=lower(field,points[:,sel]).min(axis=2)-cover-.1;real=truthpoints[sel];idx=np.rint((real-LOWER)/GRID).astype(int);assert np.all(future[idx[:,0],idx[:,1]])and lower(field,real).max()<=1e-7
   vals[variant]=np.minimum(known,values)
  for i,c in enumerate(candidates):
   z=saved[i];query=np.load(raw/('QUERY_%03d_%02d.npz'%(local,i)));source=next(x for x in read(raw/'RECORDS.json')if x['local_public']==local and x['action_index']==i)
   nonclear=containment_margin(z['self_bounds'],bounds).min()>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025 and np.linalg.norm(z['qvel'][-1,3:6])<=.025
   for variant in ['A','B','C','D']:
    err=float(np.max(abs(vals[variant][i]-query[variant])));maxerr=max(maxerr,err);assert err<=1e-10 and abs(vals[variant][i].min()-source['minimum'][variant])<=1e-10 and bool(vals[variant][i].min()>=.155 and nonclear)==source['admissible'][variant]
   assert bool(vals['A'][i].min()>=.155 and nonclear)==c['admissible'];newrecords.append(source)
 assert checked==252 and len(newrecords)==45
 # Analytic all-phase finite actor verification, independently using the signed static point field.
 ph=np.linspace(0,2*np.pi,4097);xy=np.asarray(cfg['anchor_xy'])+np.sin(ph)[:,None]*np.asarray(cfg['axis_xy'])*cfg['amplitude_m'];pointfield=SimpleNamespace(**{**static.__dict__,'half':np.zeros(2),'center_local':np.zeros(2)});margins=pose_values(pointfield,np.c_[xy,np.zeros(len(xy))])-.1;bound=cfg['amplitude_m']*np.linalg.norm(cfg['axis_xy'])*np.pi/4096;assert margins.min()>bound and np.max(abs(np.asarray(cfg['axis_xy'])*cfg['amplitude_m']*cfg['omega_rad_s']))<=.12
 assert all(sha(repo/n)==h for n,h in dependency_frozen.items())
 assert all(sha(repo/n)==h for n,h in frozen.items());status='GEOMETRY_REACHABILITY_ALL_SAVED_SETS_AND_QUERIES_VERIFIED';dump('RESULT.json',dict(status=status,counts=result['counts'],saved_trajectories=45,all_future_sets_verified=252,maximum_independent_query_error=maxerr,conditional_nonpenetrating_motion_class=True,all_phase_actor_class_verified=True,current_packets=186,new_initializations=0,new_integrations=0,new_robot_predictions=0,new_observations=0,new_navigation=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
