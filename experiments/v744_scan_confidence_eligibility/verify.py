"""Fixed conditional-confidence re-evaluation, no new motion or sensor packets."""
import gzip,hashlib,json,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation';sys.path.insert(0,str(source));sys.path.insert(0,str(repo/'experiments/v727_finite_dropout_reachability'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V744_NO_MODEL_INITIALIZATION_OR_INTEGRATION')
for n in['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from confidence_domain import ConfidenceDomain,ERROR_UPPER,MISS_THRESHOLD,MAX_OPPORTUNITIES,IMPOSSIBLE
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();root=repo/'runs/v744_scan_confidence_eligibility';root.mkdir(exist_ok=False);started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V744_FIXED_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});dump('ROUND_WINDOW.json',window);status='RUNNING';records=[];count=0;maximum_excess=0.
try:
 assert(repo/'REVIEW_PENDING').exists();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());assert read(repo/'runs/v741_preemptive_cycles_audit/RESULT.json')['status']=='PREEMPTIVE_CYCLE_SAVED_EVIDENCE_VERIFIED'and read(repo/'runs/v743_persistent_envelope_audit/RESULT.json')['status']=='DIRECT_ALL_HISTORY_CERTIFICATES_VERIFIED';assert MISS_THRESHOLD==10 and MAX_OPPORTUNITIES==56447 and ERROR_UPPER<=1e-8
 raw=repo/'runs/v740_preemptive_observation_cycles';r=read(raw/'RESULT.json');pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 def clone(d):
  c=ConfidenceDomain(d.origin);c.time=d.time;c.cost=d.cost.copy();c.possible=d.possible.copy();c.distance=d.distance.copy();c.last=dict(d.last);c.updates=d.updates;return c
 def coverage(d):
  global count,maximum_excess
  times=d.time+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);excess=float(d.point_lower(truth,times).max());assert excess<=1e-7;maximum_excess=max(maximum_excess,excess);count+=1
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 base=ConfidenceDomain(p['start_qpos'][:2]);bases={};progress=[]
 for packet in old:
  base.update(packet);coverage(base);progress.append(dict(step=packet['step'],time=base.time,cost_sha256=base.last['counter_sha256'],retained_possible_cells=int(base.possible.sum())))
  if packet['step']in[73,90,130]:
   bases[packet['step']]=clone(base);np.savez_compressed(root/('BASE_%03d.npz'%packet['step']),possible=base.possible,cost=base.cost,time=base.time,origin=base.origin)
 dump('ORIGINAL_PACKETS.json',progress)
 def check(record,d,stage):
  z=np.load(raw/(record['label']+'_PRIVATE.npz'));values=np.minimum(pose_values(static,z['poses']),d.body_lower(z['poses'],d.time+np.arange(1,329)*.01));minimum=float(values.min());margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else'GOAL_PROGRESS'if stage=='ADVANCE'and record['goal_progress_m']<.02 else None
  records.append(dict(label=record['label'],stage=stage,old_admissible=record['admissible'],old_reason=record['reason'],confidence_admissible=reason is None,confidence_reason=reason,old_minimum_causal_m=record['minimum_causal_clearance_m'],confidence_minimum_causal_m=minimum,current_counter_sha256=d.last['counter_sha256'],conditional_confidence_not_deterministic=True,new_fields_used_for_physics=False))
 def actual(record,d):
  with gzip.open(raw/(record['label']+'_OBSERVATIONS.json.gz'),'rt')as f:observations=json.load(f)
  for row in observations:d.update(row['packet']);coverage(d)
 for branch in r['branches']:
  d=clone(bases[branch['step']])
  for cycle in branch['cycles']:
   scan=cycle['scan'];check(scan,d,'SCAN')
   if not scan['admissible']:break
   actual(scan,d)
   for candidate in cycle['successors']:check(candidate,d,'ADVANCE')
   if cycle['selected_successor']is None:break
   selected=next(c for c in cycle['successors']if c['index']==cycle['selected_successor']);actual(selected,d)
 rejected=0
 for invalid in[old[-1],dict(old[-1],step=1201,time=base.time+.08)]:
  try:base.update(invalid)
  except AssertionError:rejected+=1
 assert len(records)==35 and count==423 and rejected==2 and all(sha(repo/n)==h for n,h in freeze['files'].items());flipped=[x['label']for x in records if x['confidence_admissible']and not x['old_admissible']];status='FIXED_CONFIDENCE_SCAN_SAVED_ELIGIBILITY_COMPLETE';dump('RESULT.json',dict(status=status,records=records,admission_flips=flipped,actual_packets=count,forecast_coverage_samples=count*329,maximum_actual_coverage_excess_m=maximum_excess,conditional_task_error_upper=ERROR_UPPER,miss_threshold=MISS_THRESHOLD,maximum_task_ray_opportunities=MAX_OPPORTUNITIES,reused_and_over_budget_queries_rejected=rejected,new_initializations=0,new_integrations=0,new_navigation_samples=0,new_fields_used_for_physics=False,scope='Ideal conditional independent dropout model only; not unconditional PRNG, correlated outage or real-sensor guarantee.'))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
