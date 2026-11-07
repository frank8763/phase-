"""Two fixed causal-reference qualifications; all physics through run_phase."""
import copy,fcntl,gzip,importlib.util,json,os,signal,time,traceback
from helpers import *
import mujoco
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from geometry_predictor import RobotPredictor
from exact_footprint import build,pose_values
from reserved_recovery import ReservedRecovery
from joint_admission import admit_ranked
from motion_tracker import Tracker,install_time_gate
from motion_evaluator import check_forecast
from union_belief import future_cells
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import set_public_origin

own=Path(__file__).parent;root=repo/'runs/v825_goal_renewal_native_entry';root.mkdir(exist_ok=False)
started=float(os.environ['PHASE_RENEWAL_STARTED']);deadline=float(os.environ['PHASE_RENEWAL_DEADLINE'])
window=dict(started_unix=started,absolute_deadline_unix=deadline,round_closed=False,pid=os.getpid());dump(root/'ROUND_WINDOW.json',window)
signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('V824_FIXED_ABSOLUTE_WINDOW')));signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-time.time()))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
counts=dict(old_replay_native=0,private_native=0,component_native=0,component_repeat_native=0,new_navigation=0,new_confirmation=0)
records=[];status='RUNNING';predictor=None;physical_stream=None;private_samples=[];minimum=1e30;self_min=1e30;max_error=0.;bad=0
try:
 freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/p)==h for p,h in freeze.items())
 assert read(repo/'runs/goal_renewal_20261105/V825_PREPARATION.json')['status']=='FIXED_OLD_CONTROLLER_INTERFACE_ZERO_MODEL_PASS'
 lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config)
 noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap']
 traces,states,old_decisions,old_routes=fixed_inputs();set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={}
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as stream:
  for packet in map(json.loads,stream):
   if packet['step']>500:break
   assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise)),'RAW_PACKET_RECONSTRUCTION_FAILED'
   _,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles'])
   if packet['step']in(282,500):
    assert state==states[packet['step']],'ORIGINAL_CAUSAL_STATE_NOT_EXACT';trackers[packet['step']]=copy.deepcopy(tracker)
 dump(root/'SENSOR_CALIBRATION.json',dict(raw_packets=501,original_states_exact=[282,500],models=0,integrations=0))
 m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
 geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');bounds=np.asarray(protocol['footprint_bounds'])
 fixed={k:getattr(m,k).copy()for k in ['geom_pos','geom_size','geom_quat','geom_contype','geom_conaffinity']}
 static=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.asarray(protocol['known_rectangles']).reshape(-1,4),circles=np.asarray(protocol['known_circles']).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
 state_spec=mujoco.mjtState.mjSTATE_INTEGRATION
 def full(data):
  value=np.empty(mujoco.mj_stateSize(m,state_spec));mujoco.mj_getState(m,data,value,state_spec);return value
 def private(model,data):
  assert time.time()<deadline and predictor.prediction_steps<360400,'PRIVATE_BUDGET_OR_DEADLINE'
  mujoco.mj_step(model,data);mujoco.mj_kinematics(model,data)
  private_samples.append(dict(qpos=data.qpos.copy(),qvel=data.qvel.copy(),self_bounds=predictor.self_geometry.actual(model,data).copy()))
 predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,private);predictor.enable_differential=True;ids=predictor.command_map.ids
 assert predictor.proposer is not None and predictor.proposal_model_sha256==sha(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')
 physical_stream=gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','wt');context='OLD_REPLAY'
 def physical(data,public):
  global minimum,self_min,bad
  box=geometry.actual(m,data);margin=float(containment_margin(box,bounds))
  truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),.1]])})
  clearance=float(pose_values(truth,[pose(data.qpos)])[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin)
  contacts=[catalog.classify(c,int(round(float(data.time)/.01)),public,float(data.time))for c in data.contact]
  bad+=sum(c['contact_type']in['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts)
  physical_stream.write(json.dumps(dict(context=context,public=public,time=float(data.time),qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),ctrl=data.ctrl.tolist(),mocap=data.mocap_pos.tolist(),actual_bounds=box.tolist(),clearance_m=clearance,self_margin_m=margin,contacts=contacts))+'\n')
  assert clearance>=.15 and margin>=0 and bad==0 and all(np.array_equal(getattr(m,k),v)for k,v in fixed.items()),'PHYSICAL_SAFETY_OR_STATIC_MODEL_FAILURE'
  return [clearance,margin]
 def advance(data,command,public,account):
  assert time.time()<deadline,'ABSOLUTE_DEADLINE'
  before_q=data.qpos.copy();before_v=data.qvel.copy()
  if public is not None:predictor.command_map.assert_first(command,data.ctrl[ids])
  data.ctrl[:]=0.;data.ctrl[ids]=command
  assert np.array_equal(data.qpos,before_q)and np.array_equal(data.qvel,before_v),'ROOT_MUTATION_OUTSIDE_NATIVE'
  mujoco.mj_step(m,data);counts[account]+=1;motion.apply(m,data);mujoco.mj_kinematics(m,data);mujoco.mj_collision(m,data)
  assert np.array_equal(data.ctrl[ids],command)
  actual_public=int(round(float(data.time)/.01)-1)//8
  return physical(data,actual_public)
 snapshots={};replay=[]
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as stream:
  for i,line in enumerate(stream):
   if i>=4000:break
   old=json.loads(line);advance(d,np.asarray(old['actual_ctrl'])[ids],i//8 if i%8==0 else None,'old_replay_native')
   error=max(np.max(abs(d.qpos-old['qpos_full'])),np.max(abs(d.qvel-old['qvel_full'])),np.max(abs(d.ctrl-old['actual_ctrl'])),np.max(abs(d.mocap_pos-old['mocap_pos'])))
   max_error=max(max_error,float(error));assert error<=1e-8,'ORIGINAL_NATIVE_PREFIX_NOT_EXACT';replay.append(full(d))
   step=(i+1)//8
   if (i+1)%8==0 and step in(282,500):
    snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[step]=snap
 assert counts['old_replay_native']==4000;np.savez_compressed(root/'OLD_4000_NATIVE_REPLAY.npz',integration=replay)
 spec=importlib.util.spec_from_file_location('F',repo/'current/footprint_map_b70_v513.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
 for step in(282,500):
  folder=root/f'step{step:04d}';folder.mkdir();mujoco.mj_copyData(d,m,snapshots[step]);initial=full(d).copy();env=environment(m,d);current=pose(d.qpos);last=d.ctrl[ids].copy();state=states[step]
  world=copy.deepcopy(read(cell/'planning_0265.json')['causal_input']);world['rectangles']=[*protocol['known_rectangles'],state['current_outer_rectangle']]
  field=build(F,world);field.nominal_static_geometry=SimpleNamespace(**static.__dict__);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles'])
  # Native re-evaluation of exactly the saved old select call, not new tuning.
  old=old_decisions[step];cursor=[0];original_predict=predictor.predict;calibration_error=[0.]
  def calibration_predict(*args,**kwargs):
   trajectory=original_predict(*args,**kwargs);item=old['candidates'][cursor[0]];cursor[0]+=1;z=np.load(cell/'nominal_forecasts'/item['nominal_saved_forecast'])
   error=float(np.max(abs(trajectory-z['poses'])));calibration_error[0]=max(calibration_error[0],error);assert error<=1e-8,'OLD_240_NATIVE_FORECAST_NOT_EXACT'
   return trajectory
  predictor.predict=calibration_predict;f=old['candidates'][0]['features']
  old_command,old_gate=predictor.select(env,field,np.asarray(old_routes[step]['reference_path']),old_routes[step]['index'],current,f[10],f[11],last)
  old_best=max((x for x in old['candidates']if x['reason']is None),key=lambda x:x['score'])
  assert np.max(abs(old_command-old_best['first_command']))<=1e-8 and abs(old_gate['score']-old['summary']['score'])<=1e-8
  predictor.predict=original_predict
  reference,source=new_reference(step);assert np.max(abs(reference[0,:3]-current))<=1e-8
  steer,speed=controls_for_reference(reference,current,env,np.asarray(protocol['goal_xy']))
  predictor.nominal_directory=folder/'NEW_NOMINAL';predictor.nominal_directory.mkdir()
  proposal,gate=predictor.select(env,field,reference,0,current,steer,speed,last)
  dump(folder/'NEW_NOMINAL.json',dict(gate=gate,candidates=predictor.last_diagnostics,reference_source=str(source.relative_to(repo)),reference=reference,current=current))
  del predictor.nominal_directory
  reserved=ReservedRecovery(predictor,mujoco,ids,folder);private_samples.clear()
  proposal,gate,summary=admit_ranked(reserved,predictor,d,proposal,gate,field,state,step,reference,0,folder)
  assert np.array_equal(full(d),initial),'PREDICTION_MUTATED_REAL_STATE'
  assert predictor.prediction_steps<=360400,'PRIVATE_LIMIT'
  record=dict(step=step,old_nominal_forecasts=cursor[0],old_nominal_maximum_pose_error=calibration_error[0],old_first_command_and_score_match=True,
   new_reference=str(source.relative_to(repo)),joint_summary=summary,new_gate=gate,qualified=False,component_executed=False)
  if summary is not None:
   cache=reserved.cache;prefix_samples=private_samples[-8:];assert len(prefix_samples)==8
   q=np.vstack([[x['qpos']for x in prefix_samples],cache['qpos']]);v=np.vstack([[x['qvel']for x in prefix_samples],cache['qvel']]);p=poses(q)
   controls=np.vstack([np.repeat([proposal],8,axis=0),cache['controls']]);values=field.trajectory_values(p,.01)
   assert len(q)==328 and values.min()>=.155
   prefix_gain=float(np.linalg.norm(current[:2]-protocol['goal_xy'])-np.linalg.norm(q[7,:2]-protocol['goal_xy']))
   whole_gain=float(np.linalg.norm(current[:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']))
   record.update(prefix8_target_progress_m=prefix_gain,complete328_target_progress_m=whole_gain,recovery_kind=cache['recovery_kind'],minimum_causal_clearance_m=float(values.min()))
   # Full self bounds of the SELECTED cached tail, not the final tried candidate.
   probe=mujoco.MjData(predictor.model);selected_bounds=[]
   for qi,vi in zip(q,v):
    probe.qpos[:]=qi;probe.qvel[:]=vi;mujoco.mj_forward(predictor.model,probe);selected_bounds.append(predictor.self_geometry.actual(predictor.model,probe))
   selected_bounds=np.asarray(selected_bounds);assert containment_margin(selected_bounds,bounds).min()>=.002 and np.linalg.norm(v[-1,:2])<=.025
   np.savez_compressed(folder/'CERTIFICATE.npz',qpos=q,qvel=v,controls=controls,poses=p,self_bounds=selected_bounds,initial=initial,initial_qpos=d.qpos.copy(),initial_qvel=d.qvel.copy(),initial_ctrl=d.ctrl.copy(),causal_values=values,forecast_state=json.dumps(state),reference=reference)
   if prefix_gain>0:
    completed=[]
    for repeat in(False,True):
     context=f'S{step}_'+('REPEAT'if repeat else'ACTUAL');real=mujoco.MjData(m);mujoco.mj_copyData(real,m,snapshots[step]);local=copy.deepcopy(trackers[step]);actual=[];safety=[];observations=[]
     for tick,command in enumerate(controls):
      safety.append(advance(real,command,step+tick//8 if tick%8==0 else None,'component_repeat_native'if repeat else'component_native'))
      error=max(np.max(abs(real.qpos-q[tick])),np.max(abs(real.qvel-v[tick])),np.max(abs(real.ctrl[ids]-controls[tick])))
      max_error=max(max_error,float(error));assert error<=1e-8,'NEW_PREDICTION_SCENE_STATE_MISMATCH'
      actual.append(full(real))
      if tick%8==7:
       public=step+(tick+1)//8;xy,yaw=sensor_pose(real.qpos);packet=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,noise)
       _,observed=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);coverage=check_forecast(config,observed);assert coverage['passed']
       times=np.arange(657)*.01;lo,hi=future_cells(observed['outer_state_cells'],times);truth=np.asarray([motion.xy(observed['time']+t)for t in times]);excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7
       assert (np.linalg.norm(truth-truth[0],axis=1)-.08*times).max()<=1e-7
       observations.append(dict(packet=packet,state=observed,execution_coverage=coverage,planning_excess_m=excess))
     completed.append(dict(integration=np.asarray(actual),observations=observations))
     label='REPEAT'if repeat else'ACTUAL';np.savez_compressed(folder/(label+'.npz'),integration=actual,safety=safety)
     with gzip.open(folder/(label+'_OBSERVATIONS.json.gz'),'wt')as stream:json.dump(observations,stream)
    repeat_error=float(np.max(abs(completed[0]['integration']-completed[1]['integration'])));assert repeat_error<=1e-8 and completed[0]['observations']==completed[1]['observations']
    record.update(qualified=True,component_executed=True,full_integration_repeat_error=repeat_error,actual_and_repeat_packets_exact=True)
  records.append(record);dump(root/'RESULTS.json',records);print(json.dumps({k:v for k,v in record.items()if k not in['new_gate','joint_summary']}),flush=True)
 assert all(sha(repo/p)==h for p,h in freeze.items()),'FROZEN_SOURCE_OR_INPUT_CHANGED'
 status='GOAL_REFERENCE_COMPONENTS_EVALUATED';dump(root/'RESULT.json',dict(status=status,records=records,counts={**counts,'private_native':predictor.prediction_steps},primary282_passed=records[0]['qualified'],minimum_actual_clearance_m=minimum,minimum_self_margin_m=self_min,maximum_native_state_ctrl_error=max_error,bad_contacts=bad,model_initialization_count=None,new_global_navigation=0,full_global_dynamic_passed=False))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 if physical_stream is not None:physical_stream.close()
 signal.alarm(0);counts['private_native']=None if predictor is None else predictor.prediction_steps
 window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',window);dump(root/'COMPLETION.json',dict(status=status,counts=counts,completed_inputs=len(records)))
