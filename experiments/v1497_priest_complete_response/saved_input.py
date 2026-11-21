"""Source qualification for a NEW method on saved actual data, never a wire."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
R=Path(__file__).resolve().parents[2]

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def capture(*,original_event_input,original_setup,full_states,journal,remote_index,remote_proof,prepared):
 import numpy as np
 paths=[Path(p)for p in [original_event_input,original_setup,full_states,journal,remote_index,remote_proof]]
 assert all(p.resolve().is_relative_to(R/'runs')and p.is_file()and not p.is_symlink()for p in paths)
 assert all(prepared.sources.get(str(p.relative_to(R)))==sha(p)for p in paths),'SAVED_INPUT_NOT_IN_PREPARED_IMMUTABLE_SOURCE_CHAIN'
 assert read(remote_proof)['passed']and read(remote_proof)['every_member_SHA_and_link_text']and read(remote_proof)['recovery_index_download_SHA']
 members={row['path']:row for row in read(remote_index)['files']};verified=[]
 for p in paths[:4]:
  name=str(p.relative_to(R));row=members[name];assert row['bytes']==p.stat().st_size and row['sha256']==sha(p)
  verified.append(dict(path=name,sha256=row['sha256'],bytes=row['bytes']))
 original=read(original_event_input);clean=copy.deepcopy(original);identity=clean.pop('input_sha256');assert digest(clean)==identity
 origin=copy.deepcopy(original['origin']);n=origin['native_tick'];assert type(n)is int and 2<=n<=40000
 setup=read(original_setup);assert setup['known']==read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')and setup['dt']==.01
 # Read recorded state arrays only. Never construct/replay a vehicle or infer
 # measured actor future from qpos/mocap; only packet body/encoder provenance.
 with np.load(full_states,allow_pickle=False)as arrays:
  assert set(['time','qpos','qvel','ctrl','mocap_pos','mocap_quat'])<=set(arrays.files)
  assert all(len(arrays[k])>n for k in ['time','qpos','qvel','ctrl','mocap_pos','mocap_quat'])
  def at(i):return dict(time=float(arrays['time'][i]),**{k:np.asarray(arrays[k][i]).tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']})
  current=at(n);previous=at(n-1)
 assert abs(current['time']-.01*n)<=1e-8 and current['time']==origin['sim_time']
 mode_module=exact('v1497_original_mode_history',R/'experiments/v1398_current_event_witness/mode_memory.py')
 gear_module=exact('v1497_original_gear_history',R/'experiments/v1396_rpp_rpc_retirement/gear_handoff.py')
 recorded=exact('v1497_original_receipt_normalizer',R/'experiments/v1423_integrated_route_audit/recorded.py')
 # This original saved task never installed a bridge. Refuse arbitrary mixed
 # traces rather than treating ordinary-prefix receipts as whole new schema.
 events=[json.loads(line)for line in Path(journal).read_text().splitlines()if line]
 rows=recorded.receipts(events,before_kind='BEFORE_ORIGINAL_PREFIX_NATIVE',after_kind='AFTER_ORIGINAL_PREFIX_NATIVE',bound_hash=False)
 assert [r['before_native']for r in rows]==list(range(len(rows)))and len(rows)>n
 row=rows[n];assert row['source_full_state_sha256']==digest(current)==original['full_state_sha256']
 q=current['qpos'];v=current['qvel'];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
 measured=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]];lateral=-v[0]*math.sin(yaw)+v[1]*math.cos(yaw)
 enc=[*[q[i]for i in setup['steering_qpos_addresses']],*[v[i]for i in setup['steering_qvel_addresses']]]
 def close(a,b,label):
  a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);assert a.shape==b.shape and np.isfinite(a).all()and np.isfinite(b).all()and(not a.size or abs(a-b).max()<=1e-8),label
 close(measured,origin['body'],'SAVED_CURRENT_BODY_NOT_ACTUAL');close(lateral,origin['body_lateral'],'SAVED_CURRENT_LATERAL_NOT_ACTUAL');close(enc,[*origin['steering']['position'],*origin['steering']['velocity']],'SAVED_CURRENT_ENCODERS_NOT_ACTUAL')
 close([current['ctrl'][i]for i in setup['actuator_ids']],origin['controller_memory']['last_ctrl'],'SAVED_LAST_CONTROL_NOT_ACTUAL')
 close(row['body'],origin['body'],'SAVED_ROW_BODY_CHANGED');close(row['encoders'],enc,'SAVED_ROW_ENCODERS_CHANGED');close(row['last_ctrl'],origin['controller_memory']['last_ctrl'],'SAVED_ROW_MEMORY_CHANGED');assert row['integral']==origin['controller_memory']['integral']
 mode=mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False);gate=gear_module.GearHandoff()
 for i,r in enumerate(rows[:n]):
  assert r['before_native']==i and r['applied']and r['parked_target']is None
  vr,wr,proof=gate.select(*r['upstream_request'][:2],native_tick=i,body=r['body'],last_ctrl=r['last_ctrl'],encoders=r['encoders'])
  assert [vr,wr,False]==r['request']and proof==r['gear_handoff']
  mode.applied(before_native=i,v=vr,w=wr,parked_target=r['parked_target'],steering_motion_active_after=False)
 modes=mode.snapshot(n);gear=dict(gear=gate.gear,brake_start=gate.brake_start,last_tick=gate.last_tick)
 assert modes==original['mode_history']and gear==original['gear_memory']
 for key in ['coupled_episode','steering_motion_active','parked_target']:assert origin[key]==modes[key]
 snapshot=copy.deepcopy(original['causal_snapshot']);assert digest(snapshot)==original['causal_snapshot_sha256']and snapshot['periodic']is not None
 forecast=prepared.field.all_future(snapshot,current_native=n,current_sim_time=current['time']);assert forecast==original['bridge_forecast']
 assert origin['sim_time']==current['time'];b=origin['body'];kin=exact('v1497_original_causal_boundary',R/'experiments/v1485_priest_current_polynomial_seam/causal_boundary.py')
 rear=kin.rear_kinematics(current);hint=kin.initial_hint(current,previous,native_tick=n)
 provenance=dict(role='RECORDED_ACTUAL_SOURCE_FOR_NEW_PRIEST_MODEL_COMPONENT_ONLY',original_event_input_sha256=identity,source_rows_covered=n,remote_original_files_verified=True,files=verified,remote_index_sha256=sha(remote_index),remote_proof_sha256=sha(remote_proof),current_fullstate_sha256=digest(current),previous_fullstate_sha256=digest(previous),no_new_dynamics_or_Allocator_recomputation=True,not_fresh_wire=True,original_RPP_prefix_not_PRIEST_navigation=True,instantaneous_acceleration_measurement_known=False,integral_numerical_recomputation_unexecuted=True,model_or_actual_admission=False)
 value=dict(kind='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT',schema=1,input_role='SAVED_ACTUAL_INPUT_MODEL_ONLY',run_id='NEW_PRIEST_SAVED_INPUT_COMPONENT',core_identity_sha256=prepared.hot_identity(),core_identity=copy.deepcopy(prepared.value),source_manifest_sha256=prepared.source_manifest_sha256,origin=origin,fullstate=current,fullstate_sha256=digest(current),mode_history=modes,gear_memory=gear,causal_snapshot=snapshot,causal_snapshot_sha256=digest(snapshot),causal_forecast=forecast,observation_stage='CURRENT_CAUSAL_COEFFICIENT_SNAPSHOT',public_map_sha256=prepared.public_map_sha256,rear_pose_world=[*rear['position'],rear['yaw']],rear_velocity_world=rear['velocity'],rear_acceleration_world=None,author_initial_boundary_hint=hint,next_segment=copy.deepcopy(original['next_segment']),fixed_origin_native=n,fixed_origin_sim_time=current['time'],saved_actual_input_not_fresh_wire=True,saved_provenance=provenance,proposal_only=True,physical_admission=False)
 return dict(value,input_sha256=digest(value)),setup
