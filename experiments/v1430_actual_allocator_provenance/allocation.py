"""Source-bound, sequential original Allocator recomputation, never integration."""
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback
import numpy as np
R=Path(__file__).resolve().parents[2]

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
frames=exact('v1430_actual_fullstate_measurement',R/'experiments/v1429_native_scalar_event_audit/event_audit.py')
mode_module=exact('v1430_canonical_mode_source',R/'experiments/v1398_current_event_witness/mode_memory.py')

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def fullstate(value):
 d={k:np.asarray(value[k]).tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};d['time']=float(value['time']);return d

def validate_initial(initial_fullstate,initial_packet,setup):
 before=fullstate(initial_fullstate);assert abs(before['time'])<=1e-12,'ALLOCATOR_INITIAL_NOT_CANONICAL_T0'
 body,lateral,enc=frames.measured(before,setup)
 frames.close(body,initial_packet['body'],'ALLOCATOR_INITIAL_BODY_NOT_ACTUAL');frames.close(lateral,initial_packet['body_lateral'],'ALLOCATOR_INITIAL_LATERAL_NOT_ACTUAL')
 frames.close(enc,[*initial_packet['steering']['position'],*initial_packet['steering']['velocity']],'ALLOCATOR_INITIAL_ENCODERS_NOT_ACTUAL')
 assert initial_packet['native_tick']==0 and abs(initial_packet['sim_time'])<=1e-12
 frames.close(np.asarray(before['ctrl'])[setup['actuator_ids']],initial_packet['controller_memory']['last_ctrl'],'ALLOCATOR_INITIAL_CONTROL_MEMORY_NOT_ACTUAL')
 assert initial_packet['coupled_episode']is False and initial_packet['steering_motion_active']is False and initial_packet['parked_target']is None
 return before

def validate_row(row,before,after,setup,*,expected_native):
 assert row['before_native']==expected_native and row['applied']is True,'ALLOCATOR_ACTUAL_ROW_MISSING_OR_DUPLICATE'
 before=fullstate(before);after=fullstate(after)
 assert abs(before['time']-.01*expected_native)<=1e-8 and abs(after['time']-.01*(expected_native+1))<=1e-8
 assert digest(before)==row['source_full_state_sha256'],'ALLOCATOR_ROW_FULL_STATE_CHANGED'
 body,lateral,enc=frames.measured(before,setup)
 frames.close(body,row['body'],'ALLOCATOR_ROW_BODY_NOT_ACTUAL');frames.close(enc,row['encoders'],'ALLOCATOR_ROW_ENCODERS_NOT_ACTUAL')
 frames.close(np.asarray(before['ctrl'])[setup['actuator_ids']],row['last_ctrl'],'ALLOCATOR_LAST_CONTROL_NOT_ACTUAL')
 assert np.isfinite(row['integral'])and row['control_owner']in {'ORIGINAL_RPP','DISCLOSED_SHARED_EXECUTION_BRIDGE','APPLIED_STOP_TAIL'}
 assert len(row['request'])==3 and row['request'][2]is False and all(type(x)in(int,float)and math.isfinite(x)for x in row['request'][:2])
 assert row['parked_target']is None or(type(row['parked_target'])in(int,float)and math.isfinite(row['parked_target']))
 if row.get('source_packet')is not None:frames.source_row(row,before,setup)
 control=np.asarray(after['ctrl'])[setup['actuator_ids']];assert control.shape==(4,)and np.isfinite(control).all()
 return dict(body=body,encoders=enc.tolist(),lateral=lateral,control=control)

def preflight(actual_rows,rows,initial_fullstate,initial_packet,setup,*,check=None):
 assert len(rows)==len(actual_rows)and len(rows)<=40000,'ALLOCATOR_N_NPLUS1_SOURCE_COVERAGE'
 before=validate_initial(initial_fullstate,initial_packet,setup)
 mode=mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False);owners={}
 for i,row in enumerate(rows):
  if check is not None:check()
  validate_row(row,before,actual_rows[i],setup,expected_native=i)
  if 'mode_history'in row:assert row['mode_history']==mode.snapshot(i),'ALLOCATOR_SOURCE_MODE_NOT_CONTINUOUS'
  mode.applied(before_native=i,v=row['request'][0],w=row['request'][1],parked_target=row['parked_target'],steering_motion_active_after=row['parked_target']is not None)
  owners[row['control_owner']]=owners.get(row['control_owner'],0)+1;before=fullstate(actual_rows[i])
 return dict(passed=True,source_rows=len(rows),canonical_Nplus1_source=True,control_owner_counts=owners,models=0,allocator_recomputations=0,analytical_integrations=0,physical_native=0,control_memory_integral_requires_actual_sequential_recomputation=True)

def audit(vehicle,rows,initial,*,initial_fullstate,setup,Adapter,mj,np,lock,maximum_recomputations,deadline_unix,deadline_monotonic,save):
 result=dict(passed=False,closed=False,recorded_rows=len(rows),allocator_recomputations=0,explicit_allocator_constructions=0,allocator_construction_inflight_unknown=False,allocator_recomputation_inflight_unknown=False,mujoco_models_created=0,physical_native=0,analytical_integrations=0,maximum_memory_control_error=0.,source_bound_actual_states=True)
 cursor=[None];original=None
 def vehicle_digest():
  return digest(dict(time=float(vehicle.d.time),**{k:np.asarray(getattr(vehicle.d,k)).tolist()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}))
 def budget():assert time.time()<deadline_unix and time.monotonic()<deadline_monotonic,'ALLOCATOR_DUAL_CLOCK_CAP'
 try:
  assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
  assert Path('/proc/self/fd/'+str(lock.fileno())).resolve()==R/'runs/v648_static_unknown/execution.lock';fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
  assert len(rows)==len(vehicle.rows)<=maximum_recomputations and maximum_recomputations<=40000
  source_proof=preflight(vehicle.rows,rows,initial_fullstate,initial,setup,check=budget);result['source_preflight']=source_proof
  before=validate_initial(initial_fullstate,initial,setup);original=vehicle_digest();budget()
  # Validate the first actual source before even constructing the allocator.
  if rows:validate_row(rows[0],before,vehicle.rows[0],setup,expected_native=0)
  result['allocator_construction_inflight_unknown']=True
  owner=Adapter(vehicle.m,mj,vehicle.dt,encoders=lambda:np.asarray(cursor[0]['encoders']));result['explicit_allocator_constructions']=1;result['allocator_construction_inflight_unknown']=False
  owner.virtual_rate=.6;owner.last=np.asarray(initial['controller_memory']['last_ctrl']).copy();owner.integral=initial['controller_memory']['integral'];owner._steering_motion_active=False
  mode=mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False);owners={}
  for i,row in enumerate(rows):
   budget();actual=validate_row(row,before,vehicle.rows[i],setup,expected_native=i);cursor[0]=actual
   if 'mode_history'in row:assert mode.snapshot(i)==row['mode_history'],'ALLOCATOR_MODE_MEMORY_NOT_CANONICAL'
   error=max(float(abs(owner.last-np.asarray(row['last_ctrl'])).max()),abs(owner.integral-row['integral']));result['maximum_memory_control_error']=max(result['maximum_memory_control_error'],error);assert error<=1e-8,'ALLOCATOR_MEMORY_RECOMPUTATION_DIVERGED'
   owner.parked_target=row['parked_target'];result['allocator_recomputation_inflight_unknown']=True
   u=owner.compute(*row['request'][:2],*actual['body'][3:],False)
   result['allocator_recomputations']+=1;result['allocator_recomputation_inflight_unknown']=False
   frames.close(u,actual['control'],'ALLOCATOR_CONTROL_RECOMPUTATION_DIVERGED');error=float(abs(u-actual['control']).max());result['maximum_memory_control_error']=max(result['maximum_memory_control_error'],error)
   mode.applied(before_native=i,v=row['request'][0],w=row['request'][1],parked_target=row['parked_target'],steering_motion_active_after=bool(owner._steering_motion_active))
   owners[row['control_owner']]=owners.get(row['control_owner'],0)+1;before=fullstate(vehicle.rows[i])
  assert vehicle_digest()==original,'ALLOCATOR_RECOMPUTATION_MUTATED_ACTUAL_STATE'
  result.update(passed=True,control_owner_counts=owners,final_mode_history=mode.snapshot(len(rows)))
 except BaseException as exc:result.update(first_error=repr(exc),traceback=traceback.format_exc())
 finally:
  result['closed']=True
  if original is not None:
   try:result['actual_state_unchanged']=vehicle_digest()==original
   except BaseException as exc:result['state_read_error']=repr(exc);result['passed']=False
   if result.get('actual_state_unchanged')is not True:result['passed']=False
  try:save(result)
  except BaseException as exc:
   result.update(passed=False,save_error=repr(exc));os.write(2,(json.dumps(result,allow_nan=False)+'\n').encode());raise
 return result
