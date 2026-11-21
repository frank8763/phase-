"""Canonical measured input serialization; no optimizer, model or command."""
import copy
import importlib.util
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time
R=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('v1485_causal_boundary_source',Path(__file__).with_name('causal_boundary.py'));boundary=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(boundary)

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def vector(value,n):
 assert isinstance(value,list)and len(value)==n and all(type(x)in(int,float)and math.isfinite(x)for x in value),'PRIEST_CURRENT_VECTOR'

def capture(native,envelope,snapshot,*,prepared,authority,lock,next_segment):
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text())
 assert authority['scope']=='PRIEST_CURRENT_POLYNOMIAL_INPUT'and authority['models_authorized']is True
 assert parent['active_round']==authority['round_id']and parent['models_now_authorized']and parent['scientific_revisions']==7,'PRIEST_CURRENT_INPUT_NOT_ADMITTED'
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert authority['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 identity=prepared.hot_identity();assert identity==authority['core_identity_sha256']and prepared.source_manifest_sha256==authority['source_manifest_sha256']
 assert Path(native.packet.__func__.__code__.co_filename).resolve()==R/'experiments/v1423_integrated_route_audit/native_step.py','PRIEST_NONCANONICAL_PACKET_OWNER'
 v=native.vehicle;assert not native.in_step and native.applied==v.count and native.gear.last_tick==v.count-1
 assert len(v.commands)==len(v.rows)==v.count and len(v.contacts)==v.count+1 and v.audit.native_count==v.count and v.bad==0,'PRIEST_CURRENT_ACTUAL_COVERAGE'
 now=time.monotonic();actual=prepared.event.validate_envelope(envelope,run_id=native.run_id,now=now,previous_sequence=-1);wire=actual['wire']
 assert wire==native.sent[wire['sequence']]and wire['native_tick']==v.count,'PRIEST_INPUT_NOT_CURRENT_PUBLISHED_WIRE'
 before=prepared.native.state_digest(v);assert actual['evidence_state_sha256']==before
 fullstate={k:getattr(v.d,k).tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};fullstate['time']=float(v.d.time);assert digest(fullstate)==before
 modes=native.mode_memory.snapshot(v.count);gear=dict(gear=native.gear.gear,brake_start=native.gear.brake_start,last_tick=native.gear.last_tick)
 packet=native.packet(wire);feedback=actual['feedback']
 vector(packet['body'],5);vector(feedback['encoders'],4);vector(feedback['last_ctrl'],4)
 assert packet['body']==feedback['body']==wire['body']and [*packet['steering']['position'],*packet['steering']['velocity']]==feedback['encoders']
 assert packet['controller_memory']['last_ctrl']==feedback['last_ctrl']and packet['controller_memory']['integral']==feedback['integral']
 assert all(packet[k]==modes[k]for k in ['coupled_episode','steering_motion_active','parked_target'])
 assert feedback['parked_target']==packet['parked_target']and feedback['steering_motion_active']==packet['steering_motion_active']and feedback['gear_memory']==gear
 assert snapshot['model']=='PERIODIC'and snapshot['online_actor_truth']is False
 periodic=snapshot['periodic']
 if periodic is None:
  assert snapshot['last_observed_time']is None,'PRIEST_ABSENT_FORECAST_HAS_OBSERVATION'
  forecast=None;observation_stage='NO_DYNAMIC_RETURN_YET_NO_MEASURED_FUTURE'
 else:
  forecast=prepared.field.all_future(snapshot,current_native=v.count,current_sim_time=float(v.d.time));observation_stage='CURRENT_CAUSAL_COEFFICIENT_SNAPSHOT'
 assert set(next_segment)=={'gear','poses'}and type(next_segment['gear'])is int and next_segment['gear']in(-1,1)
 assert isinstance(next_segment['poses'],list)and 2<=len(next_segment['poses'])<=5001
 for pose in next_segment['poses']:vector(pose,3)
 b=packet['body'];yaw=b[2];lateral=packet['body_lateral'];offset=.3
 assert type(lateral)in(int,float)and math.isfinite(lateral)and abs(lateral)<=.03 and abs(b[3])<=.13 and abs(b[4])<=.16,'PRIEST_CURRENT_BODY_CAPS'
 assert abs(float(v.d.time)-.01*v.count)<=1e-8,'PRIEST_CURRENT_NATIVE_SIM_CLOCK'
 world_vx=b[3]*math.cos(yaw)-lateral*math.sin(yaw);world_vy=b[3]*math.sin(yaw)+lateral*math.cos(yaw)
 rear=[b[0]-offset*math.cos(yaw),b[1]-offset*math.sin(yaw),yaw]
 rear_velocity=[world_vx+offset*math.sin(yaw)*b[4],world_vy-offset*math.cos(yaw)*b[4]]
 value=dict(kind='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT',schema=1,run_id=native.run_id,core_identity_sha256=identity,core_identity=copy.deepcopy(prepared.value),source_manifest_sha256=prepared.source_manifest_sha256,
  origin=copy.deepcopy(packet),fullstate=fullstate,fullstate_sha256=before,mode_history=copy.deepcopy(modes),gear_memory=gear,actual_envelope=actual,next_segment=copy.deepcopy(next_segment),
  causal_snapshot=copy.deepcopy(snapshot),causal_snapshot_sha256=digest(snapshot),causal_forecast=forecast,observation_stage=observation_stage,public_map_sha256=prepared.public_map_sha256,
  rear_pose_world=rear,rear_velocity_world=rear_velocity,rear_acceleration_world=None,acceleration_source='NOT_MEASURED_EXPLICIT_POLYNOMIAL_BOUNDARY_HINT',author_initial_boundary_hint=boundary.from_recorded_owner(native,fullstate),
  fixed_origin_native=v.count,fixed_origin_sim_time=float(v.d.time),proposal_only=True,optimizer_executed=False,control_emitted=False,physical_admission=False)
 assert prepared.native.state_digest(v)==before and native.mode_memory.snapshot(v.count)==modes,'PRIEST_INPUT_CAPTURE_MUTATED_OWNER'
 assert 0<=time.monotonic()-wire['sampled_at']<=.2,'PRIEST_INPUT_EXPIRED_DURING_BINDING'
 return dict(value,input_sha256=digest(value))

class InitialAccelerationUnresolved(RuntimeError):pass

def author_initial_state(current):
 clean=dict(current);identity=clean.pop('input_sha256');assert digest(clean)==identity
 # Author polynomial boundary uses an explicitly non-measured planner hint.
 # The actual response model still starts from the complete actual source state.
 return boundary.boundary_state(current)
