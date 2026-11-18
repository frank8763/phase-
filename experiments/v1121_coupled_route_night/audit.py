"""Independent all-native physical/control/causal and complete-source audit."""
import sys,json,gzip,math,importlib.abc,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL_AUDIT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/rpccr_execution_core'));sys.path.insert(0,str(C))
import numpy as np
from source import Engine,initial,python_replay,remaining_rows,final_gate,digest,COUNTS,deterministic_admission
from bindings import Adapter,REQUIRED,ref
from pipeline import front_rows,complete_stop
from physical_ops import dump
import kernel
from braking_reserve import signed
from recovery_source import forecast_packet
from fresh import finite_plan
spec=importlib.util.spec_from_file_location('night_independent_scene_contract',R/'experiments/v1089_route_scene_contract/contract.py');scene=importlib.util.module_from_spec(spec);spec.loader.exec_module(scene)

def run(task):
 out=Path(task['output']);ph=out/'physics';result=json.loads((out/'RESULT.json').read_text());branch=json.loads((out/'RECOVERY_BRANCH.json').read_text())
 if branch['mode']=='LEGACY_NORMAL':
  spec=importlib.util.spec_from_file_location('night_existing_complete_audit',R/'experiments/v1089_route_scene_contract/audit.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.configure();m={'__name__':'night_legacy_audit','__file__':str(old.ORIGINAL)};exec(compile(old.patched_source(),str(old.ORIGINAL),'exec'),m);return m['audit'](task)
 s=json.loads((ph/'SETUP.json').read_text());scene.verify_saved(ph,task);raw=np.load(ph/'NATIVE_TRACE.npz');z={k:raw[k]for k in raw.files};raw.close();cmd=np.asarray(json.loads((ph/'BODY_COMMANDS.json').read_text()));q=z['qpos'];n=len(q);assert n==len(cmd)>0
 quat=q[:,3:7];yaw=np.arctan2(2*(quat[:,0]*quat[:,3]+quat[:,1]*quat[:,2]),1-2*(quat[:,2]**2+quat[:,3]**2));forward=z['qvel'][:,0]*np.cos(yaw)+z['qvel'][:,1]*np.sin(yaw);lateral=-z['qvel'][:,0]*np.sin(yaw)+z['qvel'][:,1]*np.cos(yaw);ctrl=z['ctrl'][:,s['actuator_ids']];entry=json.loads((out/'COUPLED_ENTRY.json').read_text());root=entry['packet']['native_tick'];journal=json.loads((out/'MODE_JOURNAL.json').read_text());assert len(journal)==n-root
 owner=kernel.Predictor(s,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.),kernel.PARAMETERS).adapter;owner.__class__=signed.Adapter;owner.last=np.zeros(4);owner.integral=0.;memories=[np.zeros(5)];ce=0.;binding=True;episode=False;episodes=[False];active=[False]
 for i,(c,u)in enumerate(zip(cmd,ctrl)):
  if i==root:owner.__class__=Adapter;owner.virtual_rate=.6
  if i:
   enc=np.r_[q[i-1,s['steering_qpos_addresses']],z['qvel'][i-1,s['steering_qvel_addresses']]];measured=[forward[i-1],z['qvel'][i-1,5]]
  else:enc=np.zeros(4);measured=[0.,0.]
  owner.encoders=lambda enc=enc:enc.copy();binding&=bool(abs(np.array(measured)-c[3:5]).max()<=1e-8)
  if i>=root:
   row=journal[i-root];assert row['before_native']==i and abs(np.asarray(row['last_ctrl'])-owner.last).max()<=1e-10 and abs(row['integral']-owner.integral)<=1e-10;assert row['episode']==episode and row['active']==bool(getattr(owner,'_steering_motion_active',False));owner.parked_target=row['target']if row['parked']else None
  actual=owner.compute(*c[[1,2,3,4,5]]);ce=max(ce,float(abs(actual-u).max()));memories.append(np.r_[owner.last,owner.integral])
  if i>=root and row['parked']:episode=True;assert np.max(abs(u[2:]))<=1e-10
  if abs(c[1])>=.005:episode=False
  episodes.append(episode);active.append(bool(getattr(owner,'_steering_motion_active',False)))
 def actual_packet(p):
  k=p['native_tick'];assert abs(p['sim_time']-.01*k)<=1e-7 and p['steering']['native_tick']==k
  assert k>0
  expected=np.r_[q[k-1,:2],yaw[k-1],forward[k-1],z['qvel'][k-1,5],q[k-1,s['steering_qpos_addresses']],z['qvel'][k-1,s['steering_qvel_addresses']],memories[k]];saved=np.r_[p['body'],p['steering']['position'],p['steering']['velocity'],p['controller_memory']['last_ctrl'],p['controller_memory']['integral']];assert abs(expected-saved).max()<=1e-8,'NONACTUAL_CAUSAL_PACKET'
  if'body_lateral'in p:assert abs(p['body_lateral']-lateral[k-1])<=1e-8 and p['coupled_episode']==episodes[k]and p['steering_motion_active']==active[k]
 maximum=np.zeros(3);used=[];cursor=0
 def tracking(ss,start,count):
  nonlocal maximum
  if not count:return
  dy=yaw[start:start+count]-ss[1:count+1,2];e=[float(np.linalg.norm(q[start:start+count,:2]-ss[1:count+1,:2],axis=1).max()),float(abs(np.arctan2(np.sin(dy),np.cos(dy))).max()),float(abs(np.array([kernel.virtual(row)for row in q[start:start+count,s['steering_qpos_addresses']]])-ss[1:count+1,6]).max())];maximum=np.maximum(maximum,e)
 for row in json.loads((out/'DIRECT_SEGMENTS.json').read_text()):
  assert row['origin_native']==cursor;p=json.loads((R/row['path']).read_text())
  if p['packet']['native_tick']:actual_packet(p['packet'])
  else:assert p['packet']['body'][:3]==task['start_xy']+[task['start_yaw']]or np.max(abs(np.asarray(p['packet']['body'][:3])-np.array(task['start_xy']+[task['start_yaw']])))<=1e-8
  rebuilt=finite_plan(s,p['packet'],p['source'],p['planned_body_requests'],p['scope']);assert rebuilt['passed'];ss=np.array(rebuilt['state_path']);assert abs(ss-p['state_path']).max()<=1e-8 and abs(np.array(rebuilt['predicted_actuator_controls'])-p['predicted_actuator_controls']).max()<=1e-8;count=row['executed_native'];assert np.array_equal(cmd[cursor:cursor+count][:,[1,2,5]],np.array(p['planned_body_requests'])[:count]);tracking(ss,cursor,count)
  if p['source']is not None:used.append((p['source'],cursor,count))
  cursor+=count
 assert cursor==root;actual_packet(entry['packet']);source=entry['source'];assert source['source_native_tick']==root;used.append((source,root,n-root));engine=Engine(s);model_error=0.;blocks=json.loads((out/'COUPLED_BLOCKS.json').read_text());schedule=json.loads((out/'COUPLED_SCHEDULE.json').read_text())if(out/'COUPLED_SCHEDULE.json').exists()else None
 if schedule:
  optimization=json.loads((out/'SOURCE_OPTIMIZATION.json').read_text());assert deterministic_admission(optimization['optimizer_exit'],optimization['optimizer_calls'])
  first,fu,*_=python_replay(s,initial(entry['packet']),schedule);COUNTS['python_native']+=len(fu);proof,_=final_gate(entry,first,fu,schedule);assert proof['passed']and all(r['raw_envelope_lower']>=REQUIRED+float(entry.get('mode_reserve',.001))-1e-10 for r in proof['mode_envelopes'])
  with np.load(out/'COUPLED_INITIAL_SOURCE.npz')as a:assert abs(a['states']-first).max()<=1e-8 and abs(a['controls']-fu).max()<=1e-8
 envelopes=json.loads((out/'MODE_ENVELOPES.json').read_text())if(out/'MODE_ENVELOPES.json').exists()else []
 for number,row in enumerate(blocks):
  assert row['number']==number and row['start_native']==cursor and row['offset']==cursor-root;actual_packet(row['packet']);current=dict(entry,packet=row['packet']);suffix=remaining_rows(schedule,row['offset']);ss,uu=engine.simulate(initial(row['packet']),suffix);proof,rr=final_gate(current,ss,uu,suffix)
  if suffix[0][3]and row['packet']['steering_motion_active']:
   anchor=np.array([e for e in envelopes if e['native']<cursor][-1]['anchor']);phase=ss[:int(suffix[0][2])+1];a,b=ref._old.Geometry(s['known'],source['periodic']).clearances(anchor[None,:]);low=float(min(a[0],b[0]))-.02-math.hypot(.44,.375)*.1;inside=bool(np.linalg.norm(phase[:,:2]-anchor[:2],axis=1).max()<=.02 and abs(np.arctan2(np.sin(phase[:,2]-anchor[2]),np.cos(phase[:,2]-anchor[2]))).max()<=.1);proof['checks']['coupled_mode_envelopes']=bool(low>=REQUIRED and inside and all(r['passed']for r in proof['mode_envelopes'][1:]));proof['passed']=bool(all(proof['checks'].values()))
  assert proof==row['proof']and proof['passed']and digest(ss)==row['cpp_states_sha256']and digest(uu)==row['cpp_controls_sha256']
  prefix=row['prefix'];ps,pu,mem,ep,act=python_replay(s,initial(row['packet']),front_rows(suffix,prefix));COUNTS['python_native']+=prefix;model_error=max(model_error,float(abs(ps-ss[:prefix+1]).max()),float(abs(pu-uu[:prefix]).max()));assert model_error<=1e-8
  if prefix!=2200:
   future=forecast_packet(row['packet'],ps[-1],mem[-1],prefix);future.update(body_lateral=float(ps[-1,4]),coupled_episode=bool(ep[-1]),steering_motion_active=bool(act[-1]));origin=dict(state=ps[-1].copy(),last_ctrl=mem[-1,:4].copy(),integral=float(mem[-1,4]),coupled_episode=bool(ep[-1]),steering_motion_active=bool(act[-1]));backup,_,_,_=complete_stop(dict(entry,packet=future),engine,origin);assert backup==row['backup']and backup['passed']
  count=row['executed'];assert count<=prefix and np.array_equal(cmd[cursor:cursor+count][:,[1,2,5]],rr[:count]);tracking(ss,cursor,count);cursor+=count
  if count<prefix:assert result.get('functional_refusal_safely_stopped')and number==len(blocks)-1
 if result.get('functional_refusal_safely_stopped'):
  refusal=json.loads((out/'FUNCTIONAL_REFUSAL.json').read_text());tail=json.loads((out/'FUNCTIONAL_FAILURE_STOP.json').read_text());assert cursor==tail['begin']and tail['end']==n and tail['native']==2200 and tail['passed'];actual_packet(refusal['packet']);proof,ss,uu,rr=complete_stop(dict(entry,packet=refusal['packet']),engine,initial(refusal['packet']));assert proof==refusal['stop_proof']and proof['passed'];assert np.array_equal(cmd[cursor:][:,[1,2,5]],rr);tracking(ss,cursor,2200);cursor=n
 assert cursor==n
 causal=kernel.load('night_independent_causal_ranges',R/'experiments/v1024_full_route_execution/causal.py');norm=kernel.load('night_independent_periodic_support',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');ev=causal.Evidence(s['known']);ev.periodic=norm.PeriodicSupport();targets={}
 for src,start,count in used:targets.setdefault(src['source_native_tick'],[]).append(src)
 with gzip.open(ph/'SENSORS.json.gz','rt')as f:sensors=json.load(f)
 assert len(sensors)>=3 and sensors[0]==sensors[1]==sensors[2];matched=0
 for scan in sensors[2:]:
  ev.update(scan)
  for src in targets.get(scan['native_tick'],[]):assert ev.periodic.snapshot()==src['periodic'];matched+=1
 observed=json.loads((out/'CAUSAL_EVIDENCE.json').read_text());assert observed['first']==ev.first;d=ev.first['native_tick'];normal=cmd[d-1,1]>.005;zero=np.array_equal(cmd[d:d+328][:,[1,2,5]],np.zeros((328,3)));normals=np.c_[np.cos(np.arange(8)*math.pi/8),np.sin(np.arange(8)*math.pi/8)];violation=-math.inf
 for src,start,count in used:
  if not count:continue
  tt=z['time'][start:start+count];xy=z['mocap_pos'][start:start+count,0,:2];basis=np.c_[np.ones(len(tt)),np.sin(.32*tt),np.cos(.32*tt)]
  for j,vertices in enumerate(src['periodic']['vertices']):
   bounds=basis@np.array(vertices).T;actual=xy@normals[j];violation=max(violation,float((actual-bounds.max(axis=1)).max()),float((bounds.min(axis=1)-actual).max()))
 with gzip.open(ph/'CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 limits=np.array(s['limits']);rates=np.array(s['slew_per_second'])*.01;distance=float(np.linalg.norm(q[-1,:2]-task['goal_xy']));motion=float(np.linalg.norm(q[-1,:2]-q[d+327,:2]));cc=dict(fresh_start=result['fresh_native_zero']and result['historical_replay_native']==0,all_native=n==result['new_actual_native']==result['physical']['fully_recorded_native']==result['physical']['root_guard_native_count'],entire_source_coverage=cursor==n,model_contract=scene.verify_saved(ph,task)['passed'],actual_tracking=bool(np.all(maximum<=[.04,.035,.015])),actual_clearance=float(z['clearance'].min())>=.15-1e-8,self_margin=float(z['self_margin'].min())>=-1e-10,contacts_complete=len(contacts)==n+1,no_bad_contacts=not any(c[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for cs in contacts for c in cs),ctrl_amplitude=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),ctrl_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),single_owner=ce<=1e-10 and binding,body_caps=bool(abs(forward).max()<=.13 and abs(lateral).max()<=.03 and abs(z['qvel'][:,5]).max()<=.16),full2200tail=np.array_equal(cmd[-2200:,[1,2,5]],np.zeros((2200,3))),terminal_stopped=bool(np.linalg.norm(z['qvel'][-50:,:2],axis=1).max()<=.003 and abs(z['qvel'][-50:,5]).max()<=.003),own_replay=result['replay']['passed']and result['own_replay_native']==n and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0,normal_discovery=normal and result['physical']['first_actor_detection']['native_tick']==d,actual328brake=zero and np.linalg.norm(z['qvel'][d+327,:2])<=.03,live_causal_domain=matched==len(used),offline_actor_domain=violation<=2.1e-7,clock=float(abs(z['time']-np.arange(1,n+1)*.01).max())<=1e-7)
 mode_ok=True
 for e in envelopes:
  k=e['native'];anchor=np.asarray(e['anchor']);assert np.max(abs(np.r_[q[k-1,:2],yaw[k-1]]-anchor))<=1e-8;a,b=ref._old.Geometry(s['known'],source['periodic']).clearances(anchor[None,:]);mode_ok&=float(min(a[0],b[0]))-.02-math.hypot(.44,.375)*.1>=REQUIRED
  for i in range(k,n):
   if abs(cmd[i,1])>=.005:break
   mode_ok&=bool(np.linalg.norm(q[i,:2]-anchor[:2])<=.02 and abs(math.atan2(math.sin(yaw[i]-anchor[2]),math.cos(yaw[i]-anchor[2])))<=.1)
 cc['coupled_actual_envelopes']=mode_ok;evidence_passed=bool(all(cc.values()));functional=result['passed']and distance<=.45 and motion>=1.;answer=dict(passed=bool(evidence_passed and functional),evidence_passed=evidence_passed,functional_passed=bool(functional),checks={k:bool(v)for k,v in cc.items()},actual_goal_distance_m=distance,actual_post_discovery_motion_m=motion,minimum_actual_clearance_m=float(z['clearance'].min()),maximum_tracking=maximum.tolist(),maximum_controller_error=ce,maximum_cpp_python_prefix_error=model_error,cpp_audit_native=engine.native,python_audit_native=COUNTS['python_native'],models=0,physical_integrations=0);dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
if __name__=='__main__':
 x=run(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(x),flush=True);sys.exit(0 if x.get('evidence_passed',x['passed'])else 1)
