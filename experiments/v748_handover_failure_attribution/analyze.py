"""Saved evidence only: attribute rejection and inspect causal sensing windows."""
import fcntl,gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'))
sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V748_INITIALIZATION_INTEGRATION_FORBIDDEN')
for name in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
from renewal_state import decode
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v748_handover_failure_attribution';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V748_600S_ABSOLUTE_STOP')));signal.alarm(600)
status='RUNNING';dump('ROUND_WINDOW.json',window)
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 raw=repo/'runs/v746_early_observation_handover';r=read(raw/'RESULT.json');assert read(repo/'runs/v747_early_handover_audit/RESULT.json')['status']=='EARLY_HANDOVER_SAVED_EVIDENCE_VERIFIED'
 p=read(repo/'runs/v735_scan_differential_navigation/main01/paired/STATIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds'])
 static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 candidates=[];scans=[];samples=[]
 for b in r['branches']:
  if not b['scan']['admissible']:continue
  label=b['scan']['label'];a=np.load(raw/(label+'_ACTUAL.npz'))
  with gzip.open(raw/(label+'_OBSERVATIONS.json.gz'),'rt')as f:observations=json.load(f)
  local=[]
  for j,o in enumerate(observations):
   domain=decode(o['domain']);q=a['qpos'][8*j+7];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));pose=np.r_[q[:2],yaw];future=domain.time+np.linspace(0,3.28,329);hold=np.repeat([pose],329,axis=0);line=hold.copy();line[:,:2]+=np.linspace(0,.30,329)[:,None]*np.array([np.cos(yaw),np.sin(yaw)])
   hm=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,future)).min());lm=float(np.minimum(pose_values(static,line),domain.body_lower(line,future)).min())
   row=dict(step=b['step'],amplitude=b['amplitude'],packet_index=j+1,public_step=o['packet']['step'],time=domain.time,hold_geometry_m=hm,forward_030_geometry_m=lm,hold_qualified_geometry_only=hm>=.155,forward_qualified_geometry_only=lm>=.155);samples.append(row);local.append(row)
  for c in b['successors']:
   z=np.load(raw/(c['label']+'_PRIVATE.npz'));times=float(z['initial_time'])+np.arange(1,329)*.01;known=pose_values(static,z['poses']);unknown=domain.body_lower(z['poses'],times);unaged=domain.body_lower(z['poses'],np.full(328,domain.time));combined=np.minimum(known,unknown);assert abs(combined.min()-c['minimum_causal_clearance_m'])<1e-10
   floor=np.flatnonzero(combined<.155);margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]))
   candidates.append(dict(step=b['step'],amplitude=b['amplitude'],index=c['index'],label=c['label'],static_min_m=float(known.min()),future_unknown_min_m=float(unknown.min()),minimum_causal_m=float(combined.min()),first_rejected_native_tick=int(floor[0])+1 if len(floor)else None,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_rad_s=angular,goal_progress_m=c['goal_progress_m'],all_non_temporal_gates_pass=bool(known.min()>=.155 and margin>=.002 and speed<=.025 and angular<=.025 and c['goal_progress_m']>=.02),unaged_counterfactual_min_m=float(np.minimum(known,unaged).min()),unaged_counterfactual_pass=bool(np.minimum(known,unaged).min()>=.155),unaged_used_for_control=False))
  scans.append(dict(step=b['step'],amplitude=b['amplitude'],yaw_sweep_deg=b['scan']['actual_yaw_sweep_rad']*180/np.pi,translation_m=b['scan']['actual_translation_m'],hold_window_packets=[x['packet_index']for x in local if x['hold_qualified_geometry_only']],forward_window_packets=[x['packet_index']for x in local if x['forward_qualified_geometry_only']],maximum_hold_geometry_m=max(x['hold_geometry_m']for x in local),maximum_forward_geometry_m=max(x['forward_030_geometry_m']for x in local),terminal_hold_geometry_m=local[-1]['hold_geometry_m'],terminal_forward_geometry_m=local[-1]['forward_030_geometry_m']))
 assert len(candidates)==35 and len(samples)==287 and len(scans)==7
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 dump('CANDIDATES.json',candidates);dump('OBSERVATION_WINDOWS.json',samples);dump('SCANS.json',scans)
 status='SAVED_HANDOVER_REJECTION_ATTRIBUTION_COMPLETE';dump('RESULT.json',dict(status=status,candidates=len(candidates),all_non_temporal_gate_passes=sum(c['all_non_temporal_gates_pass']for c in candidates),future_unknown_rejections=sum(c['future_unknown_min_m']<.155 for c in candidates),unaged_counterfactual_passes=sum(c['unaged_counterfactual_pass']for c in candidates),actual_observation_packets=len(samples),scans=len(scans),scans_with_intermediate_forward_geometry=sum(bool(s['forward_window_packets'])for s in scans),all_terminal_forward_geometry_rejected=all(s['terminal_forward_geometry_m']<.155 for s in scans),new_initializations=0,new_integrations=0,new_physical_predictions=0,new_navigation=0,geometric_windows_are_not_native_certificates=True,all_counterfactuals_not_used_for_control=True))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
