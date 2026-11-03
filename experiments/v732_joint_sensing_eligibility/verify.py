"""One fixed joint eligibility test on already-observed native branches."""
import gzip,hashlib,json,os,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v732_joint_sensing_eligibility';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def no(*a,**kw):raise RuntimeError('V732_FORBIDS_MODEL_INITIALIZATION_OR_INTEGRATION')
class Forbidden:
 from_binary_path=staticmethod(no)
 from_xml_path=staticmethod(no)
 from_xml_string=staticmethod(no)
 def __init__(self,*a,**kw):no()
mujoco.MjModel=Forbidden;mujoco.MjData=no
for name in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,name,no)
sys.path.insert(0,str(repo/'experiments/v727_finite_dropout_reachability'));sys.path.insert(1,str(repo/'experiments/v721_recursive_unseen_navigation'))
from confidence_domain import ConfidenceDomain,ERROR_UPPER
from exact_footprint import pose_values
assert (repo/'REVIEW_PENDING').exists();assert read(repo/'runs/v731_turning_authority_audit/RESULT.json')['status']=='ALL_NINE_FACTORIAL_NATIVE_SENSOR_CONTACT_EVIDENCE_VERIFIED'
freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2)+'\n')
dump('ROUND_WINDOW.json',window)
def stop(*_):raise TimeoutError('V732_FIXED_300S_STOP')
signal.signal(signal.SIGALRM,stop);signal.alarm(300)
try:
 pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');base=ConfidenceDomain(p['start_qpos'][:2])
 with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as stream:old=[json.loads(s)for s in stream][:65]
 for packet in old:base.update(packet)
 static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));rows=[];total=0
 run=repo/'runs/v730_native_turning_authority';candidates=read(run/'CANDIDATES.json')
 for row in candidates:
  if not row['admissible']:continue
  domain=ConfidenceDomain(base.origin);domain.cost=base.cost.copy();domain.possible=base.possible.copy();domain.distance=base.distance.copy();domain.time=base.time;domain.updates=base.updates;domain.last=dict(base.last)
  with gzip.open(run/('CANDIDATE_%02d_OBSERVATIONS.json.gz'%row['index']),'rt')as stream:observations=json.load(stream)
  coverage=[]
  for observation in observations:
   packet=observation['packet'];domain.update(packet);times=domain.time+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);excess=float(domain.point_lower(truth,times).max());assert excess<=1e-7;coverage.append(excess);total+=1
  pose=np.asarray(row['terminal_pose']);future=np.linspace(0,3.28,329);hold=np.repeat([pose],329,axis=0);forward=hold.copy();forward[:,:2]+=np.minimum(future/1.6,1)[:,None]*.30*np.array([np.cos(pose[2]),np.sin(pose[2])]);hv=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,domain.time+future)).min());fv=float(np.minimum(pose_values(static,forward),domain.body_lower(forward,domain.time+future)).min());rows.append(dict(index=row['index'],steer=row['steer'],rear_half_difference=row['rear_half_difference'],old_deterministic_hold_m=row['terminal_fresh_hold_3_28s_lower_m'],confidence_hold_m=hv,old_deterministic_forward_m=row['terminal_fresh_geometric_forward_0_30m_lower_m'],confidence_forward_m=fv,geometric_forward_pass=fv>=.155,actual_coverage_excess_m=max(coverage),final_cost_sha256=domain.last['counter_sha256']))
  dump('BRANCHES.json',rows)
 out=dict(status='JOINT_SENSING_QUALIFIED_FOR_FUTURE_VALIDATION'if any(x['geometric_forward_pass']for x in rows)else'JOINT_SENSING_NOT_QUALIFIED',branches=rows,fixed_executed_branches=len(rows),new_observation_packets_checked=total,actual_coverage_samples=total*329,geometric_forward_witness_passes=sum(x['geometric_forward_pass']for x in rows),conditional_task_error_upper=ERROR_UPPER,new_initializations=0,new_integrations=0,new_navigation_samples=0,training_updates=0,scope='Conditional risk model remains uncalibrated for real sensors; saved-data qualification only, old V727 NOT_QUALIFIED not changed.')
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());dump('RESULT.json',out);window['status']=out['status']
finally:window.update(round_closed=True,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',window);signal.alarm(0)
print(json.dumps({k:v for k,v in out.items()if k!='branches'}))
