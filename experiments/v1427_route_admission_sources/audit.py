"""Integrated recorded full-state/receipt/geometry/source/whole-goal audit.

Pure recorded-data geometry; it never constructs or recomputes any model.
Actual applied-control replay and allocator recomputation are separate CPU2 proofs.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
recorded=exact('v1423_recorded_receipts',R/'experiments/v1423_integrated_route_audit/recorded.py')
gear_module=exact('v1423_independent_gear',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py')
mode_module=exact('v1423_independent_mode',R/'experiments/v1398_current_event_witness/mode_memory.py')
frames=exact('v1423_independent_actual_frames',R/'experiments/v1396_rpp_rpc_retirement/frames.py')
commands=exact('v1423_independent_route_commands',R/'experiments/v1411_native_guarded_execution/route_command.py')
branch_module=exact('v1423_independent_complete_branch_reader',R/'experiments/v1407_lossless_branch_stream/stream.py')
binding=exact('v1423_independent_causal_geometry',R/'experiments/v1415_unified_causal_witness/geometry_binding.py')
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
Reference=exact('v1423_independent_fixed_reference',R/'experiments/v1397_event_handoff_integration/response_reference.py').ResponseReference

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def loadnp(path):
 with np.load(path,allow_pickle=False)as z:return {k:z[k].copy()for k in z.files}
def fullstate(initial,trace,before):
 source=initial if before==0 else {k:trace[k][before-1]for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
 d={k:source[k].tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};d['time']=float(initial['time'][0])if before==0 else float(trace['time'][before-1]);return d

def audit(task):
 out=Path(task['output']);r=recorded.read(out/'RESULT.json');setup=recorded.read(out/'physics/SETUP.json');initial_packet=recorded.read(out/'INITIAL_PACKET.json');initial=loadnp(out/'INITIAL_FULL_STATE.npz');trace=loadnp(out/'physics/NATIVE_TRACE.npz');rows,events,root=recorded.collect(out);n=len(rows)
 assert set(initial)=={'time','qpos','qvel','ctrl','mocap_pos','mocap_quat'}
 assert n>0 and n==len(trace['time'])==r['new_actual_native']and not r['actual_inflight_unknown'],'ACTUAL_N_NPLUS1_COVERAGE'
 checks=dict(real_actual_evidence_not_software_fixture=not r.get('software_fixture_not_actual',False),actual_N_actions_Nplus1_states=all(len(trace[k])==n and np.shape(initial[k])==np.shape(trace[k][0])for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),finite_all_states=all(np.isfinite(trace[k]).all()and np.isfinite(initial[k]).all()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']),native_clock=bool(abs(trace['time']-.01*np.arange(1,n+1)).max()<=1e-8),physical_clearance=bool(trace['clearance'].min()>=.15-1e-8),self_margin=bool(trace['self_margin'].min()>=-1e-10),source_unchanged=r['source_unchanged']is True)
 ids=setup['actuator_ids'];ctrl=trace['ctrl'][:,ids];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
 checks['control_caps_and_slew']=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()and(abs(np.diff(np.vstack([initial_packet['controller_memory']['last_ctrl'],ctrl]),axis=0))<=rate+1e-10).all())
 with gzip.open(out/'physics/CONTACTS.json.gz','rt')as stream:contacts=json.load(stream)
 checks['complete_contacts_no_bad']=len(contacts)==n+1 and all(x[2]not in {'robot_obstacle_contact','robot_obstacle_penetration','robot_self_contact','unknown_contact'}for group in contacts for x in group)
 gear=gear_module.GearHandoff();mode=mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False);controls_by_owner={};sent={};command_gate=commands.Commands(task['run_id']);rpc_decisions=0
 for message in root:
  if message['kind']=='PUBLISHED_ACTUAL_ENVELOPE':
   envelope=message['envelope'];wire=envelope['wire'];frames.validate_wire(wire);assert wire['run_id']==task['run_id']and wire['sequence']not in sent
   sent[wire['sequence']]=wire;tick=wire['native_tick'];state=fullstate(initial,trace,tick);assert recorded.digest(state)==envelope['evidence_state_sha256'];assert envelope['feedback']['native_tick']==tick
  if message['kind']=='RECEIVED_ACTUAL_ROUTE'and message['packet']['kind']=='command':
   packet=message['packet'];command_gate.accept(packet,sent,current_native=message['before_native'],now=message['received_monotonic']);rpc_decisions+=1
 assert sent and min(sent)==0 and sorted(sent)==list(range(max(sent)+1))
 for i,row in enumerate(rows):
  assert row['applied']and row['before_native']==i
  before=fullstate(initial,trace,i);assert recorded.digest(before)==row['source_full_state_sha256'],'ROW_WRONG_ACTUAL_FULL_STATE'
  q=np.asarray(before['qpos']);velocity=np.asarray(before['qvel']);yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));body=[q[0],q[1],yaw,velocity[0]*math.cos(yaw)+velocity[1]*math.sin(yaw),velocity[5]]
  assert np.max(abs(np.asarray(row['body'])-body))<=1e-8
  encoder=np.r_[q[setup['steering_qpos_addresses']],velocity[setup['steering_qvel_addresses']]];assert np.max(abs(encoder-row['encoders']))<=1e-8
  upstream=row.get('upstream_request',row.get('raw_request'));vr,wr,proof=gear.select(*upstream[:2],native_tick=i,body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert row['request']==[vr,wr,False]and proof==row['gear_handoff']
  if 'mode_history'in row:assert mode.snapshot(i)==row['mode_history']
  mode.applied(before_native=i,v=vr,w=wr,parked_target=row['parked_target'],steering_motion_active_after=row['parked_target']is not None)
  owner=row['control_owner'];assert owner in {'ORIGINAL_RPP','DISCLOSED_SHARED_EXECUTION_BRIDGE','APPLIED_STOP_TAIL'};controls_by_owner[owner]=controls_by_owner.get(owner,0)+1
  delivery=row['delivery']
  if owner!='APPLIED_STOP_TAIL':
   frames.validate_binding(delivery,sent);assert delivery['source_kind']=='ACTUAL_FRAME'and 0<=i-delivery['observation_native_tick']<5
   checked=row.get('source_checked_monotonic',row.get('expiry_gate',{}).get('applied_monotonic'))
   assert checked is not None and 0<=checked-delivery['origin']['generated_monotonic']<=.2 and 0<=checked-delivery['observation_sampled_at']<=.2,'ROW_SOURCE_NOT_FRESH_AFTER_CERTIFICATE'
 checks.update(independent_body_encoders_fullstate_source=True,independent_gear_mode=True,actual_rpc_identity_and_retirement=rpc_decisions>0,continuous_control_owner_accounting=sum(controls_by_owner.values())==n)
 complete_reserves=0;minimum=math.inf;event_certificates=0
 for event in events:
  folder=event['folder'];current=event['current'];geom=binding.GeometryBinding(current,setup)
  if event['applied']:
   certificate=recorded.read(folder/'CERTIFICATE.json');assert certificate['input_sha256']==current['input_sha256']and certificate['generation']['passed']and certificate['independent_model_audit']['passed']
   for record in certificate['files']:assert sha(R/record['path'])==record['sha256']and(R/record['path']).stat().st_size==record['bytes']
   assert recorded.read(folder/'INDEPENDENT_AUDIT.json')['passed'];event_certificates+=1
  actual=folder/'actual'
  if not actual.exists():continue
  index=recorded.read(actual/'branches/INDEX.json');reader=branch_module.BranchReader(actual/'branches',index,np);branches={}
  for branch in index['branches']:
   bs,bu=reader.read(branch);proof=branch['proof'];tick=proof['before_native'];assert tick not in branches and proof['complete_native']==200 and proof['input_sha256']==current['input_sha256']
   lower=geom.tube(bs,tick);assert abs(lower-proof['causal_tube_lower_m'])<=1e-8;minimum=min(minimum,lower);branches[tick]=(proof,bs[0].copy());complete_reserves+=1
  reader.finish()
  with np.load(folder/'NOMINAL.npz',allow_pickle=False)as z:nominal=z['states'].tolist()
  request=recorded.read(out/'cusp_requests'/(folder.name+'.json'))['request'];reference=Reference(request,nominal)
  for row in event['applied']:
   tick=row['before_native'];proof,origin=branches[tick];packet=row['source_packet'];assert recorded.digest(packet)==row['source_packet_sha256']==proof['source_packet_sha256']
   assert proof['current_input_sha256']==current['input_sha256']and proof['causal_snapshot_sha256']==current['causal_snapshot_sha256']and proof['geometry_kind']==current['geometry_kind']
   assert proof['passed']and proof['rest']and proof['body_caps']and proof['causal_tube_lower_m']>=.22-1e-8
   expected=[*packet['body'][:3],packet['body'][3],packet['body_lateral'],packet['body'][4]];assert np.max(abs(origin[:6]-expected))<=1e-8
   after=fullstate(initial,trace,tick+1);q=after['qpos'];vv=after['qvel'];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));body=[q[0],q[1],yaw,vv[0]*math.cos(yaw)+vv[1]*math.sin(yaw),vv[5]]
   assert abs(geom.actual(body,tick+1)-row['physical_guard']['causal_lower_m'])<=1e-8 and geom.actual(body,tick+1)>=.22-1e-8
   if row.get('response_membership')is not None:assert reference.assess(body,tick+1)==row['response_membership']
 checks['every_applied_event_native_has_complete_current_reserve']=all(len(e['applied'])<=e.get('evidence_index',{}).get('complete_reserved_branches',0)for e in events)
 checks['event_certificates_and_fixed_reference']=event_certificates>0 and complete_reserves>=sum(len(e['applied'])for e in events)
 checks['complete200_applied_zero_tail']=len(rows)>=200 and all(row['control_owner']=='APPLIED_STOP_TAIL'and row['request']==[0.,0.,False]and row['parked_target']is None for row in rows[-200:])
 replay=r.get('replay',{});allocation=r.get('independent_allocation',{});checks['own_full_state_replay']=replay.get('passed')is True and replay.get('replay_native')==n and replay.get('maximum_qpos_qvel_ctrl_mocap_error',math.inf)<=1e-8 and replay.get('contact_mismatched_ticks')==0;checks['independent_allocation']=allocation.get('passed')is True and allocation.get('recorded_rows')==n and allocation.get('maximum_memory_control_error',math.inf)<=1e-8
 ros=recorded.read(out/'ROS_RESULT.json');checks['closed_original_action_and_goal']=ros.get('closed')is True and ros.get('passed')is True and not ros.get('evidence_write_errors')
 goal=float(np.linalg.norm(trace['qpos'][-1,:2]-task['goal_xy']));forward=float(np.dot(trace['qpos'][-1,:2]-task['start_xy'],[math.cos(task['start_yaw']),math.sin(task['start_yaw'])]));checks['whole_original_goal']=goal<=.45 and forward>=7.5
 physical=r.get('physical',{});checks['actual_detection_and_after_detection_travel']=physical.get('first_actor_detection')is not None and physical.get('actual_travel_after_detection_m',0.)>=1.
 coverage=exact('v1423_evaluator_only_forecast_coverage',R/'experiments/v1370_overnight_controller_matrix/evaluate_coverage.py').evaluate(out,recorded.read(out/'FORECAST_RECORDS.json'));checks['forecast_coverage']=coverage['passed']
 with gzip.open(out/'physics/SENSORS.json.gz','rt')as stream:sensors=json.load(stream)
 checks['sensor_initial_final_native']=bool(sensors and sensors[0]['native_tick']==0 and sensors[-1]['native_tick']==n)
 finalbody=rows[-1]['body'];checks['terminal_rest_and_zero_drive']=float(np.linalg.norm(trace['qvel'][-1,:2]))<=.03 and abs(trace['qvel'][-1,5])<=.03 and abs(trace['qvel'][-1,setup['steering_qvel_addresses']]).max()<=.03 and abs(ctrl[-1,2:]).max()<=1e-8
 checks['functional_and_evidence_complete']=r.get('functional_passed')is True and not r.get('first_error')and not r.get('save_errors')
 return dict(passed=all(checks.values()),checks=checks,actual_reviewed=n,complete_current_reserves=complete_reserves,minimum_complete_reserve_tube_m=None if minimum==math.inf else minimum,original_RPP_vs_shared_counts=controls_by_owner,goal_distance_m=goal,forward_progress_m=forward,prediction_coverage=coverage,models=0,analytical_native=0,physical_native=0,pair_still_separate=True)

def pair(main,repeat):
 a=Path(main);b=Path(repeat);ia=loadnp(a/'INITIAL_FULL_STATE.npz');ib=loadnp(b/'INITIAL_FULL_STATE.npz');ta=loadnp(a/'physics/NATIVE_TRACE.npz');tb=loadnp(b/'physics/NATIVE_TRACE.npz');maximum=0.
 assert set(ia)==set(ib)and set(ta)==set(tb)
 assert np.array_equal(ia['time'],ib['time'])and np.array_equal(ta['time'],tb['time']),'PAIR_NATIVE_CLOCK_CHANGED'
 for x,y in [(ia,ib),(ta,tb)]:
  for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
   assert x[key].shape==y[key].shape and np.isfinite(x[key]).all()and np.isfinite(y[key]).all(),'PAIR_SHAPE_OR_NONFINITE'
   if x[key].size:maximum=max(maximum,float(np.max(abs(x[key]-y[key]))))
 assert maximum<=1e-8
 return dict(passed=True,maximum_qpos_qvel_ctrl_mocap_error=maximum,models=0,physical_native=0)
