"""Independent event evidence audit; pure arrays, never a model/step/permission.

The caller supplies the canonical N+1 full-state resolver. Source packets must
match those actual states and recorded allocator/mode memory, rather than only
matching a mutually consistent packet/proof hash. All branch controls and final
rest are recomputed from the complete saved arrays.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
R=Path(__file__).resolve().parents[2]

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
recorded=exact('v1427_event_recorded_source',R/'experiments/v1423_integrated_route_audit/recorded.py')
binding=exact('v1427_event_causal_geometry',R/'experiments/v1415_unified_causal_witness/geometry_binding.py')
stream=exact('v1427_event_branch_stream',R/'experiments/v1407_lossless_branch_stream/stream.py')
feedback=exact('v1427_event_scalar_feedback',R/'experiments/v1409_scalar_steering_feedback/feedback.py')
sys.path.insert(0,str(R/'experiments/v1397_event_handoff_integration'))
Reference=exact('v1427_event_response_reference',R/'experiments/v1397_event_handoff_integration/response_reference.py').ResponseReference

def close(a,b,label):
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
 assert a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all(),label+'_SHAPE_OR_NONFINITE'
 assert not a.size or float(abs(a-b).max())<=1e-8,label

def measured(state,setup):
 q=np.asarray(state['qpos']);v=np.asarray(state['qvel']);yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
 body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]]
 lateral=-v[0]*math.sin(yaw)+v[1]*math.cos(yaw)
 enc=np.r_[q[setup['steering_qpos_addresses']],v[setup['steering_qvel_addresses']]]
 return body,float(lateral),enc

def source_row(row,state,setup):
 packet=row['source_packet'];tick=row['before_native']
 assert recorded.digest(packet)==row['source_packet_sha256'],'EVENT_PACKET_HASH_CHANGED'
 assert recorded.digest(state)==row['source_full_state_sha256'],'EVENT_FULL_STATE_HASH_CHANGED'
 assert packet['native_tick']==packet['steering']['native_tick']==tick
 assert abs(packet['sim_time']-state['time'])<=1e-8,'EVENT_PACKET_PHYSICAL_CLOCK_CHANGED'
 body,lateral,enc=measured(state,setup)
 close(body,packet['body'],'EVENT_PACKET_BODY_NOT_ACTUAL');close(lateral,packet['body_lateral'],'EVENT_PACKET_LATERAL_NOT_ACTUAL')
 close(enc,[*packet['steering']['position'],*packet['steering']['velocity']],'EVENT_PACKET_ENCODERS_NOT_ACTUAL')
 close(body,row['body'],'EVENT_ROW_BODY_NOT_ACTUAL');close(enc,row['encoders'],'EVENT_ROW_ENCODERS_NOT_ACTUAL')
 close(packet['controller_memory']['last_ctrl'],row['last_ctrl'],'EVENT_PACKET_ALLOCATOR_LAST_CHANGED')
 close(packet['controller_memory']['integral'],row['integral'],'EVENT_PACKET_ALLOCATOR_INTEGRAL_CHANGED')
 for key in ['coupled_episode','steering_motion_active','parked_target']:assert packet[key]==row['mode_history'][key],'EVENT_PACKET_MODE_CHANGED'
 assert row['mode_history']['covered_native']==tick
 return packet

def complete_branch(states,ctrl,proof,setup,*,geometry,packet=None):
 assert states.shape==(201,8)and ctrl.shape==(200,4)and np.isfinite(states).all()and np.isfinite(ctrl).all()
 assert proof['complete_native']==200
 tick=proof['before_native'];lower=geometry.tube(states,tick)
 close(lower,proof['causal_tube_lower_m'],'EVENT_RESERVE_TUBE_RECOMPUTATION_CHANGED')
 caps=bool((abs(states[:,3:6])<=np.asarray([.13,.03,.16])+1e-8).all())
 wheel=feedback.from_state(states[-1]);rest=bool(abs(states[-1,[3,4,5]]).max()<=.003 and max(abs(x)for x in wheel[2:])<=.03 and abs(ctrl[-1,2:]).max()<=1e-10)
 assert bool(proof['body_caps'])==caps and bool(proof['rest'])==rest,'EVENT_RESERVE_REST_OR_CAPS_CHANGED'
 assert type(proof['passed'])is bool and proof['passed']==bool(lower>=.22-1e-8 and caps and rest),'EVENT_RESERVE_PASS_CHANGED'
 limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01
 assert (ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all(),'EVENT_RESERVE_CONTROL_CAP'
 assert (abs(np.diff(ctrl,axis=0))<=rate+1e-10).all(),'EVENT_RESERVE_CONTROL_SLEW'
 if packet is not None:
  close(states[0,:6],[*packet['body'][:3],packet['body'][3],packet['body_lateral'],packet['body'][4]],'EVENT_RESERVE_ORIGIN_NOT_ACTUAL')
  assert (abs(ctrl[0]-packet['controller_memory']['last_ctrl'])<=rate+1e-10).all(),'EVENT_RESERVE_FIRST_CONTROL_SLEW'
 return float(lower)

def audit_event(event,*,setup,request_packet,state_at):
 folder=Path(event['folder']);current=event['current'];applied=event['applied'];geom=binding.GeometryBinding(current,setup)
 request=request_packet['request'];value=dict(request);identity=value.pop('request_sha256');assert recorded.digest(value)==identity
 assert current['causal_snapshot']==request_packet['causal_snapshot']and current['causal_snapshot_sha256']==recorded.digest(request_packet['causal_snapshot'])
 origin=current['origin']['native_tick'];assert request['actual']['wire']['native_tick']==origin
 certificate=recorded.read(folder/'CERTIFICATE.json')
 assert certificate['request_sha256']==identity and certificate['input_sha256']==current['input_sha256']and certificate['start_native']==origin
 assert certificate['start_full_state_sha256']==recorded.digest(state_at(origin)),'EVENT_CERTIFICATE_CURRENT_STATE_CHANGED'
 assert certificate['method']==current['method_spec'],'EVENT_CERTIFICATE_METHOD_CHANGED'
 closure=recorded.read(folder/'TRANSACTION_CLOSED.json');assert closure['closed']and closure['passed']and not closure['closing_errors']and not closure['save_errors']
 assert closure['actual_native_delta_during_certificate']==0 and closure['actual_full_state_unchanged']is True
 generation=recorded.read(folder/'GENERATION.json');audit=recorded.read(folder/'INDEPENDENT_AUDIT.json')
 assert generation==certificate['generation']and audit==certificate['independent_model_audit']
 for proof,unknown in [(generation,'analytical_inflight_unknown'),(audit,'audit_inflight_unknown')]:
  assert proof['passed']is True and proof['closed']is True and proof[unknown]is False
  assert proof['input_sha256']==current['input_sha256']and proof['qualified_method']==current['method_spec']['method']
  assert proof['causal_snapshot_sha256']==current['causal_snapshot_sha256']and proof['geometry_kind']==current['geometry_kind']
  assert proof['checks']['complete200_zero_tail']is True
 assert generation['nominal_native']==generation['complete_braking_branches']==audit['braking_origins']and audit['model_error']<=1e-8
 listed=set()
 for record in certificate['files']:
  path=R/record['path'];assert path.is_relative_to(folder)and not path.is_symlink()and path not in listed
  listed.add(path);assert path.stat().st_size==record['bytes']and hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
 assert {folder/name for name in ['CURRENT_INPUT.json','SETUP.json','GENERATION.json','INDEPENDENT_AUDIT.json','NOMINAL.npz','JOURNAL.json','MEMORY.json','MODES.json','MODELED_ACCEPTED.json']}<=listed,'EVENT_CERTIFICATE_REQUIRED_FILE_MISSING'
 actual=folder/'actual';index=recorded.read(actual/'branches/INDEX.json');assert index['input_sha256']==current['input_sha256']
 expected={row['before_native']:row for row in applied};assert len(expected)==len(applied)
 with np.load(folder/'NOMINAL.npz',allow_pickle=False)as z:nominal=z['states'].tolist()
 assert len(nominal)==generation['nominal_native']+1
 reference=Reference(request,nominal);reader=stream.BranchReader(actual/'branches',index,np);seen=set();minimum=math.inf;memberships=0
 try:
  for branch in index['branches']:
   states,ctrl=reader.read(branch);proof=branch['proof'];tick=proof['before_native'];assert tick not in seen;seen.add(tick)
   for key,value in [('input_sha256',current['input_sha256']),('current_input_sha256',current['input_sha256']),('causal_snapshot_sha256',current['causal_snapshot_sha256']),('geometry_kind',current['geometry_kind'])]:assert proof[key]==value,'EVENT_BRANCH_INPUT_IDENTITY_CHANGED'
   row=expected.get(tick);packet=None if row is None else source_row(row,state_at(tick),setup)
   lower=complete_branch(states,ctrl,proof,setup,geometry=geom,packet=packet);minimum=min(minimum,lower)
   if row is None:continue
   assert proof['source_packet_sha256']==row['source_packet_sha256']and proof['passed']is True
   body,_,_=measured(state_at(tick+1),setup);guard=row['physical_guard'];assert guard['native']==tick+1
   after_lower=geom.actual(body,tick+1);assert after_lower>=.22-1e-8
   close(after_lower,guard['causal_lower_m'],'EVENT_PHYSICAL_CAUSAL_GEOMETRY_CHANGED')
   membership=row.get('response_membership')
   if row['phase']not in {'ORIGINAL_ROUTE_ZERO_WAIT','COMPLETE_STOP_TAIL','ERROR_COMPLETE_STOP_TAIL'}:assert membership is not None,'EVENT_FIXED_REFERENCE_MEMBERSHIP_MISSING'
   if membership is not None:assert reference.assess(body,tick+1)==membership;memberships+=1
  reader.finish()
 except BaseException:
  reader.stream.close();raise
 assert set(expected)<=seen and len(seen)==event['evidence_index']['complete_reserved_branches']
 return dict(passed=True,applied_native_reviewed=len(applied),complete_reserves_reviewed=len(seen),fixed_reference_memberships=memberships,minimum_complete_reserve_tube_m=None if minimum==math.inf else minimum,models=0,physical_native=0,analytical_integrations=0,scientific_or_physical_admission=False)
