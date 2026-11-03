"""Fixed early advance-to-observation handover qualification."""
import fcntl,gzip,hashlib,json,math,os,signal,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
repo=Path(os.environ['PHASE_REPO']);own=Path(__file__).parent;source=repo/'experiments/v735_scan_differential_navigation'
sys.path.insert(0,str(repo/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1'));sys.path.insert(0,str(source));sys.path.insert(0,str(own));sys.path.insert(1,str(repo/'runtime/mk-mini/training/phase14_lidar_depth_nav/envs'));sys.path.insert(1,str(repo/'experiments/v733_early_low_translation_scan'))
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from exact_footprint import pose_values
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from recursive_domain import RecursiveDomain
from renewal_state import decode,encode
from sensor_model import packet as sensed_packet
sys.path.insert(0,str(repo/'experiments/v745_observation_handover_preparation'))
from retained_observation import prepare_retained_observation
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v746_early_observation_handover';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def clone(domain):
 copy=RecursiveDomain(domain.origin);copy.time=domain.time;copy.possible=domain.possible.copy();copy.distance=domain.distance.copy();copy.last=dict(domain.last);return copy
started=float(os.environ['PHASE_V746_STARTED']);deadline=float(os.environ['PHASE_V746_DEADLINE']);assert abs(deadline-started-900)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=900,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def timeout(*_):raise TimeoutError('V746_FIXED_900S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
replay=validation=packets=0;predictor=None;records=[];status='RUNNING';min_actual=min_self=float('inf');max_replay=max_validation=0.;bad=0
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:old_packets=[json.loads(s)for s in stream]
  for packet in old_packets:
   regenerated=sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,initial_calls)
   assert all(np.array_equal(packet[k],regenerated[k])for k in['lidar','depth']),'ORIGINAL_SENSOR_BACKEND_NOT_EXACT'
  dump('SENSOR_CALIBRATION.json',dict(status='ALL_ORIGINAL_177_NOISY_PACKETS_EXACT',packets=len(old_packets),model_initializations=0,new_integrations=0))
  assert len(old_packets)==177
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);fixed_geom=m.geom_pos.copy()
  static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;contactlog=gzip.open(root/'ACTUAL_CONTACTS.jsonl.gz','wt')
  def physical(data,public):
   global min_actual,min_self,bad
   box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),config['radius_m']]])});clearance=float(pose_values(truth,poses(data.qpos[None,:]))[0]);contacts=[catalog.classify(c,replay+validation,public,float(data.time))for c in data.contact];bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts);contactlog.write(json.dumps(dict(account_step=replay+validation,time=float(data.time),public=public,contacts=contacts))+'\n');min_actual=min(min_actual,clearance);min_self=min(min_self,margin)
   assert clearance>=.15 and margin>=0 and bad==0 and np.array_equal(m.geom_pos,fixed_geom),'ACTUAL_SAFETY_OR_STATIC_MODEL_EXCEPTION';return [clearance,margin,*box.tolist()]
  snapshots={};domains={};rq=[];rv=[];rc=[];rm=[];rs=[]
  for row in rows[:73]:
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);rs.append(physical(d,row['step']));rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl.copy());rm.append(d.mocap_pos.copy())
   max_replay=max(max_replay,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert max_replay<=1e-8,'ORIGINAL_REPLAY_MISMATCH'
  legacy=repo/'runs/v740_preemptive_observation_cycles';oldresult=read(legacy/'RESULT.json');oldbranch=next(b for b in oldresult['branches']if b['step']==73 and b['amplitude']==-8.);oldscan=oldbranch['cycles'][0]['scan'];oldadvance=next(c for c in oldbranch['cycles'][0]['successors']if c['index']==4);base=clone(decode(beliefs[73]['free_space_renewal']))
  scan_z=np.load(legacy/(oldscan['label']+'_PRIVATE.npz'));scan_a=np.load(legacy/(oldscan['label']+'_ACTUAL.npz'));advance_z=np.load(legacy/(oldadvance['label']+'_PRIVATE.npz'));advance_a=np.load(legacy/(oldadvance['label']+'_ACTUAL.npz'))
  with gzip.open(legacy/(oldscan['label']+'_OBSERVATIONS.json.gz'),'rt')as f:scan_obs=json.load(f)
  with gzip.open(legacy/(oldadvance['label']+'_OBSERVATIONS.json.gz'),'rt')as f:advance_obs=json.load(f)
  def certificate(record,z,state,created):
   return dict(schema='V735_EARLY_SCAN_01',created_step=created,start_time=float(z['initial_time']),initial_qpos=z['initial_qpos'].tolist(),initial_qvel=z['initial_qvel'].tolist(),prefix_command=z['initial_ctrl'].tolist(),target=record['target'],controls=z['controls'].tolist(),qpos=z['qpos'].tolist(),qvel=z['qvel'].tolist(),poses=z['poses'].tolist(),forecast_state=state,minimum_causal_predicted_clearance_m=record['minimum_causal_clearance_m'],minimum_predicted_self_domain_margin_m=record['self_margin_m'],terminal_speed_m_s=record['terminal_speed_m_s'],terminal_angular_speed_rad_s=record['terminal_angular_speed_rad_s'],total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False)
  original_scan_proof=certificate(oldscan,scan_z,{k:v for k,v in beliefs[73].items()if k!='step'},73);baseline_retained=None;negative_cases=0;baseline_commands=0
  def checked_old_native(command,expected,tick,public):
   global replay,max_replay
   d.ctrl[:]=0.;d.ctrl[ids]=command;mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);rs.append(physical(d,public));rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl.copy());rm.append(d.mocap_pos.copy());error=max(float(np.max(abs(d.qpos-expected['qpos'][tick]))),float(np.max(abs(d.qvel-expected['qvel'][tick]))),float(np.max(abs(d.ctrl[ids]-expected['controls'][tick]))),float(np.max(abs(d.mocap_pos-expected['mocap'][tick]))));max_replay=max(max_replay,error);assert error<=1e-8,'ORIGINAL_COMPONENT_NATIVE_REPLAY_MISMATCH'
  def replay_packet(expected):
   pp=poses(d.qpos[None,:])[0];packet=sensed_packet(pp[:2].astype(np.float32),pp[2],float(d.time),expected['packet']['step'],protocol,motion,initial_calls);assert packet==expected['packet'];base.update(packet);assert encode(base)==expected['domain']
  for tick,command in enumerate(scan_z['controls']):
   if tick>=8 and tick%8==0:
    candidate,gate=baseline_retained.command(d);assert np.array_equal(candidate,command);baseline_commands+=1
   checked_old_native(command,scan_a,tick,73+tick//8)
   if (tick+1)%8==0:
    replay_packet(scan_obs[(tick+1)//8-1])
    if tick==7:
     cache,evidence=prepare_retained_observation(original_scan_proof,d,predictor.command_map);baseline_retained=ReservedRecovery(predictor,mujoco,ids,root);baseline_retained.cache=cache;baseline_retained.executing=True
     for mode in ['qpos','qvel','time','ctrl','schedule']:
      import copy
      test=SimpleNamespace(qpos=d.qpos.copy(),qvel=d.qvel.copy(),ctrl=d.ctrl.copy(),time=float(d.time));proof=copy.deepcopy(original_scan_proof)
      if mode in ['qpos','qvel']:getattr(test,mode)[0]+=.001
      elif mode=='time':test.time+=.01
      elif mode=='ctrl':test.ctrl[ids[0]]+=.01
      else:proof['controls'][8][2]+=.001
      try:prepare_retained_observation(proof,test,predictor.command_map)
      except AssertionError:negative_cases+=1
      else:raise AssertionError('OBSERVATION_JOIN_NEGATIVE_CASE_ACCEPTED')
    else:baseline_retained.after_public(d)
  assert baseline_commands==40 and negative_cases==5 and not baseline_retained.executing and baseline_retained.cache is None
  dump('BASELINE_ADAPTER.json',dict(status='ORIGINAL_OBSERVATION_RETAINED_TAIL_EXACT',retained_public_commands=40,negative_join_cases_rejected=5,new_private_integrations=0,full_native_error=max_replay,real_state_writes=0))
  for tick,command in enumerate(advance_z['controls'][:32]):
   checked_old_native(command,advance_a,tick,114+tick//8)
   if (tick+1)%8==0:
    replay_packet(advance_obs[(tick+1)//8-1]);step=114+(tick+1)//8;snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[step]=snap;domains[step]=clone(base)
  assert replay==944
  np.savez_compressed(root/'ORIGINAL_944_NATIVE_REPLAY.npz',qpos=rq,qvel=rv,controls=rc,mocap=rm,safety=rs)
  def forecast(real,domain,target,label,horizon=328,brake=248,hold_first=False):
   initial_q=real.qpos.copy();initial_v=real.qvel.copy();last=real.ctrl[ids].copy();when=float(real.time);prefix_q=[];prefix_v=[];prefix_bounds=[]
   if hold_first:
    scratch=mujoco.MjData(predictor.model);mujoco.mj_resetData(predictor.model,scratch)
    for n in['qpos','qvel','act','qacc_warmstart']:getattr(scratch,n)[:]=getattr(real,n)
    scratch.time=when;scratch.ctrl[:]=0.;scratch.ctrl[ids]=last;mujoco.mj_forward(predictor.model,scratch);scratch.qacc_warmstart[:]=real.qacc_warmstart
    for _ in range(8):
     mujoco.mj_step(predictor.model,scratch);predictor.prediction_steps+=1;mujoco.mj_kinematics(predictor.model,scratch);prefix_q.append(scratch.qpos.copy());prefix_v.append(scratch.qvel.copy());prefix_bounds.append(predictor.self_geometry.actual(predictor.model,scratch))
    p=predictor.predict(scratch,target,ids,last,320,160);q=np.vstack([prefix_q,predictor.last_forecast_qpos]);v=np.vstack([prefix_v,predictor.last_forecast_qvel]);controls=np.vstack([np.repeat([last],8,axis=0),predictor.command_map.sequence(target,last,320,160)]);self_bounds=np.vstack([prefix_bounds,predictor.last_self_bounds]);brake=168
   else:
    p=predictor.predict(real,target,ids,last,horizon,brake);q=predictor.last_forecast_qpos.copy();v=predictor.last_forecast_qvel.copy();controls=predictor.command_map.sequence(target,last,horizon,brake);self_bounds=predictor.last_self_bounds.copy()
   p=poses(q);values=np.minimum(pose_values(static,p),domain.body_lower(p,when+np.arange(1,329)*.01));minimum=float(values.min());margin=float(containment_margin(self_bounds,bounds).min());speed=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]));progress=float(np.linalg.norm(initial_q[:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']));reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
   np.savez_compressed(root/(label+'_PRIVATE.npz'),initial_qpos=initial_q,initial_qvel=initial_v,initial_ctrl=last,initial_time=when,qpos=q,qvel=v,controls=controls,poses=p,self_bounds=self_bounds)
   return dict(label=label,target=target.tolist(),hold_first=hold_first,brake_after_native=brake,minimum_causal_clearance_m=minimum,minimum_causal_tick=int(np.argmin(values))+1,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,admissible=reason is None,reason=reason),q,v,controls
  def execute(real,domain,proof,old_retained=None):
   global validation,packets,max_validation
   record,q,v,controls=proof;assert record['admissible'];label=record['label'];updated=clone(domain);retained=None;adapter_commands=0;proof_data=np.load(root/(label+'_PRIVATE.npz'));scan_proof=certificate(record,proof_data,dict(center=None,time=domain.time,hidden_world_geometry_used=False,free_space_renewal=encode(domain)),round(real.time/.08))if record['hold_first']and abs(record['target'][2])==8. else None;actual_q=[];actual_v=[];actual_c=[];actual_m=[];safety=[];observations=[];error=0.;public_start=round(real.time/.08);before=poses(real.qpos[None,:])[0]
   for tick,command in enumerate(controls):
    if retained is not None and tick>=8 and tick%8==0:
     issued,gate=retained.command(real);assert np.array_equal(issued,command);adapter_commands+=1
    if tick%8==0:predictor.command_map.assert_first(command,real.ctrl[ids])
    real.ctrl[:]=0.;real.ctrl[ids]=command;mujoco.mj_step(m,real);validation+=1;motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real);safety.append(physical(real,public_start+tick//8));error=max(error,float(np.max(abs(real.qpos-q[tick]))),float(np.max(abs(real.qvel-v[tick]))));assert error<=1e-8,'FULL_NATIVE_BRANCH_MISMATCH';actual_q.append(real.qpos.copy());actual_v.append(real.qvel.copy());actual_c.append(real.ctrl[ids].copy());actual_m.append(real.mocap_pos.copy())
    if (tick+1)%8==0:
     pp=poses(real.qpos[None,:])[0];public=public_start+(tick+1)//8;packet=sensed_packet(pp[:2].astype(np.float32),pp[2],float(real.time),public,protocol,motion,initial_calls);updated.update(packet);future=updated.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in future]);excess=float(updated.point_lower(truth,future).max());assert excess<=1e-7,'NEW_SENSOR_DOMAIN_EXCLUDED_TRUE_ACTOR';observations.append(dict(packet=packet,domain=encode(updated),maximum_actual_coverage_excess_m=excess));packets+=1
     if scan_proof is not None:
      if tick==7:
       cache,evidence=prepare_retained_observation(scan_proof,real,predictor.command_map);retained=old_retained if old_retained is not None else ReservedRecovery(predictor,mujoco,ids,root);retained.cache=cache;retained.cursor=0;retained.expected=None;retained.expected_ctrl=None;retained.finish_pending=False;retained.executing=True
      else:retained.after_public(real)
   max_validation=max(max_validation,error);np.savez_compressed(root/(label+'_ACTUAL.npz'),qpos=actual_q,qvel=actual_v,controls=actual_c,mocap=actual_m,safety=safety)
   with gzip.open(root/(label+'_OBSERVATIONS.json.gz'),'wt')as stream:json.dump(observations,stream)
   actualp=poses(np.asarray(actual_q));now=actualp[-1];future=np.linspace(0,3.28,329);hold=np.repeat([now],329,axis=0);old_hold=float(np.minimum(pose_values(static,hold),domain.body_lower(hold,updated.time+future)).min());fresh_hold=float(np.minimum(pose_values(static,hold),updated.body_lower(hold,updated.time+future)).min())
   assert retained is None or(adapter_commands==40 and not retained.executing and retained.cache is None)
   record.update(adapter_retained_public_commands=adapter_commands,actual_native_steps=328,actual_state_error=error,actual_packets=41,actual_translation_m=float(np.linalg.norm(now[:2]-before[:2])),actual_yaw_sweep_rad=float(np.ptp(np.unwrap(np.r_[before[2],actualp[:,2]]))),actual_goal_progress_m=float(np.linalg.norm(before[:2]-protocol['goal_xy'])-np.linalg.norm(now[:2]-protocol['goal_xy'])),fresh_terminal_hold_geometry_m=fresh_hold,without_new_observation_terminal_hold_geometry_m=old_hold,actual_final_domain_sha256=encode(updated)['possible_bits_sha256'])
   return updated
  for step in[115,116,117,118]:
   for amplitude in[0.,8.,-8.]:
    mujoco.mj_copyData(d,m,snapshots[step]);domain=clone(domains[step]);branch_start_q=d.qpos.copy();old_contract_sha=sha(legacy/(oldadvance['label']+'_PRIVATE.npz'));old_retained=ReservedRecovery(predictor,mujoco,ids,root);old_retained.cache=dict(initial_qpos=advance_z['qpos'][7].copy(),initial_qvel=advance_z['qvel'][7].copy(),qpos=advance_z['qpos'][8:].copy(),qvel=advance_z['qvel'][8:].copy(),controls=advance_z['controls'][8:].copy(),start_time=float(advance_z['initial_time'])+.08);old_retained.cursor=(step-115)*8;old_retained.executing=True;old_retained.check_current_contract(d);old_cache=old_retained.cache;old_cursor=old_retained.cursor;old_cache_bytes=b''.join(old_cache[k].tobytes()for k in ['initial_qpos','initial_qvel','qpos','qvel','controls']);current_before=(d.qpos.copy(),d.qvel.copy(),d.ctrl.copy(),float(d.time));stem='S%03d_A%s'%(step,('P'if amplitude>=0 else'M')+str(int(abs(amplitude))));scan=forecast(d,domain,np.array([0.,0.,-amplitude,amplitude]),stem+'_SCAN',hold_first=True);branch=dict(step=step,amplitude=amplitude,scan=scan[0],successors=[],selected_successor=None,qualified=False,old_contract_sha256=old_contract_sha,old_contract_native_cursor=(step-114)*8,old_contract_remaining_native_ticks=328-(step-114)*8)
    assert np.array_equal(d.qpos,current_before[0])and np.array_equal(d.qvel,current_before[1])and np.array_equal(d.ctrl,current_before[2])and d.time==current_before[3]and old_contract_sha==sha(legacy/(oldadvance['label']+'_PRIVATE.npz')),'OBSERVATION_ADMISSION_MUTATED_RETAINED_ADVANCE'
    assert old_retained.cache is old_cache and old_retained.cursor==old_cursor and old_retained.executing and old_cache_bytes==b''.join(old_cache[k].tobytes()for k in ['initial_qpos','initial_qvel','qpos','qvel','controls']);old_retained.check_current_contract(d);branch['retained_object_unchanged_during_admission']=True
    if not scan[0]['admissible']:branch['outcome']='NEW_SCAN_NOT_CERTIFIED_OLD_CONTRACT_UNCHANGED'
    else:
     domain=execute(d,domain,scan,old_retained if amplitude!=0 else None);choices=[(0.,4.,4.),(0.,2.,6.),(0.,6.,2.),(-.42722137342572125,4.,4.),(.42722137342572125,4.,4.)];proofs=[]
     for j,(steer,left,right)in enumerate(choices):
      target=ReservedRecovery.target(steer,4.);target[2:]=[left,right];proof=forecast(d,domain,target,stem+'_ADVANCE_%d'%j);candidate=proof[0];candidate['index']=j
      if candidate['reason']is None and candidate['goal_progress_m']<.02:candidate.update(admissible=False,reason='GOAL_PROGRESS')
      branch['successors'].append(candidate);proofs.append(proof)
     eligible=[x for x in proofs if x[0]['admissible']]
     if eligible:
      selected=max(eligible,key=lambda x:(x[0]['goal_progress_m'],x[0]['minimum_causal_clearance_m'],-x[0]['index']));branch['selected_successor']=selected[0]['index'];domain=execute(d,domain,selected);branch['outcome']='OBSERVATION_AND_CONCRETE_ADVANCE_EXECUTED'
     else:branch['outcome']='NO_CONCRETE_SUCCESSOR'
    branch['total_goal_progress_m']=float(np.linalg.norm(branch_start_q[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy']));branch['qualified']=branch['selected_successor']is not None and branch['total_goal_progress_m']>=.02;records.append(branch);dump('BRANCHES.json',records);dump('ACTIVE.json',dict(status='RUNNING',completed_branches=len(records),replay=replay,private=predictor.prediction_steps,validation=validation,actual_packets=packets));print(json.dumps(branch),flush=True)
  contactlog.close();assert replay==944 and predictor.prediction_steps<=23616 and validation<=7872 and packets*8==validation and len(records)==12
  assert all(sha(repo/n)==h for n,h in freeze['files'].items())
  status='FIXED_EARLY_OBSERVATION_HANDOVER_DIAGNOSIS_COMPLETE';dump('RESULT.json',dict(status=status,branches=records,original_replay_steps=replay,private_integrations=predictor.prediction_steps,scene_validation_integrations=validation,actual_new_packets=packets,forecast_coverage_samples=packets*329,baseline_replayed_packets=45,baseline_adapter_retained_commands=40,negative_join_cases_rejected=5,maximum_original_replay_error=max_replay,maximum_candidate_state_error=max_validation,minimum_actual_native_clearance_m=min_actual,minimum_actual_self_margin_m=min_self,bad_contacts=bad,qualified_nonzero_branches=sum(x['qualified']and x['amplitude']!=0 for x in records),component_qualified=any(x['qualified']and x['amplitude']!=0 for x in records),new_navigation_samples=0,new_confirmation_samples=0,training_updates=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_steps=replay,private_integrations=None if predictor is None else predictor.prediction_steps,scene_validation_integrations=validation,actual_new_packets=packets,completed_branches=len(records),new_navigation_samples=0))
