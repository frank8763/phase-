"""Fixed coupled sensing/progress schedules with causal rolling full contracts."""
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
from retained_coupled import prepare_retained
from selection import initial_state,select
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=repo/'runs/v767_certified_progress_release';root.mkdir(exist_ok=False)
def dump(n,v):(root/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def clone(domain):
 copy=RecursiveDomain(domain.origin);copy.time=domain.time;copy.possible=domain.possible.copy();copy.distance=domain.distance.copy();copy.last=dict(domain.last);return copy
started=float(os.environ['PHASE_V767_STARTED']);deadline=float(os.environ['PHASE_V767_DEADLINE']);assert abs(deadline-started-1200)<1e-6 and time.time()<deadline
window=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=1200,round_closed=False,pid=os.getpid());dump('ROUND_WINDOW.json',window);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def timeout(*_):raise TimeoutError('V767_FIXED_1200S_ABSOLUTE_STOP')
signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,deadline-time.time())
actual_context='BASELINE';replay=validation=packets=0;predictor=None;records=[];status='RUNNING';min_actual=min_self=float('inf');max_replay=max_validation=0.;bad=0
try:
 freeze=read(own/'INPUT_FREEZE.json');assert all(sha(repo/n)==h for n,h in freeze['files'].items())
 with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  pair=repo/'runs/v735_scan_differential_navigation/main01/paired';cell=pair/'geometry_memory';protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);initial_calls=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];rows=[json.loads(s)for s in(cell/'v648_execution.jsonl').read_text().splitlines()];beliefs={r['step']:r for r in map(json.loads,(cell/'motion_estimate.jsonl').read_text().splitlines())}
  with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:old_packets=[json.loads(s)for s in stream]
  for packet in old_packets:
   regenerated=sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,initial_calls)
   assert packet_equal(packet,regenerated),'ORIGINAL_SENSOR_BACKEND_NOT_EXACT'
  dump('SENSOR_CALIBRATION.json',dict(status='ALL_ORIGINAL_177_NOISY_PACKETS_EXACT',packets=len(old_packets),model_initializations=0,new_integrations=0))
  assert len(old_packets)==177
  m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d);geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds']);fixed_geom=m.geom_pos.copy()
  static=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,mujoco.mj_step);ids=predictor.command_map.ids;contactlog=gzip.open(root/'ACTUAL_CONTACTS.jsonl.gz','wt')
  def physical(data,public):
   global min_actual,min_self,bad
   box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),config['radius_m']]])});clearance=float(pose_values(truth,poses(data.qpos[None,:]))[0]);contacts=[catalog.classify(c,replay+validation,public,float(data.time))for c in data.contact];bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts);contactlog.write(json.dumps(dict(account_step=replay+validation,time=float(data.time),public=public,context=actual_context,qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),controls=data.ctrl[ids].tolist(),mocap=data.mocap_pos.tolist(),safety=[clearance,margin,*box.tolist()],contacts=contacts))+'\n');min_actual=min(min_actual,clearance);min_self=min(min_self,margin)
   assert clearance>=.15 and margin>=0 and bad==0 and np.array_equal(m.geom_pos,fixed_geom),'ACTUAL_SAFETY_OR_STATIC_MODEL_EXCEPTION';return [clearance,margin,*box.tolist()]
  rq=[];rv=[];rc=[];rm=[];rs=[]
  for row in rows[:32]:
   d.ctrl[:]=row['ctrl']
   for _ in range(8):
    mujoco.mj_step(m,d);replay+=1;motion.apply(m,d);mujoco.mj_kinematics(m,d);mujoco.mj_collision(m,d);rs.append(physical(d,row['step']));rq.append(d.qpos.copy());rv.append(d.qvel.copy());rc.append(d.ctrl[ids].copy());rm.append(d.mocap_pos.copy())
   max_replay=max(max_replay,float(np.max(abs(d.qpos-row['qpos_full']))),float(np.max(abs(d.qvel-row['qvel_full']))),float(np.max(abs(d.mocap_pos-row['mocap_pos']))));assert max_replay<=1e-8
  checkpoint=mujoco.MjData(m);mujoco.mj_copyData(checkpoint,m,d);base=clone(decode(beliefs[32]['free_space_renewal']))
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
   np.savez_compressed(root/(label+'_PRIVATE.npz'),initial_act=real.act.copy(),initial_warmstart=real.qacc_warmstart.copy(),initial_full_ctrl=real.ctrl.copy(),initial_mocap_pos=real.mocap_pos.copy(),initial_mocap_quat=real.mocap_quat.copy(),initial_qpos=initial_q,initial_qvel=initial_v,initial_ctrl=last,initial_time=when,qpos=q,qvel=v,controls=controls,poses=p,self_bounds=self_bounds)
   return dict(label=label,target=target.tolist(),hold_first=hold_first,brake_after_native=brake,minimum_causal_clearance_m=minimum,minimum_causal_tick=int(np.argmin(values))+1,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,admissible=reason is None,reason=reason),q,v,controls
  def make_proof(record,z,domain):
   return dict(schema='V749_COUPLED_01',created_step=round(float(z['initial_time'])/.08),start_time=float(z['initial_time']),prefix_command=z['initial_ctrl'].tolist(),target=record['target'],controls=z['controls'].tolist(),qpos=z['qpos'].tolist(),qvel=z['qvel'].tolist(),poses=z['poses'].tolist(),forecast_state=dict(center=None,time=domain.time,hidden_world_geometry_used=False,free_space_renewal=encode(domain)),minimum_causal_predicted_clearance_m=record['minimum_causal_clearance_m'],minimum_predicted_self_domain_margin_m=record['self_margin_m'],terminal_speed_m_s=record['terminal_speed_m_s'],terminal_angular_speed_rad_s=record['terminal_angular_speed_rad_s'],total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False)
  def perform(real,command,q,v,public,store,replaying=False):
   global replay,validation,max_replay,max_validation
   predictor.command_map.assert_first(command,real.ctrl[ids]);error=0.
   for j in range(8):
    real.ctrl[:]=0.;real.ctrl[ids]=command;mujoco.mj_step(m,real)
    if replaying:replay+=1
    else:validation+=1
    motion.apply(m,real);mujoco.mj_kinematics(m,real);mujoco.mj_collision(m,real);safety=physical(real,public);error=max(error,float(np.max(abs(real.qpos-q[j]))),float(np.max(abs(real.qvel-v[j]))));assert error<=1e-8,'FULL_NATIVE_EXECUTION_MISMATCH'
    for key,value in [('qpos',real.qpos),('qvel',real.qvel),('controls',real.ctrl[ids]),('mocap',real.mocap_pos),('safety',safety)]:store[key].append(np.asarray(value).copy())
   if replaying:max_replay=max(max_replay,error)
   else:max_validation=max(max_validation,error)
   return error
  def observe(real,domain,public):
   xy,yaw=sensor_pose(real.qpos);packet=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,initial_calls);domain.update(packet);times=domain.time+np.linspace(0,3.28,329);truth=np.asarray([motion.xy(t)for t in times]);excess=float(domain.point_lower(truth,times).max());assert excess<=1e-7,'CAUSAL_DOMAIN_TRUE_ACTOR_EXCLUSION';return dict(packet=packet,domain=encode(domain),maximum_actual_coverage_excess_m=excess)
  calibration=forecast(d,base,np.array([0.,0.,8.,-8.]),'CALIBRATION',hold_first=True);cr,cq,cv,cc=calibration;assert cr['admissible'];cz=np.load(root/'CALIBRATION_PRIVATE.npz')
  with gzip.open(cell/'observation_scan_certificate.json.gz','rt')as f:original_scan=json.load(f)
  assert max(np.max(abs(cq-original_scan['qpos'])),np.max(abs(cv-original_scan['qvel'])),np.max(abs(cc-original_scan['controls'])))<=1e-8,'OLD_SCAN_PREDICTION_NOT_IDENTICAL'
  proof=make_proof(cr,cz,base);controller=ReservedRecovery(predictor,mujoco,ids,root);store={k:[]for k in ['qpos','qvel','controls','mocap','safety']};calobs=[];negative=[];bd=clone(base)
  for public in range(41):
   tick=public*8
   if public==0:command=cc[0]
   else:command,gate=controller.command(d);assert np.array_equal(command,cc[tick])
   perform(d,command,cq[tick:tick+8],cv[tick:tick+8],33+public,store,True);obs=observe(d,bd,33+public);assert packet_equal(obs['packet'],old_packets[33+public])and obs['domain']==beliefs[33+public]['free_space_renewal'];calobs.append(obs)
   if public==0:
    cache,evidence=prepare_retained(proof,d,predictor.command_map);controller.cache=cache;controller.executing=True
    import copy
    for mode in ['qpos','qvel','time','ctrl','schedule']:
     test=SimpleNamespace(qpos=d.qpos.copy(),qvel=d.qvel.copy(),ctrl=d.ctrl.copy(),time=float(d.time));changed=copy.deepcopy(proof)
     if mode in ['qpos','qvel']:getattr(test,mode)[0]+=.001
     elif mode=='time':test.time+=.01
     elif mode=='ctrl':test.ctrl[ids[0]]+=.01
     else:changed['controls'][8][2]+=.001
     try:prepare_retained(changed,test,predictor.command_map)
     except AssertionError:negative.append(mode)
     else:raise AssertionError('NEGATIVE_JOIN_ACCEPTED')
   else:controller.after_public(d)
  assert not controller.executing and len(negative)==5 and replay==584
  np.savez_compressed(root/'CALIBRATION_ACTUAL.npz',**store);np.savez_compressed(root/'ORIGINAL_256_NATIVE_REPLAY.npz',qpos=rq,qvel=rv,controls=rc,mocap=rm,safety=rs)
  with gzip.open(root/'CALIBRATION_OBSERVATIONS.json.gz','wt')as f:json.dump(calobs,f)
  dump('CALIBRATION.json',dict(status='ORIGINAL_FULL_SCAN_AND_RETAINED_COMMANDS_EXACT',record=cr,original_replay=584,negative_cases=negative,old_actual_packets_exact=41,new_private=328,full_native_error=max_replay))
  def branch(name,profile,repeat_of=None):
   global validation,packets,actual_context
   actual_context=name
   mujoco.mj_copyData(d,m,checkpoint);domain=clone(base);controller=ReservedRecovery(predictor,mujoco,ids,root);store={k:[]for k in ['qpos','qvel','controls','mocap','safety']};observations=[];trace=[];decisions=[];fallback=False;cursor=0;progress384=None;initial=d.qpos.copy();before_private=predictor.prediction_steps;current_label=None;outcome='IN_PROGRESS';selector_state=initial_state();first_release=None;first_release_goal_distance=None;progress_after_release=None
   def execute_public(command,expected_q,expected_v,label,full_index,mode):
    global packets
    public=32+cursor+1;error=perform(d,command,expected_q,expected_v,public,store);obs=observe(d,domain,public);observations.append(obs);packets+=1;trace.append(dict(local_public=cursor+1,public=public,certificate=label,full_native_index=full_index,mode=mode,command=command.tolist(),full_native_error=error))
   while cursor<384 or controller.executing:
    assert cursor<425,'FIXED_PUBLIC_BUDGET_EXCEEDED'
    if cursor<384 and cursor%4==0 and not fallback:
     phase=cursor//24;candidates=[]
     old_cache=controller.cache;old_cursor=controller.cursor;real_before=([getattr(d,k).copy()for k in ['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat']],float(d.time));old_bytes=None if old_cache is None else b''.join(old_cache[k].tobytes()for k in ['qpos','qvel','controls'])
     if old_cache is not None:controller.check_current_contract(d)
     for action_index,(mean,diff)in enumerate((mean,diff)for mean in[0,1,2]for diff in[-6,-3,0,3,6]):
      target=np.array([0.,0.,mean+diff,mean-diff]);label=name+'_P%03d_A%02d'%(cursor,action_index);candidate,q,v,controls=forecast(d,domain,target,label,hold_first=True);candidate.update(action_index=action_index);candidates.append(candidate)
     ranked=sorted([x for x in candidates if x['admissible']],key=lambda x:(-x['goal_progress_m'],-x['minimum_causal_clearance_m'],x['action_index']))
     unknown_hold=float(domain.body_lower(np.repeat(poses(d.qpos[None,:]),329,axis=0),domain.time+np.linspace(0,3.28,329)).min());selector_before=dict(selector_state);choice,selector_state,selection_evidence=select(candidates,cursor,float(poses(d.qpos[None,:])[0,2]),unknown_hold,selector_state)
     if first_release is None and 'ACTUAL_SWEEP_AND_INFORMATION_RENEWED'in selection_evidence['events']:
      first_release=cursor;first_release_goal_distance=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy']))
     record=dict(candidates[choice]if choice is not None else candidates[0]);record.update(candidates=candidates,ranking=[x['action_index']for x in ranked],selector_before=selector_before,selector_after=dict(selector_state),selection_evidence=selection_evidence,unknown_hold_m=unknown_hold,selected_index=choice);label=record['label'];selected=np.load(root/(label+'_PRIVATE.npz'));q=selected['qpos'];v=selected['qvel'];controls=selected['controls']
     assert controller.cache is old_cache and controller.cursor==old_cursor and all(np.array_equal(getattr(d,k),val)for k,val in zip(['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat'],real_before[0]))and d.time==real_before[1]and(old_cache is None or old_bytes==b''.join(old_cache[k].tobytes()for k in ['qpos','qvel','controls'])),'CANDIDATE_MUTATED_OLD_CONTRACT_OR_REAL_STATE'
     record.update(local_public=cursor,phase=phase,old_cache_unchanged=True,old_cache_present=old_cache is not None,old_native_cursor=old_cursor,domain_sha256=encode(domain)['possible_bits_sha256']);decisions.append(record)
     if record['admissible']:
      z=np.load(root/(label+'_PRIVATE.npz'));proof=make_proof(record,z,domain);execute_public(controls[0],q[:8],v[:8],label,0,'NEW_CERTIFIED_HELD_PREFIX');cache,evidence=prepare_retained(proof,d,predictor.command_map);controller.cache=cache;controller.cursor=0;controller.expected=None;controller.expected_ctrl=None;controller.finish_pending=False;controller.executing=True;current_label=label;cursor+=1
      if cursor==384:progress384=float(np.linalg.norm(initial[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy']))
      continue
     fallback=True;outcome='NEW_CERTIFICATE_REJECTED_OLD_TAIL_RETAINED'
     if old_cache is None:break
     controller.check_current_contract(d)
    if not controller.executing:break
    i=controller.cursor;cache=controller.cache;command,gate=controller.command(d);execute_public(command,cache['qpos'][i:i+8],cache['qvel'][i:i+8],current_label,i+8,'RETAINED_CERTIFIED_TAIL');controller.after_public(d);cursor+=1
    if cursor==384:progress384=float(np.linalg.norm(initial[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy']))
   if first_release is not None:progress_after_release=float(first_release_goal_distance-np.linalg.norm((store['qpos'][384*8-1]if len(store['qpos'])>=384*8 else d.qpos)[:2]-protocol['goal_xy']))
   stopped=bool(np.linalg.norm(d.qvel[:2])<=.025 and np.linalg.norm(d.qvel[3:6])<=.025)
   qualified=bool(not fallback and len(decisions)==96 and all(x['admissible']for x in decisions)and progress384 is not None and progress384>=.30 and first_release is not None and progress_after_release>=1.0 and not controller.executing and stopped)
   if not fallback:outcome='FIXED_384_STEP_CYCLE_AND_STOP_COMPLETE'if qualified else'FEEDBACK_INSUFFICIENT_PROGRESS_OR_TERMINAL'
   summary=dict(name=name,profile=profile,repeat_of=repeat_of,outcome=outcome,qualified=qualified,public_steps=cursor,scheduled_public_completed=(next((x['local_public']for x in decisions if not x['admissible']),min(cursor,384))),planned_refreshes=96,attempted_refreshes=len(decisions),accepted_refreshes=sum(x['admissible']for x in decisions),actual_native=cursor*8,actual_packets=len(observations),private_integrations=predictor.prediction_steps-before_private,goal_progress_at_384_m=progress384,final_goal_progress_m=float(np.linalg.norm(initial[:2]-protocol['goal_xy'])-np.linalg.norm(d.qpos[:2]-protocol['goal_xy'])),terminal_stopped=stopped,terminal_speed_m_s=float(np.linalg.norm(d.qvel[:2])),terminal_angular_speed_rad_s=float(np.linalg.norm(d.qvel[3:6])),terminal_cache_complete=not controller.executing,first_observation_release_public=first_release,goal_progress_after_release_m=progress_after_release,decisions=decisions)
   reference=repo/'runs/v764_observation_progress_cycle';ref=np.load(reference/'FEEDBACK_MAIN_ACTUAL.npz');assert cursor>=64,'NEW_RELEASE_PREFIX_ENDED_BEFORE_ORIGINAL64'
   for key in store:assert np.max(abs(np.asarray(store[key])[:64*8]-ref[key][:64*8]))<=1e-8,'ORIGINAL96_ACTUAL_PREFIX_CHANGED'
   with gzip.open(reference/'FEEDBACK_MAIN_OBSERVATIONS.json.gz','rt')as f:assert observations[:64]==json.load(f)[:64]
   old_decisions=read(reference/'FEEDBACK_MAIN_SUMMARY.json')['decisions'][:16];assert json.loads(json.dumps(decisions[:16]).replace(name,'FEEDBACK_MAIN'))==old_decisions
   for dec in old_decisions:
    for ca in dec['candidates']:
     origin=reference/(ca['label']+'_PRIVATE.npz');current=root/(ca['label'].replace('FEEDBACK_MAIN',name)+'_PRIVATE.npz');oldz=np.load(origin);newz=np.load(current);assert all(np.array_equal(oldz[key],newz[key])for key in oldz.files),'ORIGINAL96_CANDIDATE_PREDICTION_CHANGED'
   np.savez_compressed(root/(name+'_ACTUAL.npz'),**store)
   with gzip.open(root/(name+'_OBSERVATIONS.json.gz'),'wt')as f:json.dump(observations,f)
   dump(name+'_TRACE.json',trace);dump(name+'_SUMMARY.json',summary)
   if repeat_of is not None:
    other=np.load(root/(repeat_of+'_ACTUAL.npz'));assert all(np.asarray(store[k]).shape==other[k].shape for k in store);error=max(float(np.max(abs(np.asarray(store[k])-other[k])))for k in store);old=read(root/(repeat_of+'_SUMMARY.json'));assert error<=1e-8 and summary['qualified']==old['qualified']and summary['public_steps']==old['public_steps']and observations==read_gzip(root/(repeat_of+'_OBSERVATIONS.json.gz')),'FULL_REPEAT_MISMATCH';summary['maximum_repeat_error']=error
   dump(name+'_SUMMARY.json',summary);records.append(summary);dump('BRANCHES.json',records);dump('ACTIVE.json',dict(completed=len(records),replay=replay,private=predictor.prediction_steps,actual=validation,packets=packets));print(json.dumps({k:v for k,v in summary.items()if k!='decisions'}),flush=True)
   return summary
  def read_gzip(path):
   with gzip.open(path,'rt')as f:return json.load(f)
  for profile in ['FEEDBACK']:
   result=branch(profile+'_MAIN',profile)
   if result['qualified']:branch(profile+'_REPEAT',profile,profile+'_MAIN')
  contactlog.close();assert replay==584 and validation<=6800 and packets<=850 and packets*8==validation and predictor.prediction_steps<=944968
  assert all(sha(repo/n)==h for n,h in freeze['files'].items())
  qualified=[p for p in ['FEEDBACK']if any(x['profile']==p and x['repeat_of']is not None and x['qualified']for x in records)]
  status='CERTIFIED_PROGRESS_RELEASE_EXECUTION_COMPLETE';dump('RESULT.json',dict(status=status,branches=records,qualified_profiles=qualified,component_qualified=bool(qualified),original_replay_native=replay,private_integrations=predictor.prediction_steps,actual_validation_native=validation,actual_new_packets=packets,old_replayed_packets=41,forecast_coverage_samples=packets*329,minimum_actual_clearance_m=min_actual,minimum_actual_self_margin_m=min_self,bad_contacts=bad,maximum_replay_error=max_replay,maximum_validation_error=max_validation,new_complete_navigation=0,new_confirmation=0,training_updates=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump('ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 signal.alarm(0)
 if 'contactlog'in globals()and not contactlog.closed:contactlog.close()
 window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump('ROUND_WINDOW.json',window);dump('COMPLETION.json',dict(status=status,round_closed=True,original_replay_native=replay,private_integrations=None if predictor is None else predictor.prediction_steps,actual_validation_native=validation,actual_new_packets=packets,completed_records=len(records),new_navigation=0))
