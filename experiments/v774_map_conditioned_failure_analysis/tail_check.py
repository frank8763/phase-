import gzip,hashlib,json,signal,time,sys,os
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
for path in [repo/'runs/v771_audit_dependencies/site',repo/'experiments/v735_scan_differential_navigation',repo/'experiments/v773_map_conditioned_progress_audit']:sys.path.insert(0,str(path))
from independent_domain import IndependentDomain
from renewal_state import decode
from exact_footprint import pose_values
from types import SimpleNamespace
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(own/'TAIL_FREEZE.json');assert all(sha(repo/n)==h for n,h in f.items());assert(repo/'REVIEW_PENDING').exists();start=time.time();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V774_TAIL_600S_STOP')));signal.alarm(600);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
pair=repo/'runs/v735_scan_differential_navigation/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json');bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));raw=repo/'runs/v772_map_conditioned_progress';rows=[]
for profile in ['MAP_HISTORY','MAP_FUTURE']:
 b=read(raw/(profile+'_MAIN_SUMMARY.json'));k=b['scheduled_public_completed'];a=np.load(raw/(profile+'_MAIN_ACTUAL.npz'));domain=IndependentDomain(p['start_qpos'][:2],p,profile)
 with gzip.open(raw/(profile+'_MAIN_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
 for j in range(k,len(obs)):
  d=decode(obs[j]['domain']);domain.possible=d.possible.copy();domain.distance=d.distance.copy();domain.time=d.time;domain.last=d.last;domain.cache_time=None;domain.sets=None;domain.fields=None;q=a['qpos'][8*j+7];yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));poses=np.repeat([[q[0],q[1],yaw]],329,axis=0);ts=domain.time+np.linspace(0,3.28,329);known=float(pose_values(static,poses).min());unknown=float(domain.body_lower(poses,ts).min())
  if profile=='MAP_FUTURE':
   xy=np.asarray(cfg['anchor_xy'])+np.sin(ts*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy']);sets,_=domain.future();idx=np.rint((xy+6)/.01).astype(int);assert all(sets[z][tuple(ii)]for z,ii in zip(domain.buckets(ts),idx))and domain.future_point_lower(xy,ts).max()<=1e-7
  rows.append(dict(profile=profile,local_public=j+1,static_min_m=known,unknown_future_min_m=unknown,geometric_hold_reference_pass=min(known,unknown)>=.155,actual_linear_speed_m_s=float(np.linalg.norm(a['qvel'][8*j+7,:2])),actual_angular_speed_rad_s=float(np.linalg.norm(a['qvel'][8*j+7,3:6]))))
assert len(rows)==74;result=dict(status='SAVED_TAIL_GEOMETRIC_REFERENCE_CHECK_COMPLETE',geometric_only=True,not_a_physical_control_certificate=True,rows=rows,passing_local_public={profile:[x['local_public']for x in rows if x['profile']==profile and x['geometric_hold_reference_pass']]for profile in ['MAP_HISTORY','MAP_FUTURE']},new_initializations=0,new_integrations=0,new_robot_predictions=0,new_observations=0,elapsed_s=time.time()-start)
assert all(sha(repo/n)==h for n,h in f.items());(repo/'runs/v774_map_conditioned_failure_analysis/TAIL_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');signal.alarm(0);print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
