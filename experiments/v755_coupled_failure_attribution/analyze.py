"""Attribute saved certificate failures, separating static geometry and unknowns."""
import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'))
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V755_INITIALIZATION_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from exact_footprint import pose_values
from renewal_state import decode
from free_certificate import body_points,old_lower
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v755_coupled_failure_attribution';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+300,limit_s=300,round_closed=False);dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V755_300S_ABSOLUTE_STOP')));signal.alarm(300);status='RUNNING'
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 raw=repo/'runs/v753_coupled_progress_repaired';r=read(raw/'RESULT.json');assert read(repo/'runs/v754_coupled_progress_repaired_audit/RESULT.json')['status']=='COUPLED_PROGRESS_SAVED_EVIDENCE_VERIFIED'
 cell=repo/'runs/v735_scan_differential_navigation/main01/paired/geometry_memory';p=read(cell.parent/'STATIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};baseline=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz');initial=baseline['qpos'][-1]
 static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 records=[];branches=[]
 for b in r['branches']:
  a=np.load(raw/(b['name']+'_ACTUAL.npz'))
  with gzip.open(raw/(b['name']+'_OBSERVATIONS.json.gz'),'rt')as f:observations=json.load(f)
  failed=[]
  for d in b['decisions']:
   k=d['local_public'];domain=decode(beliefs[32]['free_space_renewal']if k==0 else observations[k-1]['domain']);z=np.load(raw/(d['label']+'_PRIVATE.npz'));times=float(z['initial_time'])+np.arange(1,329)*.01;known=pose_values(static,z['poses']);unknown=domain.body_lower(z['poses'],times);combined=np.minimum(known,unknown);assert abs(combined.min()-d['minimum_causal_clearance_m'])<=1e-10
   points,cover=body_points(z['poses']);recursive=domain.point_lower(points,times[:,None]).min(axis=1)-cover-.10;prior=old_lower(z['poses'],times,domain.origin);assert np.max(abs(unknown-np.maximum(recursive,prior)))<=1e-12
   unaged=domain.body_lower(z['poses'],np.full(328,domain.time));static_fail=bool(known.min()<.155);unknown_fail=bool(unknown.min()<.155);cause='BOTH_STATIC_AND_FUTURE_UNKNOWN'if static_fail and unknown_fail else'KNOWN_STATIC_GEOMETRY'if static_fail else'FUTURE_UNKNOWN_DOMAIN'if unknown_fail else'NO_CLEARANCE_REJECTION';i=int(np.argmin(combined));margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));first=np.flatnonzero(combined<.155)
   assert d['reason']is None or d['reason']=='TIME_CLEARANCE';assert margin>=.002 and speed<=.025 and angular<=.025
   record=dict(profile=b['profile'],label=d['label'],local_public=k,elapsed_s=k*.08,admissible=d['admissible'],reason=d['reason'],cause=cause,static_min_m=float(known.min()),future_unknown_min_m=float(unknown.min()),combined_min_m=float(combined.min()),critical_tick=i+1,critical_static_m=float(known[i]),critical_recursive_m=float(recursive[i]),critical_initial_prior_m=float(prior[i]),initial_prior_active_at_critical=bool(prior[i]>=recursive[i]),first_rejected_native_tick=int(first[0])+1 if len(first)else None,unaged_counterfactual_min_m=float(np.minimum(known,unaged).min()),unaged_counterfactual_pass=bool(np.minimum(known,unaged).min()>=.155),unaged_counterfactual_used_for_control=False,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular)
   records.append(record)
   if not d['admissible']:failed.append((record,z))
  assert len(failed)==1;failure,z=failed[0];progress_before=float(np.linalg.norm(initial[:2]-p['goal_xy'])-np.linalg.norm(z['initial_qpos'][:2]-p['goal_xy']));progress_final=b['final_goal_progress_m'];yaw=np.unwrap(np.arctan2(2*(a['qpos'][:,3]*a['qpos'][:,6]+a['qpos'][:,4]*a['qpos'][:,5]),1-2*(a['qpos'][:,5]**2+a['qpos'][:,6]**2)));branches.append(dict(profile=b['profile'],accepted_refreshes=b['accepted_refreshes'],first_rejected_local_public=failure['local_public'],last_new_certificate_elapsed_s=failure['elapsed_s'],cause=failure['cause'],static_min_m=failure['static_min_m'],future_unknown_min_m=failure['future_unknown_min_m'],minimum_certificate_m=failure['combined_min_m'],first_rejected_native_tick=failure['first_rejected_native_tick'],critical_recursive_m=failure['critical_recursive_m'],critical_initial_prior_m=failure['critical_initial_prior_m'],initial_prior_active_at_critical=failure['initial_prior_active_at_critical'],unaged_counterfactual_pass=failure['unaged_counterfactual_pass'],goal_progress_before_rejection_m=progress_before,goal_progress_in_retained_tail_m=progress_final-progress_before,final_goal_progress_m=progress_final,total_actual_yaw_range_deg=float(np.ptp(yaw)*180/np.pi),actual_public_steps=b['public_steps'],complete_four_scheduled_legs=False))
 assert len(records)==32 and len(branches)==3
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());dump('DECISIONS.json',records);dump('BRANCHES.json',branches);status='SAVED_COUPLED_REJECTION_ATTRIBUTION_COMPLETE';dump('RESULT.json',dict(status=status,profiles=branches,all_decisions=len(records),all_self_terminal_gates_pass=True,static_rejected_profiles=sum(x['cause']in ['KNOWN_STATIC_GEOMETRY','BOTH_STATIC_AND_FUTURE_UNKNOWN']for x in branches),future_unknown_rejected_profiles=sum(x['cause']in ['FUTURE_UNKNOWN_DOMAIN','BOTH_STATIC_AND_FUTURE_UNKNOWN']for x in branches),unaged_counterfactual_passes=sum(x['unaged_counterfactual_pass']for x in branches),counterfactual_not_used_for_control=True,new_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
