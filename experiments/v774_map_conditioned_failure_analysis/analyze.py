import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'runs/v771_audit_dependencies/site'))
from scipy.spatial import cKDTree
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(0,str(repo/'experiments/v773_map_conditioned_progress_audit'));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def no(*a,**k):raise RuntimeError('V774_NO_MODEL_OR_INTEGRATION')
for k in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,k,no)
from independent_domain import IndependentDomain
from renewal_state import decode
from free_certificate import body_points,reliable_rays,free_samples,old_lower
from exact_footprint import pose_values
from recursive_domain import GRID,LOWER,HALF_DIAGONAL
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v774_map_conditioned_failure_analysis';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False);dump('ROUND_WINDOW.json',window);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V774_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});status='RUNNING'
def yaw(q):return np.arctan2(2*(q[...,3]*q[...,6]+q[...,4]*q[...,5]),1-2*(q[...,5]**2+q[...,6]**2))
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/n)==h for n,h in freeze.items());assert read(repo/'runs/v773_map_conditioned_progress_audit/RESULT.json')['status']=='MAP_CONDITIONED_PROGRESS_SAVED_EVIDENCE_VERIFIED'
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f][:33]
 raw=repo/'runs/v772_map_conditioned_progress';baseline=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz')['qpos'][-1];records=[];branches=[];history_records=[]
 for profile in ['MAP_HISTORY','MAP_FUTURE']:
  b=read(raw/(profile+'_MAIN_SUMMARY.json'));d=b['decisions'][-1];local=d['local_public'];a=np.load(raw/(profile+'_MAIN_ACTUAL.npz'))
  with gzip.open(raw/(profile+'_MAIN_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
  domain=IndependentDomain(p['start_qpos'][:2],p,profile)
  for packet in old+[x['packet']for x in obs[:local]]:domain.update(packet)
  if profile=='MAP_FUTURE':sets,fields=domain.future()
  current_possible_points=LOWER+GRID*np.argwhere(domain.possible);current_tree=cKDTree(current_possible_points);witnesses=[]
  times=domain.time+np.arange(1,329)*.01
  for c in d['candidates']:
   z=np.load(raw/(c['label']+'_PRIVATE.npz'));known=pose_values(static,z['poses']);unknown=domain.body_lower(z['poses'],times);value=np.minimum(known,unknown);assert abs(value.min()-c['minimum_causal_clearance_m'])<=1e-10;tick=int(np.argmin(value));first=np.flatnonzero(value<.155);points,cover=body_points(z['poses'][tick:tick+1]);lower=domain.point_lower(points,np.array([[times[tick]]]))[0];j=int(np.argmin(lower));bodypoint=points[0,j];gridpoint=LOWER+GRID*np.rint((bodypoint-LOWER)/GRID);dist,idx=current_tree.query(gridpoint);witness=current_possible_points[int(idx)]
   rec=dict(profile=profile,local_public=local,action_index=c['action_index'],target=c['target'],static_min_m=float(known.min()),unknown_min_m=float(unknown.min()),combined_min_m=float(value.min()),first_rejected_native_tick=int(first[0])+1 if len(first)else None,critical_native_tick=tick+1,current_nearest_possible_center=witness.tolist(),current_body_cover_point=bodypoint.tolist(),current_center_distance_m=float(dist),witness_is_true_actor=False,actual_control_executed=False)
   if profile=='MAP_FUTURE':
    fut=domain.future_point_lower(points,np.array([times[tick]]))[0];jj=int(np.argmin(fut));bp=points[0,jj];gp=LOWER+GRID*np.rint((bp-LOWER)/GRID);bucket=int(domain.buckets([times[tick]])[0]);tree=cKDTree(LOWER+GRID*np.argwhere(sets[bucket]));distance,idx=tree.query(gp);pos=tree.data[int(idx)];rec.update(future_bucket=bucket,future_nearest_possible_center=pos.tolist(),future_body_cover_point=bp.tolist(),future_center_distance_m=float(distance))
   records.append(rec);witnesses.append(witness)
  unique=np.unique(np.asarray(witnesses),axis=0);packets=old+[x['packet']for x in obs[:local]]
  for center in unique:
   row=[]
   for pkt in packets:
    rays=reliable_rays(pkt);samples=free_samples(rays);distance=float(np.linalg.norm(samples-center,axis=1).min())if len(samples)else 99.;excluded=distance<.1-1e-4-HALF_DIAGONAL
    row.append(dict(public_step=pkt['step'],local_public=pkt['step']-32,nearest_reliable_prefix_sample_m=distance,center_cell_fully_excluded_by_this_packet=bool(excluded),reliable_ray_count=len(rays),lidar_maxrange_count=sum(x>=1. for x in pkt['lidar']),depth_maxrange_count=sum(x>=1. for x in pkt['depth'])))
   history_records.append(dict(profile=profile,witness_center=center.tolist(),witness_is_true_actor=False,all_packet_nearest_distance_m=min(x['nearest_reliable_prefix_sample_m']for x in row),number_packets_directly_excluding_cell=sum(x['center_cell_fully_excluded_by_this_packet']for x in row),latest_direct_excluding_local_public=max([x['local_public']for x in row if x['center_cell_fully_excluded_by_this_packet']]or[-33]),last32=row[-32:],all_packets=row))
  q=a['qpos'][local*8-1];goal=np.asarray(p['goal_xy']);progress=float(np.linalg.norm(baseline[:2]-goal)-np.linalg.norm(q[:2]-goal));diff=np.asarray([x['target'][2]-x['target'][3]for x in b['decisions']if x['admissible']]);angle=np.unwrap(np.r_[yaw(baseline),yaw(a['qpos'][:local*8])]);final=[x for x in records if x['profile']==profile]
  branches.append(dict(profile=profile,active_public=local,public_steps=b['public_steps'],accepted_refreshes=b['accepted_refreshes'],attempted_refreshes=b['attempted_refreshes'],actual_goal_progress_before_tail_m=progress,final_goal_progress_m=b['final_goal_progress_m'],actual_after_release_goal_progress_m=b['goal_progress_after_release_m'],target_turn_sign_flips=int(np.sum(diff[:-1]*diff[1:]<0)),actual_active_yaw_range_deg=float(np.rad2deg(np.ptp(angle))),last_static_rejections=sum(x['static_min_m']<.155 for x in final),last_unknown_rejections=sum(x['unknown_min_m']<.155 for x in final),last_terminal_tick_rejections=sum(x['critical_native_tick']==328 for x in final),repeat_executed=False))
 assert len(records)==30;dump('CANDIDATES.json',records);dump('RAY_HISTORIES.json',history_records);status='MAP_CONDITIONED_FAILURE_SAVED_EVIDENCE_ATTRIBUTED';dump('RESULT.json',dict(status=status,branches=branches,last_candidates=30,unique_current_witnesses=len(history_records),new_initializations=0,new_integrations=0,new_robot_predictions=0,new_observations=0,new_navigation=0,not_a_global_impossibility_proof=True))
 assert all(sha(repo/n)==h for n,h in freeze.items())
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
