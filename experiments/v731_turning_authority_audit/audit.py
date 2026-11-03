"""Independent saved native/control/sensor audit, no simulator initialization."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v731_turning_authority_audit';root.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def reject(*args,**kwargs):raise RuntimeError('V731_FORBIDS_MODEL_INITIALIZATION_OR_INTEGRATION')
class Forbidden:
 from_binary_path=staticmethod(reject)
 from_xml_path=staticmethod(reject)
 from_xml_string=staticmethod(reject)
 def __init__(self,*a,**kw):reject()
mujoco.MjModel=Forbidden;mujoco.MjData=reject
for n in ['mj_step','mj_step1','mj_step2']:setattr(mujoco,n,reject)
source=repo/'experiments/v721_recursive_unseen_navigation';sys.path.insert(0,str(source))
from recursive_domain import RecursiveDomain
from renewal_state import encode
from exact_footprint import pose_values
assert (repo/'REVIEW_PENDING').exists()
with (repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});begun=time.time();window=dict(started_unix=begun,absolute_deadline_unix=begun+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
def dump(name,x):(root/name).write_text(json.dumps(x,indent=2)+'\n')
dump('ROUND_WINDOW.json',window)
def timeout(*args):raise TimeoutError('V731_SINGLE_300S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 run=repo/'runs/v730_native_turning_authority';r=read(run/'RESULT.json');assert read(run/'ROUND_WINDOW.json')['round_closed'];pair=repo/'runs/v721_recursive_unseen_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json')
 with gzip.open(pair/'geometry_memory/sensor_packets.jsonl.gz','rt')as f:initial=[json.loads(s)for s in f][:65]
 base=RecursiveDomain(p['start_qpos'][:2])
 for packet in initial:base.update(packet)
 static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));details=[];controls_checked=packets_checked=forecast_samples=0
 for row in r['candidates']:
  data=np.load(run/('CANDIDATE_%02d_PRIVATE.npz'%row['index']));assert data['qpos'].shape==(328,20)and data['qvel'].shape==(328,19)and data['controls'].shape==(328,4)
  assert np.all(np.isfinite(data['qpos']))and np.all(np.isfinite(data['qvel']))
  assert np.all(abs(np.diff(data['controls'],axis=0))<=np.array([.1,.1,.7,.7])+1e-12)
  controls_checked+=328
  if not row['admissible']:assert row['validation_steps']==0;continue
  actual=np.load(run/('CANDIDATE_%02d_ACTUAL.npz'%row['index']));error=max(float(np.max(abs(actual[k]-data[k])))for k in ['qpos','qvel','controls']);assert error<=1e-8
  with gzip.open(run/('CANDIDATE_%02d_OBSERVATIONS.json.gz'%row['index']),'rt')as f:observations=json.load(f)
  assert len(observations)==41
  domain=RecursiveDomain(base.origin);domain.time=base.time;domain.possible=base.possible.copy();domain.distance=base.distance.copy();domain.last=dict(base.last)
  for i,observation in enumerate(observations):
   packet=observation['packet'];assert packet['step']==65+i and abs(packet['time']-base.time-(i+1)*.08)<1e-10;domain.update(packet);assert encode(domain)==observation['domain'];q=actual['qpos'][(i+1)*8-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));assert packet['xy']==q[:2].tolist()and packet['yaw']==yaw
   times=domain.time+np.linspace(0,3.28,329);truth=np.asarray(config['anchor_xy'])+np.sin(times*config['omega_rad_s']+config['phase_rad'])[:,None]*config['amplitude_m']*np.asarray(config['axis_xy']);assert domain.point_lower(truth,times).max()<=1e-7;packets_checked+=1;forecast_samples+=329
  q=actual['qpos'];v=actual['qvel'];yaw=np.unwrap(np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2)));long=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);ideal=float(np.sum(long/.60*.5*(np.tan(q[:,7])+np.tan(q[:,9])))*.01);actual_yaw=float(yaw[-1]-yaw[0]);now=np.asarray(row['terminal_pose']);future=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);forward=hold.copy();forward[:,:2]+=np.minimum(future/1.6,1)[:,None]*.30*np.array([math.cos(now[2]),math.sin(now[2])]);hold_min=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,domain.time+future)).min());forward_min=float(np.minimum(pose_values(static,forward),domain.body_lower(forward,domain.time+future)).min());assert abs(hold_min-row['terminal_fresh_hold_3_28s_lower_m'])<=1e-12 and abs(forward_min-row['terminal_fresh_geometric_forward_0_30m_lower_m'])<=1e-12
  details.append(dict(index=row['index'],steer=row['steer'],wheel_mean=row['mean_rear_wheel'],rear_half_difference=row['rear_half_difference'],full_native_error=error,actual_yaw_change_rad=actual_yaw,actual_yaw_range_rad=float(yaw.max()-yaw.min()),no_slip_bicycle_yaw_integral_rad=ideal,actual_goal_progress_m=row['actual_goal_progress_m'],terminal_hold_lower_m=hold_min,terminal_forward_geometric_lower_m=forward_min,forward_geometric_passed=forward_min>=.155))
 assert r['original_replay_steps']==512 and r['private_prediction_integrations']==8+9*320==2888 and r['candidate_scene_validation_integrations']==len(details)*328
 assert controls_checked==9*328 and packets_checked==len(details)*41 and forecast_samples==packets_checked*329
 assert r['minimum_actual_native_clearance_m']>=.15 and r['bad_contacts']==0 and r['maximum_candidate_state_error']==r['maximum_original_replay_error']==0
 metadata=read(run/'WHEEL_CONTACT_MODEL_METADATA.json');wheel_metrics=[]
 for entry in details:
  index=entry['index']
  with gzip.open(run/('CANDIDATE_%02d_WHEEL_DIAGNOSTICS.json.gz'%index),'rt')as stream:samples=json.load(stream)
  assert len(samples)==41 and all(s['executed_state_unchanged'] and s['diagnostic_forward_integrations']==0 for s in samples)
  for k,sample in enumerate(samples):
   assert sample['public_step']==65+k and abs(sample['time']-base.time-(k+1)*.08)<1e-10 and [w['name']for w in sample['wheels']]==[w['name']for w in metadata['wheels']]
   for wheel in sample['wheels']:
    assert abs(wheel['rolling_mismatch_m_s']-(wheel['center_longitudinal_velocity_m_s']-wheel['rolling_speed_reference_m_s']))<=1e-12
    for contact in wheel['ground_contacts']:
     assert contact['dimension']in [1,3,4,6] and contact['normal_force_abs_n']>=0 and contact['tangential_force_norm_n']>=0 and np.isfinite(contact['contact_force_torque']).all() and np.isfinite(contact['point_velocity_world_m_s']).all()
  aggregates=[]
  for name in [w['name']for w in metadata['wheels']]:
   wheels=[next(w for w in s['wheels']if w['name']==name)for s in samples];contacts=[c for w in wheels for c in w['ground_contacts']]
   aggregates.append(dict(name=name,mean_abs_rolling_mismatch_m_s=float(np.mean([abs(w['rolling_mismatch_m_s'])for w in wheels])),mean_abs_center_lateral_velocity_m_s=float(np.mean([abs(w['center_lateral_velocity_m_s'])for w in wheels])),sampled_ground_contacts=len(contacts),mean_normal_force_n=float(np.mean([c['normal_force_abs_n']for c in contacts]))if contacts else 0.,mean_abs_longitudinal_contact_slip_m_s=float(np.mean([abs(c['contact_longitudinal_slip_m_s'])for c in contacts]))if contacts else None,mean_abs_lateral_contact_slip_m_s=float(np.mean([abs(c['contact_lateral_slip_m_s'])for c in contacts]))if contacts else None,mean_abs_torsional_torque_nm=float(np.mean([c['torsional_torque_abs_nm']for c in contacts]))if contacts else 0.,mean_rolling_torque_norm_nm=float(np.mean([c['rolling_torque_norm_nm']for c in contacts]))if contacts else 0.))
  wheel_metrics.append(dict(index=index,public_samples=41,wheels=aggregates))
 for index,anchor_index in [(0,5),(1,1),(2,9)]:
  old=np.load(repo/'runs/v728_early_observation_maneuver'/('CANDIDATE_%02d_ACTUAL.npz'%anchor_index));new=np.load(run/('CANDIDATE_%02d_ACTUAL.npz'%index));assert max(float(np.max(abs(old[k]-new[k])))for k in ['qpos','qvel','controls'])<=1e-8
 dump('WHEEL_CONTACT_METRICS.json',dict(metadata=metadata,branches=wheel_metrics,all_sample_checks_passed=True,new_integrations=0,scope='Every8 native tick samples from independent mj_forward copy; does not attribute causal friction coefficients or certify unsampled force history.'))

 out=dict(status='ALL_NINE_FACTORIAL_NATIVE_SENSOR_CONTACT_EVIDENCE_VERIFIED',details=details,candidate_count=9,admissible_native_branches=len(details),forward_geometric_witness_passes=sum(x['forward_geometric_passed']for x in details),all_controls_checked=controls_checked,actual_new_packets_reconstructed=packets_checked,actual_future_coverage_samples=forecast_samples,original_replay_native=512,private_native=2888,scene_validation_native=r['candidate_scene_validation_integrations'],new_initializations=0,new_integrations=0,new_navigation_samples=0,training_updates=0,scope='Saved-evidence verification, finite old-state counterfactual branches; not another independent physical run or full navigation acceptance.')
 dump('RESULT.json',out)
 labels=['%+.0f deg\nd=%+.0f'%(math.degrees(x['steer']),x['rear_half_difference'])for x in details];xx=np.arange(len(details));fig,axes=plt.subplots(1,2,figsize=(12,4.5),constrained_layout=True)
 axes[0].bar(xx-.18,[math.degrees(x['actual_yaw_change_rad'])for x in details],.36,label='Actual native yaw');axes[0].bar(xx+.18,[math.degrees(x['no_slip_bicycle_yaw_integral_rad'])for x in details],.36,label='No-slip reference from measured steering');axes[0].set_xticks(xx,labels,rotation=15);axes[0].set_ylabel('Yaw change (degrees)');axes[0].set_title('Same safe old-state maneuver branches');axes[0].legend(fontsize=8)
 axes[1].bar(xx-.18,[x['terminal_hold_lower_m']for x in details],.36,label='Fresh 3.28s stopped certificate');axes[1].bar(xx+.18,[x['terminal_forward_geometric_lower_m']for x in details],.36,label='Fresh 0.30m geometric witness');axes[1].axhline(.155,color='crimson',ls='--',label='Required predicted clearance');axes[1].set_xticks(xx,labels,rotation=15);axes[1].set_ylabel('Conservative clearance lower bound (m)');axes[1].set_title('Actual observations still do not renew feasibility');axes[1].legend(fontsize=8)
 fig.savefig(root/'turning_factorial_diagnosis.png',dpi=200);plt.close(fig)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());window['status']=out['status']
finally:window.update(round_closed=True,elapsed_s=time.time()-begun);dump('ROUND_WINDOW.json',window);signal.alarm(0)
print(json.dumps({k:v for k,v in out.items()if k!='details'}))
