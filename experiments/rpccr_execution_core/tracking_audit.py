"""No-model audit: reconstruct every input, complete certificate and applied prefix."""
import sys,json,gzip,math,importlib.abc
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL_AUDIT '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));import numpy as np
from plans import ARCH,REC
from prediction import Predictor,initial
from braking_reserve import Adapter,signed
from kernel import PARAMETERS,virtual,Geometry,REQUIRED
from path_tracking import complete_from_measurement,select_reference,reference,MAX_ACTIVE,STOP_NATIVE,BLOCK
from physical_ops import dump

def audit(task):
 out=Path(task['output']);ph=out/'physics';rp=out/'RESULT.json';rp=rp if rp.exists()else ph/'paired/ENTRY_FAILURE_RESULT.json';result=json.loads(rp.read_text());assert result['passed'];setup=json.loads((ph/'SETUP.json').read_text());archive=np.load(ph/'NATIVE_TRACE.npz');z={k:archive[k]for k in archive.files};archive.close();cmd=np.asarray(json.loads((ph/'BODY_COMMANDS.json').read_text()));inp=json.loads((out/'ACTUAL_INPUT.json').read_text());hist=18074;n=len(cmd)
 source=json.loads((REC/'REMAINDER_INPUT.json').read_text())['source'];assert inp['source']==source and source['source_native_tick']==15290
 engine=Predictor(setup,initial(inp['packet']),PARAMETERS);engine.adapter.__class__=signed.Adapter;engine.adapter.last=np.zeros(4);engine.adapter.integral=0.;ctrl=z['ctrl'][:,setup['actuator_ids']];ce=0.;reserve_count=0
 blocks=json.loads((out/'BLOCKS.json').read_text());starts={b['start_native']:b for b in blocks};assert len(starts)==len(blocks)
 q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));forward=z['qvel'][:,0]*np.cos(yaw)+z['qvel'][:,1]*np.sin(yaw);packet_error=0.
 for i,(c,u)in enumerate(zip(cmd,ctrl)):
  if i==hist:engine.adapter.__class__=Adapter
  if i in starts:
   p=starts[i]['packet'];steerq=q[i-1,setup['steering_qpos_addresses']];steerv=z['qvel'][i-1,setup['steering_qvel_addresses']]
   actual=np.r_[q[i-1,:2],yaw[i-1],forward[i-1],z['qvel'][i-1,5],steerq,steerv,engine.adapter.last,engine.adapter.integral]
   saved=np.r_[p['body'],p['steering']['position'],p['steering']['velocity'],p['controller_memory']['last_ctrl'],p['controller_memory']['integral']]
   packet_error=max(packet_error,float(abs(actual-saved).max()));assert p['native_tick']==p['steering']['native_tick']==i and abs(p['sim_time']-z['time'][i-1])<=1e-8
   assert p['speed_episode']==bool(getattr(engine.adapter,'_speed_episode',False))
  if i>=hist:
   enc=np.r_[q[i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];engine.adapter.encoders=lambda enc=enc:enc
  selected=engine.adapter.compute(float(c[1]),float(c[2]),float(c[3]),float(c[4]),bool(c[5]));ce=max(ce,float(abs(selected-u).max()))
  if i>=hist:
   p=engine.adapter.last_braking_reserve;selected_proof=p['backup']if p.get('backup_selected')else p;assert selected_proof['maximum_braking_speed_upper']<=.13+1e-10;reserve_count+=bool(p.get('limited')or p.get('backup_selected'))
 offset,candidates=select_reference(setup,inp['packet'],source);selection=json.loads((out/'REFERENCE_SELECTION.json').read_text());assert selection['offset_m']==offset and selection['candidates']==candidates
 maximum=np.zeros(3);cursor=hist;progress=0;moving=0;minimum=math.inf;prediction_native=sum(c.get('active_native',0)+STOP_NATIVE for c in candidates if'active_native'in c);plan_error=0.
 for number,row in enumerate(blocks):
  assert row==json.loads((out/'certificates'/f'{number}.json').read_text());assert row['number']==number and row['start_native']==cursor and row['progress']==progress and row['remaining_active']==MAX_ACTIVE-moving and row['offset_m']==offset
  assert row['source_native_tick']==15290 and abs(row['source_age_s']-(row['packet']['sim_time']-source['periodic']['last']))<=1e-8
  proof,ss,uu,rr,indices=complete_from_measurement(setup,row['packet'],source,progress,MAX_ACTIVE-moving,offset);assert proof==row['proof']and proof['passed']
  with np.load(out/'certificates'/f'{number}.npz')as pp:
   assert np.array_equal(pp['requests'],rr)and np.array_equal(pp['progress'],indices)
   plan_error=max(plan_error,float(abs(pp['states']-ss).max()),float(abs(pp['controls']-uu).max()))
  dense=Geometry(setup['known'],source['periodic'],row['packet']['sim_time']).complete(ss);assert dense>=REQUIRED;minimum=min(minimum,dense);prediction_native+=len(rr)
  stop=proof['active_native']==0;prefix=STOP_NATIVE if stop else min(BLOCK,proof['active_native']);assert row['executed_native']==row['planned_prefix']==prefix
  assert np.array_equal(cmd[cursor:cursor+prefix][:,[1,2,5]],rr[:prefix])
  angle=yaw[cursor:cursor+prefix]-ss[1:prefix+1,2];e=np.array([np.linalg.norm(q[cursor:cursor+prefix,:2]-ss[1:prefix+1,:2],axis=1).max(),abs(np.arctan2(np.sin(angle),np.cos(angle))).max(),abs(np.array([virtual(x)for x in q[cursor:cursor+prefix,setup['steering_qpos_addresses']]])-ss[1:prefix+1,6]).max()]);maximum=np.maximum(maximum,e)
  cursor+=prefix;progress=int(indices[prefix-1]);moving+=0 if stop else prefix
  if stop:assert number==len(blocks)-1
 assert cursor==n and blocks[-1]['proof']['active_native']==0
 path,arc=reference(offset);cross=0.
 for p in q[hist:,:2]:cross=max(cross,float(np.linalg.norm(path[:,:2]-p,axis=1).min()))
 with np.load(ARCH/'physics/NATIVE_TRACE.npz')as old:he=max(float(abs(z[k][:hist]-old[k]).max())if z[k].size else 0. for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat'])
 hp=json.loads((out/'HISTORICAL_REPLAY_PROOF.json').read_text())
 with gzip.open(ph/'CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01;d=result['physical']['first_actor_detection']['native_tick'];distance=float(np.linalg.norm(q[-1,:2]-task['goal_xy']));motion=float(np.linalg.norm(q[-1,:2]-q[hist-1,:2]));center=z['mocap_pos'][hist:,0,:2];normals=np.c_[np.cos(np.arange(8)*math.pi/8),np.sin(np.arange(8)*math.pi/8)];tt=z['time'][hist:];basis=np.c_[np.ones(len(tt)),np.sin(.32*tt),np.cos(.32*tt)];violation=-float('inf')
 for i,vertices in enumerate(source['periodic']['vertices']):
  bounds=basis@np.array(vertices).T;actual=center@normals[i];violation=max(violation,float((actual-bounds.max(axis=1)).max()),float((bounds.min(axis=1)-actual).max()))
 cc=dict(all_native=n==hist+moving+STOP_NATIVE==len(q)==result['physical']['root_guard_native_count']==result['physical']['fully_recorded_native'],exact_history=he<=1e-8 and hp['passed']and hp['range_error']<=1e-6,actual_measured_inputs=packet_error<=1e-8,complete_prediction=plan_error<=1e-8,all_executed_prefixes_exact=True,actual_local_tracking=np.all(maximum<=[.04,.035,.015]),actual_path_cross_track=cross<=.04,actual_clearance=z['clearance'].min()>=.15-1e-8,self_margin=z['self_margin'].min()>=-1e-10,contacts_complete=len(contacts)==n+1,no_bad_contacts=not any(c[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for cs in contacts for c in cs),ctrl_amplitude=(ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all(),ctrl_slew=(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all(),ctrl_owner=ce<=1e-10,body_speed=abs(forward).max()<=.13 and abs(z['qvel'][:,5]).max()<=.16,full2200tail=np.array_equal(cmd[-STOP_NATIVE:,[1,2,5]],np.zeros((STOP_NATIVE,3))),last328stopped=np.linalg.norm(z['qvel'][-328:,:2],axis=1).max()<=.03 and abs(z['qvel'][-328:,5]).max()<=.03,full_own_replay=result['replay']['passed']and result['own_replay_native']==n and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0,normal_discovery=cmd[d-1,1]>.005,actual328brake=np.array_equal(cmd[d:d+328][:,[1,2,5]],np.zeros((328,3)))and np.linalg.norm(z['qvel'][d+327,:2])<=.03,causal_source=source['source_native_tick']==15290 and inp['packet']['native_tick']==hist,offline_actor_domain=violation<=2e-6,goal=distance<=.45,actual_over1m=motion>=1.,clock=abs(z['time']-np.arange(1,n+1)*.01).max()<=1e-7,analytical_accounting=prediction_native==result['analytical_prediction_native'])
 cc={k:bool(v)for k,v in cc.items()};a=dict(passed=all(cc.values()),checks=cc,actual_goal_distance_m=distance,actual_motion_m=motion,maximum_local_tracking=maximum.tolist(),maximum_path_cross_track_m=cross,maximum_measured_packet_error=packet_error,owner_error=ce,reserve_activations=reserve_count,maximum_actual_longitudinal_speed=float(abs(forward[hist:]).max()),minimum_actual_clearance_m=float(z['clearance'].min()),minimum_complete_prediction_raw_m=minimum,offline_domain_violation=violation,certificates=len(blocks),analytical_prediction_native=prediction_native,models=0,integrations=0,new_main_samples=0);dump(out/'FINAL_INDEPENDENT_AUDIT.json',a);return a
if __name__=='__main__':
 a=audit(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(a),flush=True);sys.exit(0 if a['passed']else 1)
