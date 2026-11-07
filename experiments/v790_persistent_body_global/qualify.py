"""Zero-model full closed-input calibration of online/independent historical state."""
import base64,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback,zlib
from pathlib import Path
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;sys.path.insert(0,str(repo/'runs/v771_audit_dependencies/site'))
import mujoco
def forbidden(*a,**k):raise RuntimeError('V790_QUALIFICATION_MODELS_AND_INTEGRATIONS_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_forward','mj_step','mj_step1','mj_step2']:setattr(mujoco,n,forbidden)
from risk_domain import RiskDomain
from independent_domain import IndependentDomain
from recursive_domain import HALF_DIAGONAL,SLACK,SPEED,AXIS,LOWER,GRID
from renewal_state import encode,decode
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v790_persistent_body_global/pre_navigation';root.mkdir(parents=True,exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
started=time.time();deadline=min(started+600,1793750400.);status='RUNNING';signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V790_QUALIFICATION_HARD_STOP')));signal.alarm(max(1,math.floor(deadline-started)))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
try:
 assert(repo/'REVIEW_PENDING').exists();lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());assert read(repo/'runs/v788_global_information_diagnosis/RESULT.json')['status']=='PERSISTENT_NORM_CERTIFICATE_QUALIFIED'
 pair=repo/'runs/v787_declared_speed_global/main01/paired';p=read(pair/'STATIC_PROTOCOL.json');cfg=read(pair/'DYNAMIC_PROTOCOL.json');cell=pair/'geometry_memory'
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:packets=[json.loads(s)for s in f]
 states=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()];assert len(states)==len(packets)==271
 online=RiskDomain(p['start_qpos'][:2],p,'MAP_HISTORY');audit=IndependentDomain(p['start_qpos'][:2],p,'MAP_HISTORY');sample=np.random.default_rng(789).integers(0,len(AXIS),size=(512,2));history=[];maxerr=0.;cover=-float('inf');bytes_max=0;mask_matches=0;records=[]
 for packet,old in zip(packets,states):
  online.update(packet);audit.update(packet);a=encode(online);b=encode(audit);assert a==b,'INDEPENDENT_SERIALIZED_HISTORY_MISMATCH'
  assert a['possible_bits_sha256']==old['free_space_renewal']['possible_bits_sha256'],'ORIGINAL_CURRENT_OUTER_SET_CHANGED';mask_matches+=1
  restored=decode(a);assert np.array_equal(restored.history_height,online.history_height)and np.array_equal(restored.possible,online.possible)
  fresh=np.maximum(0.,audit.distance[sample[:,0],sample[:,1]]-HALF_DIAGONAL-SLACK);history.append((audit.time,fresh));direct=np.maximum(0.,np.max([v-SPEED*(audit.time-t)for t,v in history],axis=0));encoded=np.maximum(0.,online.history_height[sample[:,0],sample[:,1]].astype(float)/1e6-SPEED*online.time);err=direct-encoded;assert err.min()>=-1e-12 and err.max()<1.000001e-6;maxerr=max(maxerr,float(err.max()));bytes_max=max(bytes_max,len(json.dumps(a)))
  times=online.time+np.arange(329)*.01;true=np.asarray(cfg['anchor_xy'])+np.sin(times*cfg['omega_rad_s']+cfg['phase_rad'])[:,None]*cfg['amplitude_m']*np.asarray(cfg['axis_xy']);value=restored.point_lower(true,times);assert value.max()<=1e-7;cover=max(cover,float(value.max()))
  if packet['step']in[116,196,228,268]:
   from types import SimpleNamespace
   from exact_footprint import pose_values
   bounds=np.asarray(p['footprint_bounds']);field=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']),circles=np.asarray(p['known_circles']),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
   prior=[x for x in read(repo/'runs/v788_global_information_diagnosis/RECORDS.json')if x['step']==packet['step']]
   candidates=read(cell/'retained_reentry'/f"step{packet['step']:04d}.json")['records'];assert len(candidates)==15
   for c,original in zip(candidates,prior):
    z=np.load(cell/'retained_reentry'/(c['label']+'.npz'));times=online.time+np.arange(1,329)*.01;known=pose_values(field,z['poses']);v1=np.minimum(known,online.body_lower(z['poses'],times));v2=np.minimum(known,audit.body_lower(z['poses'],times));assert np.max(abs(v1-v2))<=1e-10 and np.max(abs(v1-np.minimum(known,restored.body_lower(z['poses'],times))))<=1e-12
    # Quantization may decrease historical max by at most one micrometre.
    assert float(v1.min())>=original['persistent_minimum_m']-1.000001e-6
    records.append(dict(label=c['label'],minimum_m=float(v1.min()),useful_flip=bool(original['newly_admitted']and original['positive_progress']and v1.min()>=.155)))
 negatives=0
 for key,value in [('schema','OLD_SCHEMA'),('history_schema','OLD_SCHEMA'),('history_height_sha256','0'*64),('shape',[1,1])]:
  x=dict(a);x[key]=value
  try:decode(x)
  except (AssertionError,ValueError):negatives+=1
 for offset in [.0001,.08,3.28]:
  try:restored.point_lower([[0.,0.]],[restored.time-offset])
  except AssertionError:negatives+=1
 assert negatives==7 and restored.point_lower([[100.,100.]],[restored.time])[0]==0.;assert len(records)==60 and any(x['useful_flip']for x in records)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='PERSISTENT_GLOBAL_ZERO_MODEL_CALIBRATION_PASS';dump('RESULT.json',dict(status=status,packets=len(packets),old_current_masks_matched=mask_matches,exact_online_independent_serialized_states=len(packets),forecast_coverage_samples=len(packets)*329,maximum_actual_coverage_excess_m=cover,maximum_downward_quantization_m=maxerr,maximum_serialized_state_bytes=bytes_max,negative_cases_rejected=negatives,saved_predictions=records,new_models=0,new_integrations=0,new_predictions=0))
except BaseException as e:status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);dump('ROUND_WINDOW.json',dict(status=status,started_unix=started,absolute_deadline_unix=deadline,round_closed=True,elapsed_s=time.time()-started))
print(status)
