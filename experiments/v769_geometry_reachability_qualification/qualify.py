"""All saved inputs; no new model/robot steps or sensor readings."""
import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback,gc
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(0,str(own));sys.path.insert(2,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def no(*a,**k):raise RuntimeError('V769_NO_MODEL_OR_INTEGRATION')
for key in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,key,no)
from recursive_domain import RecursiveDomain,AXIS,GRID,LOWER
from renewal_state import encode
from self_geometry import containment_margin
from exact_footprint import pose_values
from map_domain import MapDomain,static_mask,future_fields,future_body,distance_lower
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v769_geometry_reachability_qualification';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0);dump('ROUND_WINDOW.json',window);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V769_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});status='RUNNING'
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 assert read(repo/'runs/v768_certified_progress_release_audit/RESULT.json')['status']=='CERTIFIED_PROGRESS_RELEASE_SAVED_EVIDENCE_VERIFIED'
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));pointfield=SimpleNamespace(**{**static.__dict__,'half':np.zeros(2),'center_local':np.zeros(2)})
 def truth(times):return np.asarray(cfg['anchor_xy'])+np.sin(np.asarray(times)*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy'])
 theta=np.linspace(0,2*np.pi,4097);xy=np.asarray(cfg['anchor_xy'])+np.sin(theta)[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy']);margins=pose_values(pointfield,np.c_[xy,np.zeros(len(xy))])-.1;lipschitz=cfg['amplitude_m']*np.linalg.norm(cfg['axis_xy'])*(2*np.pi/4096)/2;axis_speed=abs(np.asarray(cfg['axis_xy'])*cfg['amplitude_m']*cfg['omega_rad_s']);assert margins.min()>lipschitz and np.max(axis_speed)<=.12
 dump('ACTOR_CLASS_AUDIT.json',dict(conditional_motion_class='radius.1 nonpenetrating known map each_axis_speed<=.12',minimum_full_phase_static_margin_m=float(margins.min()),continuous_phase_interpolation_bound_m=float(lipschitz),maximum_axis_speed_m_s=axis_speed.tolist(),truth_for_evaluation_only=True,not_assumed_for_unrestricted_phantom_motion=True))
 allowed=static_mask(p);np.savez_compressed(root/'ALLOWED_CELLS.npz',shape=allowed.shape,bits=np.packbits(allowed,bitorder='little'))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f][:33]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 raw=repo/'runs/v767_certified_progress_release';branch=read(raw/'FEEDBACK_MAIN_SUMMARY.json');decisions={x['local_public']:x for x in branch['decisions']}
 with gzip.open(raw/'FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as f:obs=json.load(f)
 oldd=RecursiveDomain(p['start_qpos'][:2]);mapped=MapDomain(oldd.origin,allowed);checkpoints={};allpackets=old+[x['packet']for x in obs];count=0
 for j,packet in enumerate(allpackets):
  oldd.update(packet);mapped.update(packet);expected=beliefs[packet['step']]['free_space_renewal']if j<33 else obs[j-33]['domain'];assert encode(oldd)==expected
  assert np.all(~mapped.possible|oldd.possible),'MAPPED_DOMAIN_NOT_SUBSET_OF_ORIGINAL'
  actual=truth([packet['time']])[0];idx=np.rint((actual-LOWER)/GRID).astype(int);assert allowed[tuple(idx)]and mapped.possible[tuple(idx)]and oldd.possible[tuple(idx)]
  count+=1;local=packet['step']-32
  if local in [64,96,116]:
   checkpoints[local]=(oldd.possible.copy(),mapped.possible.copy(),oldd.distance.copy(),mapped.distance.copy(),oldd.time)
   np.savez_compressed(root/('STATE_%03d.npz'%local),old_bits=np.packbits(oldd.possible,bitorder='little'),map_bits=np.packbits(mapped.possible,bitorder='little'),shape=allowed.shape,time=oldd.time,origin=oldd.origin)
 assert count==186 and len(checkpoints)==3
 records=[];coverage=[]
 for local,(original,mp,original_distance,map_distance,when)in checkpoints.items():
  oldd.possible=original;oldd.distance=original_distance;oldd.time=when;mapped.possible=mp;mapped.distance=map_distance;mapped.time=when
  times=when+np.arange(1,329)*.01;xy=truth(times);idx=np.rint((xy-LOWER)/GRID).astype(int);assert np.all(allowed[idx[:,0],idx[:,1]])
  saved={};labels=[]
  for c in decisions[local]['candidates']:
   z=np.load(raw/(c['label']+'_PRIVATE.npz'));known=pose_values(static,z['poses']);av=np.minimum(known,oldd.body_lower(z['poses'],times));bv=np.minimum(known,mapped.body_lower(z['poses'],times));assert abs(av.min()-c['minimum_causal_clearance_m'])<1e-10
   saved[c['action_index']]=dict(candidate=c,z=z,known=known,A=av,B=bv)
  for variant,possible,mask in [('C',mp,allowed),('D',original,None)]:
   sets,fields=future_fields(possible,mask);bits=np.stack([np.packbits(x,bitorder='little')for x in sets]);np.savez_compressed(root/('FUTURE_%03d_%s.npz'%(local,variant)),bits=bits,shape=allowed.shape,bucket_s=.08,origin=p['start_qpos'][:2],time=when)
   bucket=np.ceil(np.arange(1,329)/8).astype(int);assert all(sets[b][tuple(ii)]for b,ii in zip(bucket,idx)),'FUTURE_TRUE_CENTER_NOT_IN_OUTER_SET'
   for b in range(1,42):
    keep=bucket==b;lower=distance_lower(fields[b],xy[keep]);assert float(lower.max())<=1e-7
   coverage.append(dict(local_public=local,variant=variant,future_native_queries=328,complete_true_center_cells_covered=True))
   for i,d in saved.items():d[variant]=np.minimum(d['known'],future_body(fields,d['z']['poses']))
   del sets,fields,bits;gc.collect()
  for i,d in saved.items():
   c=d['candidate'];z=d['z'];margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));gate=margin>=.002 and speed<=.025 and angular<=.025
   rec=dict(local_public=local,action_index=i,label=c['label'],target=c['target'],original_admissible=c['admissible'],goal_progress_m=c['goal_progress_m'],non_clearance_gates_pass=gate,minimum={v:float(d[v].min())for v in ['A','B','C','D']},admissible={v:bool(d[v].min()>=.155 and gate)for v in ['A','B','C','D']},not_used_for_control=True);records.append(rec);np.savez_compressed(root/('QUERY_%03d_%02d.npz'%(local,i)),**{v:d[v]for v in ['A','B','C','D']})
  dump('PROGRESS.json',dict(completed_states=local,records=len(records)))
 assert len(records)==45;counts={str(k):{v:sum(x['admissible'][v]for x in records if x['local_public']==k)for v in ['A','B','C','D']}for k in [64,96,116]}
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='SAVED_GEOMETRY_REACHABILITY_QUALIFICATION_COMPLETE';dump('RECORDS.json',records);dump('RESULT.json',dict(status=status,states=[64,96,116],counts=counts,all_actual_packets=count,current_truth_cells_covered=186,future_coverage=coverage,conditional_nonpenetrating_map_motion_class=True,new_initializations=0,new_integrations=0,new_robot_predictions=0,new_observations=0,new_navigation=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
