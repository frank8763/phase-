"""Reconstruct all fixed scan and successor evidence with zero model loads."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v734_scan_saved_evidence';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def reject(*a,**kw):raise RuntimeError('V734_FORBIDS_MODEL_INITIALIZATION_OR_INTEGRATION')
class Forbidden:
 from_binary_path=staticmethod(reject)
 from_xml_path=staticmethod(reject)
 from_xml_string=staticmethod(reject)
 def __init__(self,*a,**kw):reject()
mujoco.MjModel=Forbidden;mujoco.MjData=reject
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,reject)
sys.path.insert(0,str(repo/'experiments/v721_recursive_unseen_navigation'));from recursive_domain import RecursiveDomain;from renewal_state import encode;from exact_footprint import pose_values
assert (repo/'REVIEW_PENDING').exists()
with (repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2)+'\n')
dump('ROUND_WINDOW.json',window)
def stop(*_):raise TimeoutError('V734_SINGLE_300S_STOP')
signal.signal(signal.SIGALRM,stop);signal.alarm(300)
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());run=repo/'runs/v733_early_low_translation_scan';r=read(run/'RESULT.json');assert read(run/'ROUND_WINDOW.json')['round_closed'];pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');contract=read(pair/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json');limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate'])
 with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as stream:old=[json.loads(s)for s in stream][:33]
 base=RecursiveDomain(p['start_qpos'][:2])
 for packet in old:base.update(packet)
 static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));details=[];packet_count=0;successor_predictions=0;successor_actual=0
 def poses(q):return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
 def sequence(target,last,count,brake):
  command=last.copy();rows=[]
  for tick in range(0,count,8):
   active=np.asarray(target).copy()
   if tick>=brake:active[2:]=0.
   command=np.clip(np.clip(active,limits[:,0],limits[:,1]),command-rate,command+rate);rows.extend([command.copy()for _ in range(8)])
  return np.asarray(rows)
 def clone(domain):
  new=RecursiveDomain(domain.origin);new.possible=domain.possible.copy();new.distance=domain.distance.copy();new.time=domain.time;new.last=dict(domain.last);return new
 def observations(filename,domain,actual,start_step):
  global packet_count
  with gzip.open(filename,'rt')as stream:rows=json.load(stream)
  assert len(rows)==41
  for i,row in enumerate(rows):
   packet=row['packet'];assert packet['step']==start_step+i+1;domain.update(packet);assert encode(domain)==row['domain'];q=actual['qpos'][(i+1)*8-1];pp=poses(np.asarray([q]))[0];assert np.max(abs(packet['xy']-q[:2]))<=1e-12 and abs(packet['yaw']-pp[2])<=1e-12
   times=domain.time+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);assert domain.point_lower(truth,times).max()<=1e-7;packet_count+=1
  return domain
 assert [x['pivot_half_difference']for x in r['candidates']]==[0.,4.,-4.,8.,-8.,12.,-12.]
 for row in r['candidates']:
  i=row['index'];private=np.load(run/('CANDIDATE_%02d_PRIVATE.npz'%i));q=private['qpos'];v=private['qvel'];ctrl=private['controls'];assert q.shape==(328,20)and v.shape==(328,19)and ctrl.shape==(328,4);assert np.max(abs(poses(q)-private['poses']))<=1e-12
  expected=np.vstack([ctrl[:8],sequence(np.asarray(row['target_command']),ctrl[0],320,160)]);assert np.max(abs(ctrl-expected))<=1e-12 and np.all(ctrl>=limits[:,0]-1e-12)and np.all(ctrl<=limits[:,1]+1e-12)
  values=np.minimum(pose_values(static,private['poses']),base.body_lower(private['poses'],base.time+np.arange(1,329)*.01));minimum=float(values.min());assert abs(minimum-row['minimum_causal_clearance_m'])<=1e-12
  if not row['admissible']:continue
  actual=np.load(run/('CANDIDATE_%02d_ACTUAL.npz'%i));assert max(float(np.max(abs(actual[k]-private[k])))for k in ['qpos','qvel','controls'])<=1e-8;assert np.linalg.norm(v[-1,:2])<=.025 and np.linalg.norm(v[-1,3:6])<=.025 and minimum>=.155
  domain=observations(run/('CANDIDATE_%02d_OBSERVATIONS.json.gz'%i),clone(base),actual,32);now=poses(actual['qpos'])[-1];future=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);forward=hold.copy();forward[:,:2]+=np.minimum(future/1.6,1)[:,None]*.30*np.array([np.cos(now[2]),np.sin(now[2])]);actual_forward=float(np.minimum(pose_values(static,forward),domain.body_lower(forward,domain.time+future)).min());without=float(np.minimum(pose_values(static,forward),base.body_lower(forward,domain.time+future)).min());assert abs(actual_forward-row['terminal_fresh_geometric_forward_0_30m_lower_m'])<=1e-12 and abs(without-row['without_new_observation_forward_m'])<=1e-12
  suffix=row['successor'];assert len(suffix['candidates'])==5;eligible=[]
  for candidate in suffix['candidates']:
   j=candidate['index'];z=np.load(run/('SCAN_%02d_SUCCESSOR_%02d_PRIVATE.npz'%(i,j)));successor_predictions+=328;assert z['qpos'].shape==(328,20)and z['qvel'].shape==(328,19);assert np.max(abs(poses(z['qpos'])-z['poses']))<=1e-12
   expected=sequence(candidate['target'],actual['controls'][-1],328,248);assert np.max(abs(z['controls']-expected))<=1e-12;values=np.minimum(pose_values(static,z['poses']),domain.body_lower(z['poses'],domain.time+np.arange(1,329)*.01));minimum=float(values.min());progress=float(np.linalg.norm(now[:2]-p['goal_xy'])-np.linalg.norm(z['qpos'][-1,:2]-p['goal_xy']));assert abs(minimum-candidate['minimum_causal_clearance_m'])<=1e-12 and abs(progress-candidate['goal_progress_m'])<=1e-12
   good=minimum>=.155 and candidate['self_margin_m']>=.002 and np.linalg.norm(z['qvel'][-1,:2])<=.025 and np.linalg.norm(z['qvel'][-1,3:6])<=.025 and progress>=.02;assert bool(good)==candidate['admissible']
   if good:eligible.append(candidate)
  if eligible:
   selected=max(eligible,key=lambda c:(c['goal_progress_m'],c['minimum_causal_clearance_m'],-c['index']));assert selected['index']==suffix['selected_index'];pred=np.load(run/('SCAN_%02d_SUCCESSOR_%02d_PRIVATE.npz'%(i,selected['index'])));suffix_actual=np.load(run/('SCAN_%02d_SELECTED_SUCCESSOR_ACTUAL.npz'%i));assert max(float(np.max(abs(pred[k]-suffix_actual[k])))for k in ['qpos','qvel','controls'])<=1e-8;observations(run/('SCAN_%02d_SUCCESSOR_OBSERVATIONS.json.gz'%i),clone(domain),suffix_actual,73);successor_actual+=328;assert suffix['actual_goal_progress_m']>=.02
  else:assert suffix['selected_index']is None and suffix['actual_validation_steps']==0
  qualified=row['actual_yaw_range_rad']>math.radians(11.25)and row['actual_translation_m']<=.25 and suffix['actual_validation_steps']==328
  details.append(dict(index=i,amplitude=row['pivot_half_difference'],qualified=bool(qualified),actual_scan_range_deg=math.degrees(row['actual_yaw_range_rad']),actual_translation_m=row['actual_translation_m'],fresh_geometric_forward_m=actual_forward,without_new_observation_forward_m=without,concrete_successor_count=len(eligible),selected_successor_index=suffix['selected_index'],successor_actual_goal_progress_m=suffix.get('actual_goal_progress_m'),minimum_selected_successor_causal_m=None if not eligible else selected['minimum_causal_clearance_m']))
 assert len(details)==7 and r['original_replay_steps']==256 and r['scan_prediction_integrations']==2248 and r['successor_prediction_integrations']==successor_predictions==11480 and r['private_prediction_integrations']==13728 and r['scan_scene_validation_integrations']==2296 and r['successor_scene_validation_integrations']==successor_actual==1640 and r['candidate_scene_validation_integrations']==3936
 assert r['minimum_actual_native_clearance_m']>=.15 and r['bad_contacts']==0 and r['maximum_original_replay_error']==r['maximum_candidate_state_error']==0
 qualified=[x for x in details if x['qualified']];selected=min(qualified,key=lambda x:(abs(x['amplitude']),-x['minimum_selected_successor_causal_m'],x['index']))if qualified else None
 out=dict(status='EARLY_SCAN_AND_CONCRETE_NATIVE_SUCCESSOR_QUALIFIED'if qualified else'EARLY_SCAN_NOT_QUALIFIED',details=details,qualified_count=len(qualified),selected_for_one_future_development_candidate=selected,actual_new_packets_reconstructed=packet_count,actual_forecast_coverage_samples=packet_count*329,original_replay_native=256,private_integrations=13728,scene_validation_integrations=3936,new_initializations=0,new_integrations=0,new_navigation_samples=0,training_updates=0,scope='One old-task component qualification only, not complete navigation or fresh confirmation.')
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());dump('RESULT.json',out);window['status']=out['status']
finally:window.update(round_closed=True,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',window);signal.alarm(0)
print(json.dumps({k:v for k,v in out.items()if k!='details'}))
