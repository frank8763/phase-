"""Independently audit retained partial states and exact sensor schemas; no physics."""
import ast,copy,fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent
sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(2,str(repo/'experiments/v733_early_low_translation_scan'));sys.path.insert(3,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V751_INITIALIZATION_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from packet_contract import packet_equal,raw_packet,derived_rays,FIELDS
from sensor_model import packet as sensed_packet
from dynamic_scene import Motion
from recursive_domain import RecursiveDomain
from renewal_state import encode,decode
from exact_footprint import pose_values
from self_geometry import containment_margin
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v751_coupled_packet_schema_diagnosis';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+300,limit_s=300,round_closed=False);dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V751_300S_ABSOLUTE_STOP')));signal.alarm(300);status='RUNNING'
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];bounds=np.asarray(p['footprint_bounds']);c=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=c['ids']
 static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};domain=RecursiveDomain(p['start_qpos'][:2]);raw_matches=derived=0
 for pkt in old:
  regen=sensed_packet(pkt['xy'],pkt['yaw'],pkt['time'],pkt['step'],p,motion,calls);assert packet_equal(pkt,regen);raw_matches+=1;derived+=int('rays'in pkt);domain.update(pkt);assert encode(domain)==beliefs[pkt['step']]['free_space_renewal']
 # Cross-check the new derived helper against the frozen original audit's AST function.
 tree=ast.parse((repo/'experiments/v735_scan_differential_navigation/audit_field_discovery.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='rays');scope={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen original rays>','exec'),scope)
 for pkt in old:assert np.array_equal(scope['rays'](pkt),derived_rays(pkt))
 raw=repo/'runs/v749_coupled_observation_progress';completion=read(raw/'COMPLETION.json');assert completion['status']=='STOPPED_EXCEPTION'and completion['original_replay_native']==264 and completion['private_integrations']==328 and completion['actual_validation_native']==0
 with gzip.open(raw/'ACTUAL_CONTACTS.jsonl.gz','rt')as f:native=[json.loads(s)for s in f]
 assert len(native)==264;legacy=np.load(repo/'runs/v746_early_observation_handover/ORIGINAL_944_NATIVE_REPLAY.npz');pred=np.load(raw/'CALIBRATION_PRIVATE.npz')
 with gzip.open(cell/'observation_scan_certificate.json.gz','rt')as f:original_scan=json.load(f)
 pred_error=max(float(np.max(abs(pred[k]-original_scan[k])))for k in ['qpos','qvel','poses','controls']);assert pred_error<=1e-8
 maximum=0.;bad=0;minimum=float('inf');self_min=float('inf')
 for i,row in enumerate(native):
  assert row['account_step']==i+1 and row['context']=='BASELINE';q=np.asarray(row['qpos']);v=np.asarray(row['qvel']);ctrl=np.asarray(row['controls']);mc=np.asarray(row['mocap']);box=np.asarray(row['safety'][2:]);when=row['time'];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
  if i<256:err=max(np.max(abs(q-legacy['qpos'][i])),np.max(abs(v-legacy['qvel'][i])),np.max(abs(ctrl-legacy['controls'][i,ids])),np.max(abs(mc-legacy['mocap'][i])))
  else:err=max(np.max(abs(q-pred['qpos'][i-256])),np.max(abs(v-pred['qvel'][i-256])),np.max(abs(ctrl-pred['controls'][i-256])))
  maximum=max(maximum,float(err));assert maximum<=1e-8
  field=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*p['known_circles'],[*motion.xy(when),config['radius_m']]])});value=float(pose_values(field,[np.r_[q[:2],yaw]])[0]);margin=float(containment_margin(box,bounds));assert abs(value-row['safety'][0])<=1e-8 and abs(margin-row['safety'][1])<=1e-10 and value>=.15 and margin>=0 and np.max(abs(mc[config['mocap_id']]-np.r_[motion.xy(when),0.]))<=1e-8;minimum=min(minimum,value);self_min=min(self_min,margin);bad+=sum(x['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for x in row['contacts'])
 assert bad==0
 q=np.asarray(native[-1]['qpos']);yaw=float(np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2)));regen=sensed_packet(q[:2].astype(np.float32),yaw,native[-1]['time'],33,p,motion,calls);stored=old[33];fields={k:regen[k]==stored[k]for k in FIELDS};assert all(fields.values());assert set(stored)-set(regen)=={'rays'}and packet_equal(stored,regen)and stored!=regen
 start=decode(beliefs[32]['free_space_renewal']);domain=RecursiveDomain(start.origin);domain.time=start.time;domain.possible=start.possible.copy();domain.distance=start.distance.copy();domain.last=dict(start.last);domain.update(regen);assert encode(domain)==beliefs[33]['free_space_renewal']
 negative=0;checks=[]
 for pkt in old:
  base=raw_packet(pkt)
  for field in ['time','yaw','lidar_max_range','depth_max_range','xy','lidar','depth']:
   changed=copy.deepcopy(base)
   if type(changed[field])is list:changed[field][0]=float(np.nextafter(changed[field][0],np.inf))
   else:changed[field]=float(np.nextafter(changed[field],np.inf))
   assert not packet_equal(base,changed);negative+=1
  for field in FIELDS:
   changed=copy.deepcopy(base);del changed[field];assert not packet_equal(base,changed);negative+=1
  changed=copy.deepcopy(base);changed['unknown_field']=0;assert not packet_equal(base,changed);negative+=1
  if pkt['rays']:
   changed=copy.deepcopy(pkt);changed['rays'][0][0]=float(np.nextafter(changed['rays'][0][0],np.inf));assert not packet_equal(base,changed);negative+=1
  for value in [True,'0',float('nan'),float('inf')]:
   changed=copy.deepcopy(base);changed['lidar'][0]=value;assert not packet_equal(base,changed);negative+=1
  changed=copy.deepcopy(base);changed['rays']=[[0.]*6];assert not packet_equal(base,changed);negative+=1
  changed=copy.deepcopy(base);changed['step']+=1;assert not packet_equal(base,changed);negative+=1
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='PARTIAL_NATIVE_AND_EXACT_PACKET_SCHEMA_DIAGNOSIS_COMPLETE';dump('RECONSTRUCTED_PACKET33.json',regen);dump('RESULT.json',dict(status=status,original_v749_status_preserved=completion['status'],root_cause='Whole-dictionary comparison mixed8 raw fields with old derived rays field',original_raw_fields_all_exact=fields,only_extra_legacy_field='rays',saved_old_packets=raw_matches,derived_ray_packets_verified=derived,all_original_domains_exact=True,reconstructed_packet33_domain_exact=True,reconstructed_packet33_is_original_payload_readback=False,negative_cases_rejected=negative,old_native_replay_verified=264,old_private_scan_predictions_verified=328,maximum_old_native_state_control_error=maximum,maximum_private_scan_error=pred_error,minimum_actual_native_clearance_m=minimum,minimum_actual_self_margin_m=self_min,bad_contacts=bad,three_profiles_all_unexecuted=True,new_initializations=0,new_integrations=0,new_predictions=0,new_navigation=0,no_restarted_v749=True,source_of_reconstructed_packet='Saved264th native state + frozen deterministic sensor backend and bootstrap noise counters'))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
