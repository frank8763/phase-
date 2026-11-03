"""Reconstruct closed two-cycle evidence, with initialization/integration blocked."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation'
sys.path.insert(0,str(source));sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'));sys.path.insert(2,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V777_MODEL_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from dynamic_scene import Motion
from exact_footprint import pose_values
from self_geometry import containment_margin
from recursive_domain import RecursiveDomain
from renewal_state import encode
from sensor_model import packet as sensed_packet
sys.path.insert(0,str(repo/'experiments/v772_map_conditioned_progress'))
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
sys.path.insert(0,str(repo/'runs/v771_audit_dependencies/site'));sys.path.insert(0,str(repo/'experiments/v773_map_conditioned_progress_audit'))
from independent_domain import IndependentDomain
repo=Path(__file__).resolve().parents[2];raw=repo/'runs/v776_retained_tail_reentry_qualification';root=repo/'runs/v777_retained_tail_reentry_audit';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def clone(d):
 c=RecursiveDomain(d.origin);c.time=d.time;c.possible=d.possible.copy();c.distance=d.distance.copy();c.last=dict(d.last);return c
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def sequence(target,last,count,brake):
 rows=[];command=np.asarray(last).copy()
 for tick in range(0,count,8):
  active=np.asarray(target).copy()
  if tick>=brake:active[2:]=0.
  command=np.clip(np.clip(active,limits[:,0],limits[:,1]),command-rate,command+rate);rows.extend([command.copy()for _ in range(min(8,count-tick))])
 return np.asarray(rows)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V777_600S_ABSOLUTE_STOP')));signal.alarm(600);dump('ROUND_WINDOW.json',window);status='RUNNING';records=[]
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(repo/'experiments/v776_retained_tail_reentry_qualification/INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 r=read(raw/'RESULT.json');assert r['status']=='SAVED_RETAINED_TAIL_REENTRY_QUALIFICATION_COMPLETE'and read(raw/'ROUND_WINDOW.json')['round_closed']
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};domain=RecursiveDomain(p['start_qpos'][:2])
 for pkt in old:
  assert packet_equal(pkt,sensed_packet(pkt['xy'],pkt['yaw'],pkt['time'],pkt['step'],p,motion,initial_calls));domain.update(pkt);assert encode(domain)==beliefs[pkt['step']]['free_space_renewal']
  if pkt['step']==32:base=clone(domain)
 assert len(old)==177

 source=repo/'runs/v772_map_conditioned_progress';replay=np.load(raw/'BASELINE_REPLAY.npz');prior=np.load(source/'ORIGINAL_256_NATIVE_REPLAY.npz')
 fields=['qpos','qvel','controls','mocap','safety']
 assert all(np.array_equal(replay[k],prior[k])for k in fields)
 all_safety=[];private=0
 def geometry(a,when):
  for j,(q,box)in enumerate(zip(a['qpos'],a['safety'][:,2:])):
   t=when+(j+1)*.01;field=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*p['known_circles'],[*motion.xy(t),config['radius_m']]])});minimum=float(pose_values(field,poses(q[None,:]))[0]);margin=float(containment_margin(box,bounds));assert abs(minimum-a['safety'][j,0])<=1e-8 and abs(margin-a['safety'][j,1])<=1e-10 and minimum>=.15 and margin>=0 and np.max(abs(a['mocap'][j,config['mocap_id']]-np.r_[motion.xy(t),0.]))<=1e-8;all_safety.append([minimum,margin])
 def prediction(record,q,v,last,domain):
  global private
  z=np.load(raw/(record['label']+'_PRIVATE.npz'));assert max(np.max(abs(z['initial_qpos']-q)),np.max(abs(z['initial_qvel']-v)),np.max(abs(z['initial_ctrl']-last)),abs(float(z['initial_time'])-domain.time))<=1e-10
  assert record['hold_first']is True and record['brake_after_native']==168 and z['qpos'].shape==(328,len(q))and z['qvel'].shape==(328,len(v))and np.max(abs(z['poses']-poses(z['qpos'])))<=1e-12
  commands=np.vstack([np.repeat([last],8,axis=0),sequence(record['target'],last,320,160)]);assert np.array_equal(z['controls'],commands)and np.all(commands>=limits[:,0]-1e-12)and np.all(commands<=limits[:,1]+1e-12)
  vals=np.minimum(pose_values(static,z['poses']),domain.body_lower(z['poses'],domain.time+np.arange(1,329)*.01));minimum=float(vals.min());margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));progress=float(np.linalg.norm(q[:2]-p['goal_xy'])-np.linalg.norm(z['qpos'][-1,:2]-p['goal_xy']));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
  assert reason==record['reason']and record['admissible']==(reason is None)and int(np.argmin(vals))+1==record['minimum_causal_tick'];assert max(abs(minimum-record['minimum_causal_clearance_m']),abs(margin-record['self_margin_m']),abs(speed-record['terminal_speed_m_s']),abs(angular-record['terminal_angular_speed_rad_s']),abs(progress-record['goal_progress_m']))<=1e-8;private+=328;return z

 geometry(replay,0.);native={'BASELINE':{k:replay[k]for k in fields}};counts=0;total_replay=256
 targets=read(raw/'TARGETS.json');expected=[dict(index=i,target=[0.,0.,float(v+d),float(v-d)],mean=v,difference=d)for i,(v,d)in enumerate((v,d)for v in[0,1,2]for d in[-6,-3,0,3,6])];assert targets==expected
 assert [(s['name'],s['local_public'])for s in r['states']]==[('TAIL_138',138),('TAIL_140',140),('TAIL_144',144)]
 for state in r['states']:
  name=state['name'];k=state['local_public'];a=np.load(raw/(name+'_REPLAY.npz'));old_a=np.load(source/'MAP_HISTORY_MAIN_ACTUAL.npz');assert len(a['qpos'])==k*8
  for key in fields:assert np.max(abs(a[key]-old_a[key][:k*8]))<=1e-8
  geometry(a,base.time);total_replay+=k*8;domain=IndependentDomain(base.origin,p,'MAP_HISTORY')
  for pk in old[:33]:domain.update(pk)
  with gzip.open(raw/(name+'_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
  with gzip.open(source/'MAP_HISTORY_MAIN_OBSERVATIONS.json.gz','rt')as f:old_obs=json.load(f)
  assert obs==old_obs[:k]and len(obs)==k
  for j,o in enumerate(obs):
   q=a['qpos'][8*j+7];xy,yaw=sensor_pose(q);pkt=o['packet'];assert pkt['step']==33+j and abs(pkt['time']-(33+j)*.08)<1e-9 and np.array_equal(xy,pkt['xy'])and yaw==pkt['yaw']and packet_equal(pkt,sensed_packet(xy,yaw,pkt['time'],pkt['step'],p,motion,initial_calls));domain.update(pkt);assert encode(domain)==o['domain'];ts=domain.time+np.linspace(0,3.28,329);excess=float(domain.point_lower(np.asarray([motion.xy(t)for t in ts]),ts).max());assert excess<=1e-7 and abs(excess-o['maximum_actual_coverage_excess_m'])<=1e-10;counts+=1
  assert encode(domain)==read(raw/(name+'_INITIAL_DOMAIN.json'));q=a['qpos'][-1];v=a['qvel'][-1];last=a['controls'][-1]
  cz=np.load(raw/(state['candidates'][0]['label']+'_PRIVATE.npz'));assert state['old_tail_remaining_native']==(161-k)*8>0
  for rec,t in zip(state['candidates'],targets):
   assert rec['target']==t['target']and rec['action_index']==t['index']and rec['initial_state_unmodified'];z=prediction(rec,q,v,last,domain)
   for key in ['initial_qpos','initial_qvel','initial_ctrl','initial_time','initial_act','initial_warmstart','initial_full_ctrl','initial_mocap_pos','initial_mocap_quat']:assert np.array_equal(z[key],cz[key])
   known=pose_values(static,z['poses']);unknown=domain.body_lower(z['poses'],domain.time+np.arange(1,329)*.01);assert abs(known.min()-rec['static_min_m'])<1e-10 and abs(unknown.min()-rec['unknown_min_m'])<1e-10
  assert len(state['candidates'])==15;eligible=[x for x in state['candidates']if x['admissible']];ranked=sorted(eligible,key=lambda x:(-x['goal_progress_m'],-x['minimum_causal_clearance_m'],x['action_index']));assert [x['action_index']for x in ranked]==state['ranking'] and (ranked[0]if ranked else None)==state['best'] and len(eligible)==state['admissible_count']and sum(x['goal_progress_m']>=.05 for x in eligible)==state['positive_progress_count'];assert state['new_actual_executed']is False
  native[name]={key:a[key]for key in fields};records.append({key:val for key,val in state.items()if key not in ['candidates','calibration']})
 # Global accounting step differs by design. All physical contact event fields remain identical.
 old_contacts={'BASELINE':[],'MAP_HISTORY_MAIN':[]}
 with gzip.open(source/'ACTUAL_CONTACTS.jsonl.gz','rt')as f:
  for line in f:
   x=json.loads(line);key=x['context']
   if key in old_contacts:old_contacts[key].append(x)
 count=0;bad=0;cursor={k:0 for k in native}
 with gzip.open(raw/'ACTUAL_CONTACTS.jsonl.gz','rt')as f:
  for line in f:
   x=json.loads(line);count+=1;key=x['context'];idx=cursor[key];cursor[key]+=1;assert x['account_step']==count;old_x=old_contacts['BASELINE'if key=='BASELINE'else'MAP_HISTORY_MAIN'][idx]
   for field in fields:assert np.max(abs(np.asarray(x[field])-native[key][field][idx]))<=1e-12
   assert x['time']==old_x['time']and x['public']==old_x['public']
   normalize=lambda c:{k:v for k,v in c.items()if k!='physics_step'}
   assert [normalize(c)for c in x['contacts']]==[normalize(c)for c in old_x['contacts']]
   bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in x['contacts'])
 assert count==total_replay==3632 and all(cursor[k]==len(v['qpos'])for k,v in native.items())and bad==0 and counts==422 and private==14760
 assert r['original_replay_native']==3632 and r['private_integrations']==14760 and r['actual_validation_native']==r['actual_new_packets']==0
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='RETAINED_TAIL_REENTRY_SAVED_EVIDENCE_VERIFIED';dump('RESULT.json',dict(status=status,states=records,old_replayed_native=3632,private_integrations=14760,old_packets_reconstructed=422,coverage_samples=422*329,bad_contacts=bad,minimum_actual_clearance_m=float(np.min(np.asarray(all_safety)[:,0])),new_initializations=0,new_integrations=0,new_navigation=0,new_confirmation=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
