"""Two preregistered native saved-state branches, no new global navigation."""
import copy,fcntl,gzip,os,signal,time,traceback
from helpers import *
import mujoco
from dynamic_scene import Motion
from dynamic_contact import GeometryCatalog
from self_geometry import SelfGeometry,containment_margin
from geometry_predictor import RobotPredictor
from reserved_recovery import ReservedRecovery
from exact_footprint import pose_values
from motion_tracker import Tracker,install_time_gate
from independent_norm import static_field
from motion_evaluator import check_forecast
from union_belief import future_cells
from sensor_model import packet as sensed_packet
from packet_contract import packet_equal
from canonical_sensor_pose import sensor_pose
from unseen_prior import set_public_origin
assert not root.exists();root.mkdir()
started=float(os.environ['PHASE_ESCAPE_STARTED']);deadline=float(os.environ['PHASE_ESCAPE_DEADLINE']);window=dict(started_unix=started,absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False)
dump(root/'ROUND_WINDOW.json',window);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FIXED_COMPONENT_ABSOLUTE_DEADLINE')));signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-time.time()))
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});counts=dict(old_replay_native=0,private_native=None,component_native=0,component_repeat_native=0,new_navigation=0,new_confirmation=0)
records=[];status='RUNNING';predictor=None;stream=None;minimum=1e30;self_min=1e30;max_error=0.;bad=0
try:
 freeze=read(own/'INPUT_FREEZE.json')['files'];assert all(sha(repo/n)==h for n,h in freeze.items())
 lock=(repo/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 protocol=read(pair/'STATIC_PROTOCOL.json');config=read(pair/'DYNAMIC_PROTOCOL.json');motion=Motion(config);noise=read(pair/'INITIALIZATION_PROVENANCE.json')['noise_call_state_after_bootstrap'];entries=read(own/'FIXED_INPUTS.json');states={e['step']:e['state']for e in entries};bounds=np.asarray(protocol['footprint_bounds']);static=static_field(protocol)
 set_public_origin(protocol['start_qpos'][:2]);tracker=Tracker();trackers={};packet_count=0
 with gzip.open(cell/'sensor_packets.jsonl.gz','rt')as f:
  for packet in map(json.loads,f):
   if packet['step']>295:break
   assert packet_equal(packet,sensed_packet(packet['xy'],packet['yaw'],packet['time'],packet['step'],protocol,motion,noise))
   _,state=tracker.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);packet_count+=1
   if packet['step']in states:assert state==states[packet['step']],'FIXED_CAUSAL_STATE_NOT_EXACT';trackers[packet['step']]=copy.deepcopy(tracker)
 assert packet_count==296;dump(root/'SENSOR_CALIBRATION.json',dict(packets=packet_count,states_exact=[295],models=0,integrations=0))
 m=mujoco.MjModel.from_binary_path(str(pair/'scene_model.mjb'));d=mujoco.MjData(m);d.qpos[:]=protocol['start_qpos'];motion.apply(m,d);mujoco.mj_forward(m,d)
 geometry=SelfGeometry(m,mujoco);catalog=GeometryCatalog(m,mujoco,pair/'assets/isolated_indoor.xml');fixed={k:getattr(m,k).copy()for k in ['geom_pos','geom_size','geom_quat','geom_contype','geom_conaffinity']};spec=mujoco.mjtState.mjSTATE_INTEGRATION
 def full(data):
  out=np.empty(mujoco.mj_stateSize(m,spec));mujoco.mj_getState(m,data,out,spec);return out
 samples=[]
 def private(model,data):
  assert time.time()<deadline and predictor.prediction_steps<200000
  mujoco.mj_step(model,data);mujoco.mj_kinematics(model,data);
  if len(samples)<8:samples.append(dict(qpos=data.qpos.copy(),qvel=data.qvel.copy()))
 predictor=RobotPredictor(SimpleNamespace(model=m,data=d),repo/'runtime/mk-mini',mujoco,private);ids=predictor.command_map.ids
 assert predictor.proposer is not None and predictor.proposal_model_sha256==sha(repo/'runs/v690_visible_eight_meter/training_8m/proposer.json')
 original_predict=predictor.predict
 def capped_predict(*args,**kwargs):
  assert time.time()<deadline and predictor.prediction_steps+kwargs.get('horizon',240)<=200000,'PRIVATE_CAP'
  return original_predict(*args,**kwargs)
 predictor.predict=capped_predict
 context='OLD_REPLAY';stream=gzip.open(root/'ACTUAL_NATIVE.jsonl.gz','wt')
 def advance(data,command,public,account):
  global minimum,self_min,bad
  assert time.time()<deadline
  if public is not None:predictor.command_map.assert_first(command,data.ctrl[ids])
  before=data.qpos.copy();data.ctrl[:]=0.;data.ctrl[ids]=command;assert np.array_equal(before,data.qpos)
  mujoco.mj_step(m,data);counts[account]+=1;motion.apply(m,data);mujoco.mj_kinematics(m,data);mujoco.mj_collision(m,data)
  box=geometry.actual(m,data);margin=float(containment_margin(box,bounds));truth=SimpleNamespace(**{**static.__dict__,'half':(box[2:]-box[:2])/2,'center_local':(box[2:]+box[:2])/2,'circles':np.asarray([*protocol['known_circles'],[*motion.xy(data.time),.1]])})
  clearance=float(pose_values(truth,poses(data.qpos))[0]);minimum=min(minimum,clearance);self_min=min(self_min,margin);actual_public=(int(round(data.time/.01))-1)//8
  contacts=[catalog.classify(c,int(round(data.time/.01)),actual_public,float(data.time))for c in data.contact];bad+=sum(c['contact_type']in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact']for c in contacts)
  stream.write(json.dumps(dict(context=context,public=actual_public,time=float(data.time),qpos=data.qpos.tolist(),qvel=data.qvel.tolist(),ctrl=data.ctrl.tolist(),mocap=data.mocap_pos.tolist(),actual_bounds=box.tolist(),clearance_m=clearance,self_margin_m=margin,contacts=contacts))+'\n')
  assert clearance>=.15 and margin>=0 and bad==0 and all(np.array_equal(getattr(m,k),v)for k,v in fixed.items()),'ACTUAL_SAFETY_OR_MODEL_FAILURE'
  assert np.array_equal(data.ctrl[ids],command)
  return [clearance,margin]
 snapshots={};replay=[]
 with gzip.open(cell/'dynamic_native.jsonl.gz','rt')as f:
  for i,line in enumerate(f):
   if i>=2360:break
   old=json.loads(line);advance(d,np.asarray(old['actual_ctrl'])[ids],i//8 if i%8==0 else None,'old_replay_native')
   error=max(np.max(abs(d.qpos-old['qpos_full'])),np.max(abs(d.qvel-old['qvel_full'])),np.max(abs(d.ctrl-old['actual_ctrl'])),np.max(abs(d.mocap_pos-old['mocap_pos'])))
   max_error=max(max_error,float(error));assert error<=1e-8,'OLD_NATIVE_REPLAY_NOT_EXACT';replay.append(full(d))
   if(i+1)%8==0 and(i+1)//8 in states:
    snap=mujoco.MjData(m);mujoco.mj_copyData(snap,m,d);snapshots[(i+1)//8]=snap
 assert counts['old_replay_native']==2360;np.savez_compressed(root/'OLD_2360_REPLAY.npz',integration=replay)
 for entry in entries:
  step=entry['step'];folder=root/f'step{step:04d}';folder.mkdir();mujoco.mj_copyData(d,m,snapshots[step]);initial=full(d).copy();state=entry['state'];field=SimpleNamespace(**static.__dict__);field.pose_values=MethodType(pose_values,field);install_time_gate(field,state,'predictive',protocol['known_circles'],protocol['known_rectangles']);selected=None;attempts=[]
  from early_joint import activate,select
  reserved=ReservedRecovery(predictor,mujoco,ids,folder);reserved.public_goal_xy=np.asarray(protocol['goal_xy']);reserved.cache={'minimum_causal_predicted_clearance_m':entry['previous_reserve_minimum_m'],'created_step':294}
  reference=np.asarray(entry['reference']['path']);index=int(np.argmin(np.linalg.norm(reference[:,:2]-d.qpos[:2],axis=1)));index=min(index,len(reference)-2);reserved.set_reference(reference,index,protocol['goal_xy'],.60)
  assert activate(reserved,state,step)and step==295
  nominal=entry['nominal'];safe=sorted([c for c in nominal['candidates']if c['reason']is None],key=lambda c:c['score'],reverse=True);unique=[];seen=set()
  for c in safe:
   key=tuple(c['first_command'])
   if key in seen:continue
   seen.add(key);z=np.load(cell/'nominal_forecasts'/c['nominal_saved_forecast']);unique.append((c['score'],np.asarray(key),z['poses'],c['minimum_clearance_m'],c['self_domain_margin_m']))
  prefixes={};admit=reserved.admit_nominal
  def capture(*args):
   samples.clear();summary=admit(*args);prefixes[tuple(args[1])]=copy.deepcopy(samples);return summary
  reserved.admit_nominal=capture
  chosen=select(reserved,predictor,d,nominal['summary'],field,state,step,reference,index,folder,unique)
  assert np.array_equal(full(d),initial),'PRIVATE_PREDICTION_MUTATED_REAL'
  event=json.loads((folder/'early_joint_decisions.jsonl').read_text());attempts=event['probes'];dump(folder/'ATTEMPTS.json',attempts)
  if chosen is not None:
   command,gate,summary=chosen;proposal={'command':command.tolist(),'rank':gate['joint_admission_distinct_command_rank']};samples[:]=prefixes[tuple(command)];selected=(proposal,reserved)
  row=dict(step=step,tested_proposals=len(attempts),qualified=False,component_executed=False)
  if selected is not None:
   proposal,reserved=selected;cache=reserved.cache;q=np.vstack([[x['qpos']for x in samples],cache['qpos'],cache['one_cycle_continuation']['extra_qpos']]);v=np.vstack([[x['qvel']for x in samples],cache['qvel'],cache['one_cycle_continuation']['extra_qvel']]);controls=np.vstack([np.repeat([proposal['command']],8,axis=0),cache['controls'],cache['one_cycle_continuation']['extra_controls']]);p=poses(q);values=field.trajectory_values(p,.01);assert len(q)==336 and values.min()>=.155
   probe=mujoco.MjData(predictor.model);selected_bounds=[]
   for qi,vi in zip(q,v):
    probe.qpos[:]=qi;probe.qvel[:]=vi;mujoco.mj_forward(predictor.model,probe);selected_bounds.append(predictor.self_geometry.actual(predictor.model,probe))
   assert containment_margin(np.asarray(selected_bounds),bounds).min()>=.002 and np.linalg.norm(v[-1,:2])<=.025
   gain=float(np.linalg.norm(d.qpos[:2]-protocol['goal_xy'])-np.linalg.norm(q[-1,:2]-protocol['goal_xy']))
   dump(folder/'SELECTED.json',dict(proposal=proposal,cache=cache,complete_goal_progress_m=gain))
   np.savez_compressed(folder/'CERTIFICATE.npz',qpos=q,qvel=v,controls=controls,poses=p,self_bounds=selected_bounds,initial=initial,initial_qpos=d.qpos.copy(),initial_qvel=d.qvel.copy(),initial_ctrl=d.ctrl.copy(),causal_values=values,forecast_state=json.dumps(state))
   completed=[]
   for repeat in[False,True]:
    context=f'S{step}_'+('REPEAT'if repeat else'ACTUAL');real=mujoco.MjData(m);mujoco.mj_copyData(real,m,snapshots[step]);local=copy.deepcopy(trackers[step]);actual=[];safety=[];observations=[]
    for tick,command in enumerate(controls):
     safety.append(advance(real,command,step+tick//8 if tick%8==0 else None,'component_repeat_native'if repeat else'component_native'));error=max(np.max(abs(real.qpos-q[tick])),np.max(abs(real.qvel-v[tick])),np.max(abs(real.ctrl[ids]-command)));max_error=max(max_error,float(error));assert error<=1e-8,'NEW_NATIVE_PREFIX_TAIL_NOT_EXACT';actual.append(full(real))
     if tick%8==7:
      public=step+(tick+1)//8;xy,yaw=sensor_pose(real.qpos);packet=sensed_packet(xy,yaw,float(real.time),public,protocol,motion,noise);_,observed=local.update_packet(packet,protocol['known_rectangles'],protocol['known_circles']);coverage=check_forecast(config,observed);assert coverage['passed'];times=np.arange(657)*.01;lo,hi=future_cells(observed['outer_state_cells'],times);truth=np.asarray([motion.xy(observed['time']+t)for t in times]);excess=float(np.maximum(lo-truth[:,None,:],truth[:,None,:]-hi).max(axis=2).min(axis=1).max());assert excess<=1e-7 and(np.linalg.norm(truth-truth[0],axis=1)-.08*times).max()<=1e-7;observations.append(dict(packet=packet,state=observed,execution_coverage=coverage,planning_excess_m=excess))
    label='REPEAT'if repeat else'ACTUAL';np.savez_compressed(folder/(label+'.npz'),integration=actual,safety=safety)
    with gzip.open(folder/(label+'_OBSERVATIONS.json.gz'),'wt')as f:json.dump(observations,f)
    completed.append((np.asarray(actual),observations))
   repeat_error=float(np.max(abs(completed[0][0]-completed[1][0])));assert repeat_error<=1e-8 and completed[0][1]==completed[1][1]
   row.update(qualified=gain>=.02,component_executed=True,complete_goal_progress_m=gain,minimum_causal_clearance_m=float(values.min()),recovery_kind=cache['recovery_kind'],target=cache['target'],brake_after=cache['brake_after_native_ticks'],repeat_error=repeat_error)
  records.append(row);dump(root/'RESULTS.json',records);print(json.dumps(row,default=serial),flush=True)
 assert all(sha(repo/n)==h for n,h in freeze.items());status='EARLY_JOINT_COMPONENT_EVALUATED';dump(root/'RESULT.json',dict(status=status,records=records,counts={**counts,'private_native':predictor.prediction_steps},component_passed=any(x['qualified']for x in records),minimum_actual_clearance_m=minimum,minimum_self_margin_m=self_min,maximum_native_state_ctrl_error=max_error,bad_contacts=bad,internal_model_initializations=None,new_global_navigation=0))
except BaseException as error:
 status='STOPPED_EXCEPTION';dump(root/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()));raise
finally:
 if stream is not None:stream.close()
 signal.setitimer(signal.ITIMER_REAL,0);counts['private_native']=None if predictor is None else predictor.prediction_steps;window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',window);dump(root/'COMPLETION.json',dict(status=status,counts=counts,completed_inputs=len(records)))
