"""Zero-model qualification of an explicitly declared course norm-speed cap."""
import gzip,json,hashlib,signal,sys,time,os
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;sys.path.insert(0,str(own));sys.path.insert(0,str(repo/'runs/v771_audit_dependencies/site'))
from risk_domain import RiskDomain
from independent_domain import IndependentDomain
from renewal_state import encode,decode
from exact_footprint import pose_values
from unseen_prior import set_public_origin
root=repo/'runs/v787_speed_prior_qualification';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());started=time.time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V787_ZERO_MODEL_300S')));signal.alarm(300);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
raw=repo/'runs/v786_global_forward_curve/main01/paired';cell=raw/'geometry_memory';protocol=read(raw/'STATIC_PROTOCOL.json');config=read(raw/'DYNAMIC_PROTOCOL.json');set_public_origin(protocol['start_qpos'][:2]);actual_bound=float(config['amplitude_m']*config['omega_rad_s']*np.linalg.norm(config['axis_xy']));assert actual_bound<=.08+1e-12
with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
a=RiskDomain(protocol['start_qpos'][:2],protocol,'MAP_HISTORY');b=IndependentDomain(protocol['start_qpos'][:2],protocol,'MAP_HISTORY');by_step={};coverage=[]
try:
 for packet in packets:
  a.update(packet);b.update(packet);state=encode(a);assert state==encode(b)and state['conservative_norm_speed_bound']==.08
  ts=a.time+np.linspace(0,3.28,329);true=np.asarray(config['anchor_xy'])+np.sin(ts*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);excess=float(a.point_lower(true,ts).max());assert excess<=1e-7
  by_step[packet['step']]=state;coverage.append(excess)
 # Deterministic interval implication, with boundary-near samples; no inference from actor position.
 fractions=np.array([-.5,-.499999,0,.499999,.5])*.01;dt=.08
 for start in fractions:
  for displacement in np.linspace(-.08*dt,.08*dt,129):assert abs(int(np.rint((start+displacement)/.01))-int(np.rint(start/.01)))<=1
 bb=np.asarray(protocol['footprint_bounds']);field=SimpleNamespace(half=(bb[2:]-bb[:2])/2,center_local=(bb[2:]+bb[:2])/2,rectangles=np.asarray(protocol['known_rectangles']),circles=np.asarray(protocol['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));records=[]
 for file in sorted((cell/'retained_reentry').glob('step????.json')):
  x=read(file);d=decode(by_step[x['step']]);candidates=[]
  for c in x['records']:
   z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));values=np.minimum(pose_values(field,z['poses']),d.body_lower(z['poses'],d.time+np.arange(1,329)*.01));minimum=float(values.min());other=c['self_margin_m']>=.002 and c['terminal_speed_m_s']<=.025 and c['terminal_angular_speed_rad_s']<=.025;passed=minimum>=.155 and other;candidates.append(dict(index=c['index'],old_reason=c['reason'],new_minimum_m=minimum,passed=passed,progress_m=c['goal_progress_m'],target=c['target']))
  rec=dict(step=x['step'],admitted=sum(c['passed']for c in candidates),positive_progress=sum(c['passed']and c['progress_m']>=.05 and np.mean(c['target'][2:])>=1 for c in candidates),candidates=candidates);records.append(rec)
 assert sum(x['positive_progress']for x in records)>0,'NO_PREREGISTERED_PROGRESS_TAIL_QUALIFIED'
 assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 with gzip.open(root/'CAUSAL_DOMAINS.json.gz','xt')as f:json.dump(by_step,f)
 result=dict(status='DECLARED_NORM_SPEED_CAUSAL_QUALIFICATION_PASS',maximum_physical_norm_speed_m_s=actual_bound,declared_public_norm_cap_m_s=.08,old_broader_axis_speed_cap_m_s=.12,old_broader_class_passed=False,all_raw_packets=len(packets),all329_coverage_samples=329*len(packets),maximum_actual_center_exclusion_m=max(coverage),independent_numpy_scipy_domains_exact=True,states=records,new_models=0,new_integrations=0,new_predictions=0,new_navigation=0,source_unchanged=True)
 (root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='states'}),flush=True)
finally:signal.alarm(0);(root/'ROUND_WINDOW.json').write_text(json.dumps(dict(started_unix=started,absolute_deadline_unix=started+300,round_closed=True,elapsed_s=time.time()-started,new_models=0,new_integrations=0),indent=2)+'\n')
