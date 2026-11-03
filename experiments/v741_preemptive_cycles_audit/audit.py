"""Reconstruct closed two-cycle evidence, with initialization/integration blocked."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation'
sys.path.insert(0,str(source));sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'));sys.path.insert(2,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V741_MODEL_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from dynamic_scene import Motion
from exact_footprint import pose_values
from self_geometry import containment_margin
from recursive_domain import RecursiveDomain
from renewal_state import encode
from sensor_model import packet as sensed_packet
repo=Path(__file__).resolve().parents[2];raw=repo/'runs/v740_preemptive_observation_cycles';root=repo/'runs/v741_preemptive_cycles_audit';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+300,limit_s=300,round_closed=False,new_initializations=0,new_integrations=0)
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
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V741_300S_ABSOLUTE_STOP')));signal.alarm(300);dump('ROUND_WINDOW.json',window);status='RUNNING';records=[]
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(repo/'experiments/v740_preemptive_observation_cycles/INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());r=read(raw/'RESULT.json');assert r['status']=='FIXED_PREEMPTIVE_OBSERVATION_CYCLES_COMPLETE'and read(raw/'ROUND_WINDOW.json')['round_closed']
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};base=RecursiveDomain(p['start_qpos'][:2]);bases={}
 for packet in old:
  regen=sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],p,motion,initial_calls);assert all(np.array_equal(packet[k],regen[k])for k in['lidar','depth']);base.update(packet);assert encode(base)==beliefs[packet['step']]['free_space_renewal']
  if packet['step']in[73,90,130]:bases[packet['step']]=clone(base)
 assert len(old)==177 and read(raw/'SENSOR_CALIBRATION.json')['packets']==177
 rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];replay=np.load(raw/'ORIGINAL_1040_NATIVE_REPLAY.npz');assert len(replay['qpos'])==1040
 for i,row in enumerate(rows[:130]):
  t=8*i+7;assert max(np.max(abs(replay['qpos'][t]-row['qpos_full'])),np.max(abs(replay['qvel'][t]-row['qvel_full'])),np.max(abs(replay['mocap'][t]-row['mocap_pos'])))<=1e-8 and np.array_equal(replay['controls'][8*i:8*i+8],np.repeat([row['ctrl']],8,axis=0))
 private=actual=packets=0;all_safety=[]
 def actual_geometry(data,when):
  out=[]
  for i,(q,box)in enumerate(zip(data['qpos'],data['safety'][:,2:])):
   t=when+(i+1)*.01;field=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*p['known_circles'],[*motion.xy(t),config['radius_m']]])});value=float(pose_values(field,poses(q[None,:]))[0]);margin=float(containment_margin(box,bounds));assert abs(value-data['safety'][i,0])<=1e-8 and abs(margin-data['safety'][i,1])<=1e-10 and value>=.15 and margin>=0;assert np.max(abs(data['mocap'][i,config['mocap_id']]-np.r_[motion.xy(t),0.]))<=1e-8;out.append([value,margin])
  all_safety.extend(out)
 # Prescribed actor mocap height is unchanged; XY and all original mocap states are checked separately.
 def check_actual(record,z,domain):
  global actual,packets
  a=np.load(raw/(record['label']+'_ACTUAL.npz'));assert len(a['qpos'])==328 and max(float(np.max(abs(a[k]-z[k])))for k in['qpos','qvel','controls'])<=1e-8;actual+=328;when=float(z['initial_time']);actual_geometry(a,when)
  for j,t in enumerate(when+np.arange(1,329)*.01):assert np.max(abs(a['mocap'][j,0,:2]-motion.xy(t)))<=1e-8
  updated=clone(domain)
  with gzip.open(raw/(record['label']+'_OBSERVATIONS.json.gz'),'rt')as f:observations=json.load(f)
  assert len(observations)==41
  for j,row in enumerate(observations):
   q=a['qpos'][8*j+7];pp=poses(q[None,:])[0];packet=row['packet'];step=round(when/.08)+j+1;assert packet['step']==step and abs(packet['time']-(when+(j+1)*.08))<=1e-9 and np.array_equal(np.asarray(packet['xy']),pp[:2].astype(np.float32).astype(float))and abs(packet['yaw']-pp[2])<=1e-12
   regenerated=sensed_packet(packet['xy'],packet['yaw'],packet['time'],step,p,motion,initial_calls);assert all(np.array_equal(packet[k],regenerated[k])for k in['lidar','depth']);updated.update(packet);assert encode(updated)==row['domain'];times=updated.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in times]);excess=float(updated.point_lower(truth,times).max());assert excess<=1e-7 and abs(excess-row['maximum_actual_coverage_excess_m'])<=1e-10;packets+=1
  end=poses(a['qpos'])[-1];hold=np.repeat([end],329,axis=0);future=np.linspace(0,3.28,329);fresh=float(np.minimum(pose_values(static,hold),updated.body_lower(hold,updated.time+future)).min());stale=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,updated.time+future)).min());assert max(abs(fresh-record['fresh_terminal_hold_geometry_m']),abs(stale-record['without_new_observation_terminal_hold_geometry_m']))<=1e-10 and encode(updated)['possible_bits_sha256']==record['actual_final_domain_sha256']
  return updated,a
 def check_prediction(record,domain,q,v,last,when,successor):
  global private
  z=np.load(raw/(record['label']+'_PRIVATE.npz'));assert max(np.max(abs(z['initial_qpos']-q)),np.max(abs(z['initial_qvel']-v)),np.max(abs(z['initial_ctrl']-last)),abs(float(z['initial_time'])-when))<=1e-10;assert z['qpos'].shape==(328,len(q))and np.max(abs(poses(z['qpos'])-z['poses']))<=1e-12
  target=np.asarray(record['target']);control=np.vstack([np.repeat([last],8,axis=0),sequence(target,last,320,160)])if record['hold_first']else sequence(target,last,328,248);assert np.array_equal(control,z['controls'])and np.all(control>=limits[:,0]-1e-12)and np.all(control<=limits[:,1]+1e-12);private+=328
  values=np.minimum(pose_values(static,z['poses']),domain.body_lower(z['poses'],when+np.arange(1,329)*.01));minimum=float(values.min());margin=float(containment_margin(z['self_bounds'],bounds).min());speed=float(np.linalg.norm(z['qvel'][-1,:2]));angular=float(np.linalg.norm(z['qvel'][-1,3:6]));progress=float(np.linalg.norm(q[:2]-p['goal_xy'])-np.linalg.norm(z['qpos'][-1,:2]-p['goal_xy']));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else'GOAL_PROGRESS'if successor and progress<.02 else None
  assert record['reason']==reason and record['admissible']==(reason is None)and record['minimum_causal_tick']==int(np.argmin(values))+1;assert max(abs(minimum-record['minimum_causal_clearance_m']),abs(margin-record['self_margin_m']),abs(speed-record['terminal_speed_m_s']),abs(angular-record['terminal_angular_speed_rad_s']),abs(progress-record['goal_progress_m']))<=1e-8
  return z
 actual_geometry(dict(qpos=replay['qpos'],safety=replay['safety'],mocap=replay['mocap']),0.)
 assert[(b['step'],b['amplitude'])for b in r['branches']]==[(s,a)for s in[73,90,130]for a in[0.,8.,-8.]]
 for b in r['branches']:
  step=b['step'];q=replay['qpos'][8*step-1];v=replay['qvel'][8*step-1];last=replay['controls'][8*step-1,ids];when=float(bases[step].time);domain=clone(bases[step]);initial=q.copy();complete=0
  for c in b['cycles']:
   scan=c['scan'];assert scan['hold_first']and scan['target']==[0.,0.,-b['amplitude'],b['amplitude']];z=check_prediction(scan,domain,q,v,last,when,False)
   if not scan['admissible']:assert not c['successors']and c['selected_successor']is None;break
   domain,a=check_actual(scan,z,domain);q=a['qpos'][-1];v=a['qvel'][-1];last=a['controls'][-1];when=float(domain.time);eligible=[];proofs={};assert len(c['successors'])==5
   for candidate in c['successors']:
    proof=check_prediction(candidate,domain,q,v,last,when,True);proofs[candidate['index']]=proof
    if candidate['admissible']:eligible.append(candidate)
   if not eligible:assert c['selected_successor']is None;break
   selected=max(eligible,key=lambda x:(x['goal_progress_m'],x['minimum_causal_clearance_m'],-x['index']));assert selected['index']==c['selected_successor'];domain,a=check_actual(selected,proofs[selected['index']],domain);q=a['qpos'][-1];v=a['qvel'][-1];last=a['controls'][-1];when=float(domain.time);complete+=1
  progress=float(np.linalg.norm(initial[:2]-p['goal_xy'])-np.linalg.norm(q[:2]-p['goal_xy']));assert abs(progress-b['total_goal_progress_m'])<=1e-10 and complete==b['completed_cycles']and b['qualified']==(complete==2 and progress>0)
  records.append(dict(step=step,amplitude=b['amplitude'],completed_cycles=complete,qualified=b['qualified'],total_goal_progress_m=progress,outcome=b['outcome']));dump('PROGRESS.json',records)
 contactlines=bad=0
 with gzip.open(raw/'ACTUAL_CONTACTS.jsonl.gz','rt')as stream:
  for line in stream:
   row=json.loads(line);contactlines+=1;bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in row['contacts'])
 assert len(records)==9 and contactlines==1040+actual and bad==0 and private==r['private_integrations']<=35424 and actual==r['scene_validation_integrations']<=11808 and packets==r['actual_new_packets']and packets*8==actual
 qualified=all(any(b['qualified']and b['amplitude']!=0 for b in records if b['step']==s)for s in[73,130]);assert qualified==r['component_qualified'];assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='PREEMPTIVE_CYCLE_SAVED_EVIDENCE_VERIFIED';dump('RESULT.json',dict(status=status,component_qualified=qualified,branches=records,original_replay_steps=1040,private_integrations=private,scene_validation_integrations=actual,actual_new_packets=packets,forecast_coverage_samples=packets*329,bad_contacts=bad,minimum_actual_native_clearance_m=float(np.asarray(all_safety)[:,0].min()),new_initializations=0,new_integrations=0,new_navigation_samples=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
