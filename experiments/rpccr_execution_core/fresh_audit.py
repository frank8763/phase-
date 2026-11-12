"""All-native fresh navigation audit; regenerate live sources from recorded sensors."""
import sys,json,gzip,math,importlib.abc
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL_AUDIT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));import numpy as np
import live_reference as live
from prediction import Predictor,initial
from braking_reserve import Adapter,signed
from kernel import PARAMETERS,virtual,ref,REQUIRED,Geometry,load
from physical_ops import dump

def audit(task):
 out=Path(task['output']);ph=out/'physics';rp=out/'RESULT.json';rp=rp if rp.exists()else ph/'paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text());assert result['passed']and result['historical_replay_native']==0 and result['fresh_native_zero'];setup=json.loads((ph/'SETUP.json').read_text());raw=np.load(ph/'NATIVE_TRACE.npz');z={k:raw[k]for k in raw.files};raw.close();cmd=np.array(json.loads((ph/'BODY_COMMANDS.json').read_text()));q=z['qpos'];n=len(cmd);yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));forward=z['qvel'][:,0]*np.cos(yaw)+z['qvel'][:,1]*np.sin(yaw);ctrl=z['ctrl'][:,setup['actuator_ids']];entry=json.loads((out/'LIVE_ENTRY.json').read_text());root=entry['packet']['native_tick'];engine=Predictor(setup,initial(entry['packet']),PARAMETERS);engine.adapter.__class__=signed.Adapter;engine.adapter.last=np.zeros(4);engine.adapter.integral=0.;memories=[np.zeros(5)];ce=0.
 for i,(c,u)in enumerate(zip(cmd,ctrl)):
  if i==root:engine.adapter.__class__=Adapter
  if i>=root:
   enc=np.r_[q[i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];engine.adapter.encoders=lambda enc=enc:enc
  actual=engine.adapter.compute(*c[[1,2,3,4,5]]);ce=max(ce,float(abs(actual-u).max()));memories.append(np.r_[engine.adapter.last,engine.adapter.integral])
 def actual_packet(p):
  tick=p['native_tick'];assert tick==p['steering']['native_tick']and abs(p['sim_time']-.01*tick)<=1e-7
  if tick:
   expected=np.r_[q[tick-1,:2],yaw[tick-1],forward[tick-1],z['qvel'][tick-1,5],q[tick-1,setup['steering_qpos_addresses']],z['qvel'][tick-1,setup['steering_qvel_addresses']],memories[tick]]
   saved=np.r_[p['body'],p['steering']['position'],p['steering']['velocity'],p['controller_memory']['last_ctrl'],p['controller_memory']['integral']];assert abs(expected-saved).max()<=1e-8,'NONACTUAL_INPUT'
  else:assert p['body'][:3]==task['start_xy']+[task['start_yaw']]and np.array_equal(p['controller_memory']['last_ctrl'],np.zeros(4))
 maximum=np.zeros(3);cursor=0;used=[]
 def tracking(ss,count):
  nonlocal maximum
  a=yaw[cursor:cursor+count]-ss[1:count+1,2];e=np.array([np.linalg.norm(q[cursor:cursor+count,:2]-ss[1:count+1,:2],axis=1).max(),abs(np.arctan2(np.sin(a),np.cos(a))).max(),abs(np.array([virtual(x)for x in q[cursor:cursor+count,setup['steering_qpos_addresses']]])-ss[1:count+1,6]).max()]);maximum=np.maximum(maximum,e)
 from fresh import finite_plan
 for row in json.loads((out/'DIRECT_SEGMENTS.json').read_text()):
  assert row['origin_native']==cursor;p=json.loads((R/row['path']).read_text());actual_packet(p['packet']);rebuilt=finite_plan(setup,p['packet'],p['source'],p['planned_body_requests'],p['scope']);assert rebuilt['passed'];ss=np.array(rebuilt['state_path']);assert abs(ss-p['state_path']).max()<=1e-8 and abs(np.array(rebuilt['predicted_actuator_controls'])-p['predicted_actuator_controls']).max()<=1e-8;count=row['executed_native'];assert np.array_equal(cmd[cursor:cursor+count][:,[1,2,5]],np.array(p['planned_body_requests'])[:count]);tracking(ss,count)
  if p['source']is not None:used.append((p['source'],cursor,count))
  cursor+=count
 assert cursor==root;actual_packet(entry['packet']);source=entry['source'];assert source['source_native_tick']==root;used.append((source,root,n-root));cfg=json.loads((Path(task['run_root'])/'CONFIG.json').read_text());proposal=live.produce(setup,entry['packet'],source,Path(task['run_root']),task['goal_xy']);saved=json.loads((out/'LIVE_SOURCE_PROOF.json').read_text());assert saved['chosen']==proposal['proof']and saved['candidates']==proposal['candidates']and saved['static']['actions']==proposal['static']['actions'];reference=proposal['reference']
 with np.load(out/'LIVE_REFERENCE.npz')as p:assert np.array_equal(p['nominal_requests'],proposal['nominal_requests'])and abs(p['nominal_states']-proposal['nominal_states']).max()<=1e-8
 wait=json.loads((out/'LIVE_WAIT_EXECUTION.json').read_text());count=len(proposal['wait_requests']);assert wait['start_native']==cursor and wait['executed_native']==count;assert np.array_equal(cmd[cursor:cursor+count][:,[1,2,5]],proposal['wait_requests']);tracking(proposal['wait_states'],count)
 with np.load(out/'LIVE_WAIT.npz')as p:assert np.array_equal(p['requests'],proposal['wait_requests'])and abs(p['states']-proposal['wait_states']).max()<=1e-8 and abs(p['controls']-proposal['wait_controls']).max()<=1e-8
 cursor+=count;blocks=json.loads((out/'BLOCKS.json').read_text());progress=0;moving=0;minimum=math.inf
 for j,row in enumerate(blocks):
  assert row==json.loads((out/'certificates'/f'{j}.json').read_text())and row['start_native']==cursor and row['progress']==progress and row['remaining_active']==live.MAX_ACTIVE-moving;actual_packet(row['packet']);assert row['packet']['speed_episode']==bool(np.any(cmd[root:cursor,1]==.125));assert row['source_native_tick']==root and abs(row['source_age_s']-(row['packet']['sim_time']-source['periodic']['last']))<=1e-8
  proof,ss,uu,rr,indices=reference.complete(setup,row['packet'],source,progress,live.MAX_ACTIVE-moving);assert proof==row['proof']and proof['passed'];minimum=min(minimum,proof['minimum_raw_m'])
  with np.load(out/'certificates'/f'{j}.npz')as p:assert np.array_equal(p['requests'],rr)and np.array_equal(p['progress'],indices)and abs(p['states']-ss).max()<=1e-8 and abs(p['controls']-uu).max()<=1e-8
  stop=proof['active_native']==0;count=live.STOP if stop else min(live.BLOCK,proof['active_native']);assert row['executed_native']==row['planned_prefix']==count and np.array_equal(cmd[cursor:cursor+count][:,[1,2,5]],rr[:count]);tracking(ss,count);cursor+=count;progress=int(indices[count-1]);moving+=0 if stop else count
  if stop:assert j==len(blocks)-1
 assert cursor==n and blocks[-1]['proof']['active_native']==0;cross=0.
 for pose in q[root+len(proposal['wait_requests']):,:2]:cross=max(cross,float(np.linalg.norm(reference.path[:,:2]-pose,axis=1).min()))
 causal=load('fresh_audit_causal_ranges',R/'experiments/v1024_full_route_execution/causal.py');norm=load('fresh_audit_public_periodic',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');evidence=causal.Evidence(setup['known']);evidence.periodic=norm.PeriodicSupport();targets={}
 for src,start,count in used:targets.setdefault(src['source_native_tick'],[]).append(src)
 with gzip.open(ph/'SENSORS.json.gz','rt')as f:sensors=json.load(f)
 assert len(sensors)>=3 and sensors[0]==sensors[1]==sensors[2]and sensors[2]['native_tick']==0
 matched=0
 for scan in sensors[2:]:
  evidence.update(scan)
  for src in targets.get(scan['native_tick'],[]):assert evidence.periodic.snapshot()==src['periodic'];matched+=1
 observed=json.loads((out/'CAUSAL_EVIDENCE.json').read_text());assert observed['first']==evidence.first;first=evidence.first;d=first['native_tick'];distance=float(np.linalg.norm(q[-1,:2]-task['goal_xy']));motion=float(np.linalg.norm(q[-1,:2]-q[d+327,:2]));normal=cmd[d-1,1]>.005;zero=np.array_equal(cmd[d:d+328][:,[1,2,5]],np.zeros((328,3)));normals=np.c_[np.cos(np.arange(8)*math.pi/8),np.sin(np.arange(8)*math.pi/8)];violation=-math.inf
 for src,start,count in used:
  tt=z['time'][start:start+count];xy=z['mocap_pos'][start:start+count,0,:2];basis=np.c_[np.ones(len(tt)),np.sin(.32*tt),np.cos(.32*tt)]
  for j,vertices in enumerate(src['periodic']['vertices']):
   bounds=basis@np.array(vertices).T;actual=xy@normals[j];violation=max(violation,float((actual-bounds.max(axis=1)).max()),float((bounds.min(axis=1)-actual).max()))
 with gzip.open(ph/'CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 limits=np.array(setup['limits']);rates=np.array(setup['slew_per_second'])*.01
 cc=dict(fresh_start_and_no_history=result['fresh_native_zero']and result['historical_replay_native']==0,all_native=n==result['navigation_native']==result['new_actual_native']==len(q)==result['physical']['root_guard_native_count']==result['physical']['fully_recorded_native'],entire_source_coverage=cursor==n,canonical_model=setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8',actual_local_tracking=np.all(maximum<=[.04,.035,.015]),actual_path_cross_track=cross<=.04,actual_clearance=z['clearance'].min()>=.15-1e-8,self_margin=z['self_margin'].min()>=-1e-10,contacts_complete=len(contacts)==n+1,no_bad_contacts=not any(c[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for cs in contacts for c in cs),ctrl_amplitude=(ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all(),ctrl_slew=(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all(),single_ctrl_owner=ce<=1e-10,body_speed=abs(forward).max()<=.13 and abs(z['qvel'][:,5]).max()<=.16,full2200tail=np.array_equal(cmd[-2200:,[1,2,5]],np.zeros((2200,3))),last328stopped=np.linalg.norm(z['qvel'][-328:,:2],axis=1).max()<=.03 and abs(z['qvel'][-328:,5]).max()<=.03,full_own_replay=result['replay']['passed']and result['own_replay_native']==n and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0,normal_discovery=normal and result['physical']['first_actor_detection']['native_tick']==d,actual328brake=zero and np.linalg.norm(z['qvel'][d+327,:2])<=.03,causal_domains_from_live_ranges=matched==len(used),offline_actor_domain=violation<=2.1e-7,goal=distance<=.45,actual_over1m=motion>=1.,clock=abs(z['time']-np.arange(1,n+1)*.01).max()<=1e-7,live_prediction_accounting=live.PREDICTION_NATIVE==result['analytical_prediction_native'])
 cc={k:bool(v)for k,v in cc.items()};answer=dict(passed=all(cc.values()),checks=cc,fresh_navigation_native=n,historical_replay_native=0,actual_goal_distance_m=distance,post_discovery_stop_motion_m=motion,minimum_actual_clearance_m=float(z['clearance'].min()),maximum_local_tracking=maximum.tolist(),maximum_reference_cross_track_m=cross,maximum_control_reconstruction_error=ce,minimum_dynamic_prediction_raw_m=minimum,offline_domain_violation=violation,analytical_prediction_native=live.PREDICTION_NATIVE,models=0,integrations=0);dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
if __name__=='__main__':
 answer=audit(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(answer),flush=True);sys.exit(0 if answer['passed']else 1)
