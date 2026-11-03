"""Attribute frozen-prediction rejection; no new motion or optimistic execution."""
import hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation';sys.path.insert(0,str(source))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V739_NO_INITIALIZATION_OR_INTEGRATION')
for name in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,name,forbidden)
from exact_footprint import pose_values
from unseen_prior import clearance
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v739_joint_return_failure_analysis';root.mkdir(exist_ok=False);raw=repo/'runs/v737_joint_return_qualification';pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';start=time.time();window=dict(started_unix=start,absolute_deadline_unix=start+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V739_FIXED_300S_STOP')));signal.alarm(300);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});dump('ROUND_WINDOW.json',window);status='RUNNING'
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def first_below(values):
 ticks=np.flatnonzero(values<.155);return None if not len(ticks)else int(ticks[0])+1
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());assert(repo/'REVIEW_PENDING').exists()and read(repo/'runs/v738_joint_return_saved_audit/RESULT.json')['status']=='ALL_FIXED_JOINT_RETURN_EVIDENCE_VERIFIED'
 result=read(raw/'RESULT.json');protocol=read(pair/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 beliefs={r['step']:{k:v for k,v in r.items()if k!='step'}for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};records=[];curves=[]
 for r in result['records']:
  step=r['step'];state=beliefs[step];prefix=np.load(raw/(r['label']+'_PREFIX.npz'))
  for index,tail in enumerate(r['detail']['candidates']):
   data=np.load(raw/(r['label']+'_TAIL_%02d.npz'%index));q=np.vstack([prefix['qpos'],data['qpos']]);v=np.vstack([prefix['qvel'],data['qvel']]);p=poses(q);dt=np.arange(1,329)*.01;known=pose_values(field,p);dynamic=clearance(field,p,state,dt);unaged=clearance(field,p,state,np.zeros(328));actual=np.minimum(known,dynamic);optimistic=np.minimum(known,unaged)
   margin=min(float(containment_margin(prefix['self_bounds'],bounds).min()),float(containment_margin(data['self_bounds'],bounds).min()));speed=float(np.linalg.norm(v[-1,:2]));assert abs(actual.min()-tail['minimum_clearance_m'])<=1e-8
   slow=np.flatnonzero(np.linalg.norm(v[:,:2],axis=1)>.025);last_moving_tick=None if not len(slow)else int(slow[-1])+1
   record=dict(step=step,rank=r['rank'],tail_index=index,kind=tail['kind'],minimum_known_static_m=float(known.min()),minimum_original_causal_m=float(actual.min()),minimum_current_information_no_future_aging_m=float(optimistic.min()),self_margin_m=margin,terminal_speed_m_s=speed,first_original_below_floor_tick=first_below(actual),first_static_below_floor_tick=first_below(known),first_unaged_below_floor_tick=first_below(optimistic),first_240_minimum_original_causal_m=float(actual[:240].min()),last_moving_tick=last_moving_tick,all_328_static_passed=bool(known.min()>=.155),current_information_without_future_aging_passed=bool(optimistic.min()>=.155),original_rejection=tail['reason'],unaged_counterfactual_used_for_execution=False)
   records.append(record);curves.append(np.stack([known,dynamic,unaged,actual,optimistic],axis=0))
  dump('PROGRESS.json',dict(completed_commands=len({(r['step'],r['rank'])for r in records}),tails=len(records)))
 summaries=[]
 for step in [140,144,148]:
  rs=[x for x in records if x['step']==step];best=max(rs,key=lambda x:x['minimum_original_causal_m']);summaries.append(dict(step=step,tails=len(rs),known_static_passes=sum(x['all_328_static_passed']for x in rs),unaged_information_passes=sum(x['current_information_without_future_aging_passed']for x in rs),self_and_terminal_passes=sum(x['self_margin_m']>=.002 and x['terminal_speed_m_s']<=.025 for x in rs),ordinary_horizon_240_clearance_passes=sum(x['first_240_minimum_original_causal_m']>=.155 for x in rs),original_full_328_passes=sum(x['minimum_original_causal_m']>=.155 for x in rs),all_original_reasons_time_clearance=all(x['original_rejection']=='TIME_CLEARANCE'for x in rs),best_saved_tail=best))
 hold=[];oldrows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];laststate=read(cell/'rejected_control.json')
 for step in [32,73,90,97,130,135,136,140,144,148,152,176]:
  q=np.asarray(oldrows[step-1]['qpos_full']);p=np.repeat(poses(q[None,:]),329,axis=0);state=beliefs[step];dt=np.linspace(0,3.28,329);values=np.minimum(pose_values(field,p),clearance(field,p,state,dt));below=np.flatnonzero(values<.155);hold.append(dict(step=step,time=state['time'],current_hold_geometry_clearance_m=float(values[0]),minimum_3_28s_geometry_hold_m=float(values.min()),first_below_floor_after_s=None if not len(below)else float(dt[below[0]]),geometric_pose_hold_not_a_native_control_proof=True))
 np.savez_compressed(root/'SAVED_TAIL_ATTRIBUTION_CURVES.npz',curves=np.asarray(curves),channel_names=np.array(['known_static','original_dynamic','unaged_dynamic','original_joint','unaged_joint']))
 assert len(records)==567 and all(sha(repo/n)==h for n,h in freeze['files'].items());status='FIXED_JOINT_REJECTION_ATTRIBUTION_COMPLETE';dump('RESULT.json',dict(status=status,summaries=summaries,records=records,hold_geometry_timeline=hold,unaged_values_are_not_future_certificates=True,new_initializations=0,new_integrations=0,new_navigation_samples=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-start);dump('ROUND_WINDOW.json',window)
