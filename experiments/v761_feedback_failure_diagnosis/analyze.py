"""Saved-state attribution and controller execution/forecast mismatch in objective."""
import gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def no(*a,**k):raise RuntimeError('NO_NEW_MODEL_OR_PHYSICS')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,no)
from renewal_state import decode
from exact_footprint import pose_values
from free_certificate import body_points,old_lower,reliable_rays
from recursive_domain import AXIS,GRID,LOWER,HALF_DIAGONAL
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v761_feedback_failure_diagnosis';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False);dump('ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V761_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});status='RUNNING'
def yaw(q):return np.arctan2(2*(q[...,3]*q[...,6]+q[...,4]*q[...,5]),1-2*(q[...,5]**2+q[...,6]**2))
def center_static_margin(xy,protocol):
 x=np.asarray(xy);result=min(x[0]+5,5-x[0],x[1]+5,5-x[1])-.1
 for row in protocol['known_rectangles']:
  delta=np.abs(x-np.asarray(row[:2]))-np.asarray(row[2:]);dist=float(np.linalg.norm(np.maximum(delta,0)))if np.max(delta)>0 else float(np.max(delta));result=min(result,dist-.1)
 for row in protocol['known_circles']:result=min(result,float(np.linalg.norm(x-np.asarray(row[:2])))-row[2]-.1)
 return result
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 assert read(repo/'runs/v760_state_feedback_execution_audit/RESULT.json')['status']=='STATE_FEEDBACK_SAVED_EVIDENCE_VERIFIED'
 raw=repo/'runs/v759_state_feedback_execution';r=read(raw/'RESULT.json');b=r['branches'][0];a=np.load(raw/'FEEDBACK_MAIN_ACTUAL.npz');baseline=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz');initial=baseline['qpos'][-1];cell=repo/'runs/v735_scan_differential_navigation/main01/paired/geometry_memory';p=read(cell.parent/'STATIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
 with gzip.open(raw/'FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as f:obs=json.load(f)
 field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 records=[];selections=[];witnesses=[]
 for d in b['decisions']:
  k=d['local_public'];domain=decode(beliefs[32]['free_space_renewal']if k==0 else obs[k-1]['domain']);timevals=domain.time+np.arange(1,329)*.01
  for c in d['candidates']:
   z=np.load(raw/(c['label']+'_PRIVATE.npz'));known=pose_values(field,z['poses']);unknown=domain.body_lower(z['poses'],timevals);combined=np.minimum(known,unknown);assert abs(combined.min()-c['minimum_causal_clearance_m'])<1e-10
   staticfail=bool(known.min()<.155);unknownfail=bool(unknown.min()<.155);unaged=domain.body_lower(z['poses'],np.full(328,domain.time));rec=dict(local_public=k,action_index=c['action_index'],target=c['target'],admissible=c['admissible'],goal_progress_m=c['goal_progress_m'],static_min_m=float(known.min()),unknown_min_m=float(unknown.min()),static_rejected=staticfail,unknown_rejected=unknownfail,unaged_counterfactual_pass=bool(min(known.min(),unaged.min())>=.155),counterfactual_used=False);records.append(rec)
   if d is b['decisions'][-1]:
    tick=int(np.argmin(combined));points,cover=body_points(z['poses'][tick:tick+1]);lower=domain.point_lower(points,np.array([[timevals[tick]]]))[0];j=int(np.argmin(lower));point=points[0,j];grid_idx=np.rint((point-LOWER)/GRID).astype(int);grid_point=LOWER+grid_idx*GRID;possible_idx=np.argwhere(domain.possible);dist2=np.sum((possible_idx-grid_idx)**2,axis=1);ij=possible_idx[int(np.argmin(dist2))];center=LOWER+ij*GRID
    witness=dict(action_index=c['action_index'],critical_tick=tick+1,body_cover_point=point.tolist(),nearest_possible_center=center.tolist(),nearest_center_static_clearance_m=center_static_margin(center,p),nearest_center_physically_intersects_known_static=center_static_margin(center,p)<0,geometric_distance_m=float(np.linalg.norm(center-grid_point)),domain_grid_distance_m=float(domain.distance[tuple(grid_idx)]),center_is_actual_truth=False)
    assert abs(witness['geometric_distance_m']-witness['domain_grid_distance_m'])<1e-10;witnesses.append(witness)
  z=np.load(raw/(d['label']+'_PRIVATE.npz'));end=min(k+4,len(a['qpos'])//8);segment=a['qpos'][k*8:end*8];before=initial if k==0 else a['qpos'][k*8-1];actual_change=float(np.rad2deg(np.arctan2(np.sin(yaw(segment[-1])-yaw(before)),np.cos(yaw(segment[-1])-yaw(before)))))if len(segment)else 0.;forecast_change=float(np.rad2deg(np.arctan2(np.sin(yaw(z['qpos'][-1])-yaw(before)),np.cos(yaw(z['qpos'][-1])-yaw(before)))))
  selections.append(dict(local_public=k,target=d['target'],admissible=d['admissible'],eligible_count=len(d['ranking']),predicted_goal_progress_m=d['goal_progress_m'],actual_next4_yaw_deg=actual_change,full328_predicted_yaw_deg=forecast_change,actual_next4_rear_controls=a['controls'][k*8:end*8:8,2:].tolist()))
 active=next(d['local_public']for d in b['decisions']if not d['admissible']);q=a['qpos'][active*8-1];before_progress=float(np.linalg.norm(initial[:2]-p['goal_xy'])-np.linalg.norm(q[:2]-p['goal_xy']));targetdiff=np.array([d['target'][2]-d['target'][3]for d in b['decisions']if d['admissible']]);signflips=int(np.sum(targetdiff[:-1]*targetdiff[1:]<0));activeyaw=np.unwrap(np.r_[yaw(initial),yaw(a['qpos'][:active*8])]);final=[x for x in records if x['local_public']==active]
 dump('CANDIDATES.json',records);dump('SELECTIONS.json',selections);dump('CRITICAL_WITNESSES.json',witnesses)
 status='SAVED_STATE_FEEDBACK_FAILURE_ATTRIBUTION_COMPLETE';dump('RESULT.json',dict(status=status,decisions=len(b['decisions']),candidates=len(records),first_no_candidate_public=active,active_goal_progress_m=before_progress,final_goal_progress_m=b['final_goal_progress_m'],fallback_goal_progress_m=b['final_goal_progress_m']-before_progress,active_yaw_range_deg=float(np.rad2deg(np.ptp(activeyaw))),selected_target_turn_sign_flips=signflips,last_candidates_static_rejected=sum(x['static_rejected']for x in final),last_candidates_unknown_rejected=sum(x['unknown_rejected']for x in final),last_candidates_unaged_counterfactual_passes=sum(x['unaged_counterfactual_pass']for x in final),nearest_unknown_inside_known_solid=sum(x['nearest_center_physically_intersects_known_static']for x in witnesses),candidate_count_last=len(final),all_counterfactuals_not_executed=True,new_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0))
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
