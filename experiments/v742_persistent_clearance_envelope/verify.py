"""Finite saved-packet eligibility only; no new model or integration."""
import gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation';sys.path.insert(0,str(source));sys.path.insert(0,str(own))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V742_MODEL_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from recursive_domain import RecursiveDomain,AXIS,GRID,LOWER,SPEED,HALF_DIAGONAL,SLACK
from renewal_state import encode
from envelope import Envelope
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();root=repo/'runs/v742_persistent_clearance_envelope';root.mkdir(exist_ok=False);started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V742_FIXED_600S_ABSOLUTE_STOP')));signal.alarm(600);dump('ROUND_WINDOW.json',window);status='RUNNING';records=[];packet_count=0;maxcoverage=-float('inf');max_direct_error=0.;minimum_dominance=float('inf')
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());assert read(repo/'runs/v741_preemptive_cycles_audit/RESULT.json')['status']=='PREEMPTIVE_CYCLE_SAVED_EVIDENCE_VERIFIED'
 raw=repo/'runs/v740_preemptive_observation_cycles';r=read(raw/'RESULT.json');pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 def clone(d):
  out=RecursiveDomain(d.origin);out.time=d.time;out.possible=d.possible.copy();out.distance=d.distance.copy();out.last=dict(d.last);return out
 def truth_check(e,d):
  global packet_count,maxcoverage,minimum_dominance
  times=e.time+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);a=e.point_lower(truth,times);b=d.point_lower(truth,times);maxcoverage=max(maxcoverage,float(a.max()));minimum_dominance=min(minimum_dominance,float((a-b).min()));assert a.max()<=1e-7 and np.all(a>=b-1e-12);packet_count+=1
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};base=RecursiveDomain(p['start_qpos'][:2]);e=Envelope(base.origin);bases={};envelopes={};rng=np.random.default_rng(742);ix=rng.integers(0,len(AXIS),(1001,2));direct=np.zeros(1001);previous_time=0.;direct_samples=[]
 for packet in old:
  base.update(packet);assert encode(base)==beliefs[packet['step']]['free_space_renewal'];e.update(base);now=float(packet['time']);fresh=np.maximum(0.,base.distance[ix[:,0],ix[:,1]]-HALF_DIAGONAL-SLACK);direct=np.maximum(0.,np.maximum(direct-SPEED*(now-previous_time),fresh));error=float(np.max(abs(direct-e.lower[ix[:,0],ix[:,1]])));max_direct_error=max(max_direct_error,error);assert error<=1e-12;previous_time=now;truth_check(e,base)
  direct_samples.append(dict(time=now,fresh=fresh.tolist()))
  if packet['step']in[73,90,130]:bases[packet['step']]=clone(base);envelopes[packet['step']]=e.copy();np.savez_compressed(root/('BASE_%03d.npz'%packet['step']),lower=e.lower,time=e.time,origin=e.origin)
 dump('DIRECT_SAMPLE_INPUTS.json',dict(grid_indices=ix.tolist(),snapshots=direct_samples,maximum_error=max_direct_error))
 def check(record,e,d,stage):
  z=np.load(raw/(record['label']+'_PRIVATE.npz'));times=e.time+np.arange(1,329)*.01;known=pose_values(static,z['poses']);old_values=np.minimum(known,d.body_lower(z['poses'],times));new_values=np.minimum(known,e.body_lower(z['poses'],times));assert abs(old_values.min()-record['minimum_causal_clearance_m'])<=1e-8 and np.all(new_values>=old_values-1e-12)
  margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));progress=float(record['goal_progress_m']);reason='TIME_CLEARANCE'if new_values.min()<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else'GOAL_PROGRESS'if stage=='ADVANCE'and progress<.02 else None
  rec=dict(label=record['label'],stage=stage,old_reason=record['reason'],new_reason=reason,old_admissible=record['admissible'],new_admissible=reason is None,old_minimum_clearance_m=float(old_values.min()),new_minimum_clearance_m=float(new_values.min()),gain_m=float(new_values.min()-old_values.min()),saved_trajectory_only=True,new_observations_for_unexecuted_branch=False);records.append(rec);np.savez_compressed(root/(record['label']+'_GEOMETRY.npz'),old_values=old_values,new_values=new_values,known_values=known)
 def update_actual(record,e,d):
  with gzip.open(raw/(record['label']+'_OBSERVATIONS.json.gz'),'rt')as stream:obs=json.load(stream)
  for row in obs:
   d.update(row['packet']);assert encode(d)==row['domain'];e.update(d);truth_check(e,d)
  return e,d
 for b in r['branches']:
  d=clone(bases[b['step']]);e=envelopes[b['step']].copy()
  for cycle in b['cycles']:
   scan=cycle['scan'];check(scan,e,d,'SCAN')
   if not scan['admissible']:break
   e,d=update_actual(scan,e,d)
   for candidate in cycle['successors']:check(candidate,e,d,'ADVANCE')
   if cycle['selected_successor']is None:break
   selected=next(c for c in cycle['successors']if c['index']==cycle['selected_successor']);e,d=update_actual(selected,e,d)
 assert len(records)==35 and packet_count==423 and all(sha(repo/n)==h for n,h in freeze['files'].items())
 # A future packet cannot be used to issue an earlier certificate.
 rejected=0
 for offset in[1e-4,.08,3.28]:
  try:e.point_lower([[0.,0.]],[e.time-offset])
  except AssertionError:rejected+=1
 assert rejected==3 and float(e.point_lower([[100.,100.]],[e.time])[0])==0.
 status='PERSISTENT_CERTIFICATE_SAVED_ELIGIBILITY_COMPLETE';dump('RESULT.json',dict(status=status,records=records,saved_complete_trajectories=len(records),newly_admissible=[x['label']for x in records if x['new_admissible']and not x['old_admissible']],original_packets=len(old),all_packets=packet_count,forecast_coverage_samples=packet_count*329,maximum_actual_coverage_excess_m=maxcoverage,minimum_actual_pointwise_dominance_m=minimum_dominance,direct_grid_recurrence_maximum_error=max_direct_error,noncausal_queries_rejected=rejected,new_initializations=0,new_integrations=0,new_navigation_samples=0,probability_assumption_added=False,new_fields_used_for_physics=False))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
