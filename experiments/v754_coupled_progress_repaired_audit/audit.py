"""Reconstruct closed two-cycle evidence, with initialization/integration blocked."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation'
sys.path.insert(0,str(source));sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'));sys.path.insert(2,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'))
import mujoco
def forbidden(*a,**kw):raise RuntimeError('V754_MODEL_INITIALIZATION_OR_INTEGRATION_FORBIDDEN')
for n in ['MjModel','MjSpec','MjData','mj_step','mj_step1','mj_step2','mj_forward']:setattr(mujoco,n,forbidden)
from dynamic_scene import Motion
from exact_footprint import pose_values
from self_geometry import containment_margin
from recursive_domain import RecursiveDomain
from renewal_state import encode
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
repo=Path(__file__).resolve().parents[2];raw=repo/'runs/v753_coupled_progress_repaired';root=repo/'runs/v754_coupled_progress_repaired_audit';root.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();started=time.time();window=dict(started_unix=started,absolute_deadline_unix=started+600,limit_s=600,round_closed=False,new_initializations=0,new_integrations=0)
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
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('V754_600S_ABSOLUTE_STOP')));signal.alarm(600);dump('ROUND_WINDOW.json',window);status='RUNNING';records=[]
try:
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 freeze=read(repo/'experiments/v753_coupled_progress_repaired/INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items());r=read(raw/'RESULT.json');assert r['status']=='FIXED_COUPLED_OBSERVATION_PROGRESS_DIAGNOSIS_COMPLETE'and read(raw/'ROUND_WINDOW.json')['round_closed']
 pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';p=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];contract=read(cell/'ACTUATOR_COMMAND_CONTRACT.json');ids=contract['ids'];limits=np.asarray(contract['limits']);rate=np.asarray(contract['rate']);bounds=np.asarray(p['footprint_bounds']);static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(p['known_rectangles']).reshape(-1,4),circles=np.asarray(p['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:old=[json.loads(s)for s in f]
 beliefs={x['step']:x for x in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())};domain=RecursiveDomain(p['start_qpos'][:2])
 for pkt in old:
  assert packet_equal(pkt,sensed_packet(pkt['xy'],pkt['yaw'],pkt['time'],pkt['step'],p,motion,initial_calls));domain.update(pkt);assert encode(domain)==beliefs[pkt['step']]['free_space_renewal']
  if pkt['step']==32:base=clone(domain)
 assert len(old)==177
 rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];replay=np.load(raw/'ORIGINAL_256_NATIVE_REPLAY.npz');assert replay['qpos'].shape[0]==256;old_replay=np.load(repo/'runs/v746_early_observation_handover/ORIGINAL_944_NATIVE_REPLAY.npz')
 for key in ['qpos','qvel','mocap','safety']:assert np.array_equal(replay[key],old_replay[key][:256])
 assert np.array_equal(replay['controls'],old_replay['controls'][:256,ids])
 initialq=replay['qpos'][-1];initialv=replay['qvel'][-1];initialc=replay['controls'][-1];all_safety=[];actual=packets=0;private=0;adapter_checks=0
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
 sys.path.insert(0,str(repo/'experiments/v753_coupled_progress_repaired'))
 from retained_coupled import prepare_retained
 def adapter(record,z,domain,negative=False):
  global adapter_checks
  import copy
  proof=dict(schema='V749_COUPLED_01',created_step=round(float(z['initial_time'])/.08),start_time=float(z['initial_time']),prefix_command=z['initial_ctrl'].tolist(),target=record['target'],controls=z['controls'].tolist(),qpos=z['qpos'].tolist(),qvel=z['qvel'].tolist(),poses=z['poses'].tolist(),forecast_state=dict(center=None,time=domain.time,hidden_world_geometry_used=False,free_space_renewal=encode(domain)),minimum_causal_predicted_clearance_m=record['minimum_causal_clearance_m'],minimum_predicted_self_domain_margin_m=record['self_margin_m'],terminal_speed_m_s=record['terminal_speed_m_s'],terminal_angular_speed_rad_s=record['terminal_angular_speed_rad_s'],total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False)
  ctrl=np.zeros(len(rows[0]['ctrl']));ctrl[ids]=z['initial_ctrl'];real=SimpleNamespace(qpos=z['qpos'][7].copy(),qvel=z['qvel'][7].copy(),ctrl=ctrl,time=float(z['initial_time'])+.08);before=copy.deepcopy(real);cache,evidence=prepare_retained(proof,real,SimpleNamespace(ids=ids,sequence=sequence));assert all(np.array_equal(cache[k],z[k][8:])for k in ['qpos','qvel','poses','controls'])and cache['recovery_kind']=='COUPLED_OBSERVATION_BRAKE';assert np.array_equal(cache['initial_qpos'],z['qpos'][7])and np.array_equal(cache['initial_qvel'],z['qvel'][7])and abs(cache['start_time']-real.time)<=1e-12 and all(np.array_equal(getattr(real,k),getattr(before,k))for k in ['qpos','qvel','ctrl']);adapter_checks+=1
  if negative:
   for mode in ['qpos','qvel','time','ctrl','schedule']:
    test=copy.deepcopy(real);changed=copy.deepcopy(proof)
    if mode in ['qpos','qvel']:getattr(test,mode)[0]+=.001
    elif mode=='time':test.time+=.01
    elif mode=='ctrl':test.ctrl[ids[0]]+=.01
    else:changed['controls'][8][2]+=.001
    try:prepare_retained(changed,test,SimpleNamespace(ids=ids,sequence=sequence))
    except AssertionError:pass
    else:raise AssertionError('NEGATIVE_JOIN_ACCEPTED')
 def observe(row,q,step,domain):
  pkt=row['packet'];pp=poses(q[None,:])[0];assert pkt['step']==step and abs(pkt['time']-(step*.08))<=1e-9 and np.array_equal(np.asarray(pkt['xy']),pp[:2].astype(np.float32).astype(float))and pkt['yaw']==sensor_pose(q)[1] and packet_equal(pkt,sensed_packet(pkt['xy'],pkt['yaw'],pkt['time'],step,p,motion,initial_calls));domain.update(pkt);assert row['domain']==encode(domain);times=domain.time+np.linspace(0,3.28,329);excess=float(domain.point_lower(np.asarray([motion.xy(t)for t in times]),times).max());assert excess<=1e-7 and abs(excess-row['maximum_actual_coverage_excess_m'])<=1e-10
 geometry(replay,0.);cal=read(raw/'CALIBRATION.json');cr=cal['record'];cz=prediction(cr,initialq,initialv,initialc,base);assert cr['admissible']and cr['target']==[0.,0.,8.,-8.];adapter(cr,cz,base,True)
 with gzip.open(cell/'observation_scan_certificate.json.gz','rt')as f:oldcert=json.load(f)
 assert max(np.max(abs(cz[k]-oldcert[k]))for k in ['qpos','qvel','controls','poses'])<=1e-8
 ca=np.load(raw/'CALIBRATION_ACTUAL.npz');assert all(np.max(abs(ca[k]-cz[k]))<=1e-8 for k in ['qpos','qvel','controls']);geometry(ca,base.time);cd=clone(base)
 with gzip.open(raw/'CALIBRATION_OBSERVATIONS.json.gz','rt')as f:co=json.load(f)
 for j,o in enumerate(co):observe(o,ca['qpos'][8*j+7],33+j,cd);assert packet_equal(o['packet'],old[33+j])and o['domain']==beliefs[33+j]['free_space_renewal']
 assert len(co)==41 and cal['negative_cases']==['qpos','qvel','time','ctrl','schedule']and cal['original_replay']==584
 expected_order=[];qualified_profiles=[]
 for profile in ['STRAIGHT','LEFT_RIGHT','RIGHT_LEFT']:
  main=next(b for b in r['branches']if b['name']==profile+'_MAIN');expected_order.append(main['name'])
  if main['qualified']:expected_order.append(profile+'_REPEAT');qualified_profiles.append(profile)
 assert [b['name']for b in r['branches']]==expected_order
 native_by_context={'BASELINE':{key:np.concatenate([replay[key],ca[key]])for key in ['qpos','qvel','controls','mocap','safety']}}
 for b in r['branches']:
  name=b['name'];profile=b['profile'];a=np.load(raw/(name+'_ACTUAL.npz'));trace=read(raw/(name+'_TRACE.json'));assert len(trace)==b['public_steps']<=137 and len(a['qpos'])==b['actual_native']==8*len(trace)
  with gzip.open(raw/(name+'_OBSERVATIONS.json.gz'),'rt')as f:obs=json.load(f)
  assert len(obs)==len(trace)==b['actual_packets'];domain=clone(base);q=initialq.copy();v=initialv.copy();last=initialc.copy();decisions={d['local_public']:d for d in b['decisions']};active=None;active_created=None;fallback=False;failed_at=None;checked=0
  for local,t in enumerate(trace):
   if local<96 and local%4==0 and not fallback:
    d=decisions[local];phase=local//24;lr=(2.,2.)if profile=='STRAIGHT'else((-4.,8.)if(phase%2==0)==(profile=='LEFT_RIGHT')else(8.,-4.));assert d['target']==[0.,0.,*lr]and d['phase']==phase and d['old_cache_unchanged']is True and d['old_cache_present']==(active is not None)and d['domain_sha256']==encode(domain)['possible_bits_sha256'];assert d['old_native_cursor']==(0 if active is None else(local-active_created-1)*8);z=prediction(d,q,v,last,domain);checked+=1
    if d['admissible']:adapter(d,z,domain);active=z;active_label=d['label'];active_created=local
    else:fallback=True;failed_at=local
   assert active is not None;idx=(local-active_created)*8;assert t['certificate']==active_label and t['full_native_index']==idx and t['local_public']==local+1 and t['public']==33+local and t['mode']==('NEW_CERTIFIED_HELD_PREFIX'if idx==0 else'RETAINED_CERTIFIED_TAIL')
   assert np.array_equal(t['command'],active['controls'][idx]);segment=slice(8*local,8*local+8)
   assert max(np.max(abs(a['qpos'][segment]-active['qpos'][idx:idx+8])),np.max(abs(a['qvel'][segment]-active['qvel'][idx:idx+8])),np.max(abs(a['controls'][segment]-active['controls'][idx:idx+8])))<=1e-8
   command=np.asarray(t['command']);assert np.all(abs(command-last)<=rate+1e-12)and np.all(command>=limits[:,0]-1e-12)and np.all(command<=limits[:,1]+1e-12);q=a['qpos'][8*local+7];v=a['qvel'][8*local+7];last=a['controls'][8*local+7];observe(obs[local],q,33+local,domain)
  # An initial rejected contract has no executed sample or sensor packet.
  if not trace:
   d=decisions[0];assert d['target']==[0.,0.,*((2.,2.)if profile=='STRAIGHT'else(-4.,8.)if profile=='LEFT_RIGHT'else(8.,-4.))];z=prediction(d,q,v,last,domain);assert not d['admissible'];checked=1;fallback=True;failed_at=0
  assert checked==len(decisions)==b['attempted_refreshes']and sum(d['admissible']for d in decisions.values())==b['accepted_refreshes'];actual+=len(trace)*8;packets+=len(obs)
  if trace:geometry(a,base.time);assert (len(trace)-active_created)*8==328
  progress96=None if len(trace)<96 else float(np.linalg.norm(initialq[:2]-p['goal_xy'])-np.linalg.norm(a['qpos'][96*8-1,:2]-p['goal_xy']))
  stopped=bool(np.linalg.norm(v[:2])<=.025 and np.linalg.norm(v[3:6])<=.025);qualified=bool(not fallback and len(decisions)==24 and progress96 is not None and progress96>=.30 and stopped)
  assert qualified==b['qualified']and progress96==b['goal_progress_at_96_m']and stopped==b['terminal_stopped']and b['terminal_cache_complete']is True
  progress=float(np.linalg.norm(initialq[:2]-p['goal_xy'])-np.linalg.norm(q[:2]-p['goal_xy']));assert abs(progress-b['final_goal_progress_m'])<=1e-10 and b['private_integrations']==len(decisions)*328
  if b['repeat_of']is not None:
   other=np.load(raw/(b['repeat_of']+'_ACTUAL.npz'));assert all(a[k].shape==other[k].shape and np.max(abs(a[k]-other[k]))<=1e-8 for k in ['qpos','qvel','controls','mocap','safety'])
   with gzip.open(raw/(b['repeat_of']+'_OBSERVATIONS.json.gz'),'rt')as f:assert obs==json.load(f)
  native_by_context[name]={k:a[k]for k in ['qpos','qvel','controls','mocap','safety']};records.append(dict(name=name,profile=profile,qualified=qualified,public_steps=len(trace),accepted_refreshes=b['accepted_refreshes'],attempted_refreshes=len(decisions),first_rejected_local_public=failed_at,goal_progress_at_96_m=progress96,final_goal_progress_m=progress,outcome=b['outcome']));dump('PROGRESS.json',records)
 counter={k:0 for k in native_by_context};bad=0;count=0
 with gzip.open(raw/'ACTUAL_CONTACTS.jsonl.gz','rt')as f:
  for line in f:
   x=json.loads(line);key=x['context'];j=counter[key];counter[key]+=1;count+=1;assert x['account_step']==count
   for field in ['qpos','qvel','controls','mocap','safety']:assert np.max(abs(np.asarray(x[field])-native_by_context[key][field][j]))<=1e-12
   bad+=sum(c['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in x['contacts'])
 assert all(counter[k]==len(v['qpos'])for k,v in native_by_context.items())and count==584+actual and bad==0
 assert private==r['private_integrations']<=47560 and actual==r['actual_validation_native']<=6576 and packets==r['actual_new_packets']<=822 and packets*8==actual and r['qualified_profiles']==qualified_profiles and r['component_qualified']==bool(qualified_profiles)
 assert all(sha(repo/n)==h for n,h in freeze['files'].items());status='COUPLED_PROGRESS_SAVED_EVIDENCE_VERIFIED';dump('RESULT.json',dict(status=status,component_qualified=bool(qualified_profiles),qualified_profiles=qualified_profiles,branches=records,original_replay_native=584,private_integrations=private,actual_validation_native=actual,actual_new_packets=packets,old_replayed_packets=41,forecast_coverage_samples=packets*329,adapter_checks=adapter_checks,minimum_actual_clearance_m=float(np.asarray(all_safety)[:,0].min()),bad_contacts=bad,new_initializations=0,new_integrations=0,new_complete_navigation=0,new_confirmation=0))
except BaseException as e:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(status=status,round_closed=True,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window)
