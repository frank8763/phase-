"""Canonical actual-owner lifecycle. No admission is created by this source."""
import ast
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent;C=R/'experiments/v1449_route_initializer_binding';O=R/'runs'/N.name

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
io=exact('v1421_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
owner_module=exact('v1421_canonical_owner',C/'canonical_owner.py')
pump_module=exact('v1421_actual_pump',C/'pump.py')
peer_module=exact('v1423_current_model_peer_lifecycle',C/'model_peer.py')
phase_module=exact('v1437_native_shared_phase_runtime',C/'phase_runtime.py')

contract=exact('v1464_narrow_live_event_contract',N/'contract.py')
NotAdmitted=contract.NotAdmitted

def admit(task,approval,window):
 qualification=contract.authorize(task,window,native=True)
 assert approval==read(O/'APPROVAL.json')
 return qualification


def physical_binding(output):
 import numpy as np
 from types import SimpleNamespace
 bound=exact('v1423_complete_frozen_adapter_binding',R/'experiments/v1115_coupled_complete_source/bindings.py');Adapter=bound.Adapter
 pinpath=R/'experiments/v1179_frozen_recovery_native/recovery_tools.py';pin=next(x for x in ast.parse(pinpath.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='pin');scope=dict(Path=Path,os=os);exec(compile(ast.Module(body=[pin],type_ignores=[]),str(pinpath),'exec'),scope);old=SimpleNamespace(np=np,pin=scope['pin'])
 factory=exact('v1423_canonical_scene_factory',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');factory.O=output.parent
 replay=exact('v1423_exact_applied_control_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
 assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
 return old,Adapter,factory,replay


def _run(task,approval,window,evidence_quota):
 qualification=admit(task,approval,window);out=Path(task['output']);limits=qualification['limits'];v=None;canonical=None;pump=None;modeled=None;creating=False;replaying=False;first=None;save_errors=[];journal=None;capture=None;tail_started=False
 quota_module=exact('v1432_actual_pre_wire_quota',C/'quota.py')
 capture_module=exact('v1431_complete_physical_capture_budget',R/'experiments/v1454_bounded_gzip_closure/capture_budget.py')
 def atomic(path,value):
  if Path(path).name in {'FIRST_ERROR.json','TRANSACTION_ERROR.json','CUSP_BIND_ERROR.json','ERROR_STOP_TAIL.json'}:return evidence_quota.error_atomic(path,value,io.atomic)
  return evidence_quota.atomic(path,value,io.atomic)
 result=dict(passed=False,closed=False,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,own_replay_native=0,new_actual_native=0,actual_inflight_unknown=False,historical_controls_used=0)
 phases=phase_module.PhaseRuntime(window,limits,lambda value:atomic(out/'NATIVE_PHASES.json',value))
 phase_gate=phase_module.NativePhaseGate(phases,limits,lambda:v,lambda:capture)
 startup=exact('v1464_canonical_ready_control',N/'startup.py')
 started=time.monotonic();next_storage=0.
 def remaining():
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id']
  return min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())
 def check(stage,requested):
  startup.check_native_stop(out,run_id=task['run_id'],source_identity=approval['qualification_sha256'])
  phase_gate(stage,requested)
  # Byte snapshots are prepared by Pump.publish before a fresh actual wire;
  # each write is charged by OutputBoundary, never by a hot full-tree walk.

 def attempt(stage,fn):
  try:return fn()
  except BaseException as exc:
   save_errors.append(dict(stage=stage,error=repr(exc)))
   try:phases.arm_root()
   except BaseException as clock_error:save_errors.append(dict(stage='ROOT_ALARM_AFTER_'+stage,error=repr(clock_error)))
   return None
 def stop(*_):raise TimeoutError('ACTUAL_ROUTE_HARD_STOP_SAVE_PREFIX')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   phases.transition('normal')
   check('INITIALIZATION',0);evidence_quota.admit(16*1024**2,'CANONICAL_INITIALIZER_FILE_HEADROOM');old,Adapter,factory,replay=physical_binding(out);np=old.np
   creating=True;atomic(out/'INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),physical_native=0))
   import mujoco as mj
   saves=exact('v1432_native_model_file_admission',C/'bounded_io.py')
   init_end=startup.initializer_deadlines(window,phases.budget.deadlines(),cap_s=limits['canonical_initializer_wall_cap_s'])
   signal.setitimer(signal.ITIMER_REAL,max(.001,min(init_end['absolute_deadline_unix']-time.time(),init_end['hard_stop_monotonic']-time.monotonic())))
   with saves.native_model_saves(mj,evidence_quota.charge_write):v=factory.create_vehicle(out/'physics',task)
   creating=False;result['canonical_vehicle_initializations']=1
   phases.arm(phases.budget.deadlines());check('INITIALIZATION',0)
   old.pin();capture=capture_module.CaptureBudget(evidence_quota);capture.update(v)
   import mujoco as mj
   assert v.count==0 and v.d.time==0.
   before=owner_module.native_module.state_digest(v);previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
   assert owner_module.native_module.state_digest(v)==before
   journal=(out/'ACTUAL_OWNER_JOURNAL.jsonl').open('x',buffering=1)
   def append(row):
    encoded=json.dumps(row,separators=(',',':'),allow_nan=False)+'\n';evidence_quota.admit(2*len(encoded.encode())+16384,'ROOT_ACTUAL_OWNER_RECEIPT');journal.write(encoded);journal.flush()
   modeled=peer_module.EventPeer(out,run_id=task['run_id'],check_budget=check,atomic=atomic)
   canonical_authority=dict(approval,scope='ACTUAL_ROUTE_EVENT_WITNESS',outer_scope=approval['scope'],whole_route_admission=False,maximum_events=1)
   canonical=owner_module.CanonicalOwner(v,task=task,output=out,setup=read(out/'physics/SETUP.json'),authority=canonical_authority,lock=lock,budget=dict(generation_native=0,audit_native=0,generation_inflight_unknown=False,audit_inflight_unknown=False),limits=limits['witness'],reserve_accounting=dict(analytical_native=0,predictor_constructions=0,analytical_inflight_unknown=False,construction_inflight_unknown=False),reserve_limits=limits['current_reserve'],atomic=atomic,np=np,peer_command=modeled.command,peer_replies=modeled.replies,check_budget=check,quota=evidence_quota)
   # The normal phase includes all current generation/audit/reserve work.
   private_deadline=dict(canonical_authority,**phases.budget.deadlines())
   canonical.authority=private_deadline
   canonical.transaction.authority=private_deadline
   evidence_quota.save_npz(out/'INITIAL_FULL_STATE.npz',dict(time=np.asarray(v.d.time),**{k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}),np)
   atomic(out/'INITIAL_PACKET.json',canonical.native.packet(None));pump=pump_module.Pump(canonical,check_budget=check,append=append,model_peer=modeled)
   startup.emit_ready(v,canonical,out,run_id=task['run_id'],source_identity=approval['qualification_sha256'],atomic=atomic)
   event_stop=exact('v1464_real_current_event_stop',N/'event_stop.py').FirstEventStop(canonical,pump)
   while not pump.stopped:
    event_stop.before_iteration();pump.iteration();event_stop.after_iteration()
   result['live_first_event']=event_stop.require_complete()
   evidence_quota.retire_grant();tail_started=True;phases.transition('complete_zero_tail')
   evidence_quota.retire_grant();evidence_quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=evidence_quota.external_writers)
   atomic(out/'STOP_PHASE_AUTHORITY.json',phase_module.bind_stop_authority(canonical,phases))
   for _ in range(200):
    if canonical.native.bridge_started:
     check('ACTUAL_STOP_TAIL',1);canonical.native.apply(0.,0.,phase='COMPLETE_STOP_TAIL',control_owner='APPLIED_STOP_TAIL',delivery=None,stop_tail=True)
    else:pump.prefix_step(None,stop_tail=True)
   canonical.envelope();body=list(v.body());distance=math.dist(body[:2],task['goal_xy']);progress=sum((body[i]-task['start_xy'][i])*[math.cos(task['start_yaw']),math.sin(task['start_yaw'])][i]for i in range(2))
   result['functional_checks']=dict(original_action_succeeded=pump.ros_pass,whole_goal_distance=distance<=.45,whole_forward_progress=progress>=7.5,body_stopped=max(abs(x)for x in body[3:])<=.03,steering_settled=max(abs(x)for x in v.steering_sample()[2:])<=.03,drive_zero=max(abs(x)for x in v.adapter.last[2:])<=1e-8,complete200_applied_zero_tail=canonical.native.last_zero_count>=200)
   result.update(whole_goal_distance_m=distance,whole_forward_progress_m=progress,functional_passed=all(result['functional_checks'].values()),runtime_component_passed=result['live_first_event']['complete_actual_bridge']and result['functional_checks']['complete200_applied_zero_tail'],whole_route_navigation_passed=False,independent_complete_route_audit_required=True,partial_navigation_attempt=True)
  except BaseException as exc:
   evidence_quota.retire_grant()
   first=dict(error=repr(exc),traceback=traceback.format_exc());attempt('SAVE_FIRST_ERROR',lambda:atomic(out/'FIRST_ERROR.json',first))
   if not tail_started and pump is not None and canonical is not None and not pump.prefix_inflight and not canonical.native.in_step:
    try:
     tail_started=True;phases.transition('complete_zero_tail')
     evidence_quota.retire_grant();evidence_quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=evidence_quota.external_writers)
     atomic(out/'STOP_PHASE_AUTHORITY.json',phase_module.bind_stop_authority(canonical,phases))
     for _ in range(200):
      if canonical.native.bridge_started:
       check('ACTUAL_STOP_TAIL',1);canonical.native.apply(0.,0.,phase='ERROR_COMPLETE_STOP_TAIL',control_owner='APPLIED_STOP_TAIL',delivery=None,stop_tail=True)
      else:pump.prefix_step(None,stop_tail=True)
     canonical.envelope();result['error_complete200_zero_tail_applied']=True
    except BaseException as stopping:
     result.update(error_complete200_zero_tail_applied=False,error_stop_tail_error=repr(stopping))
     attempt('SAVE_SECONDARY_STOP_ERROR',lambda:atomic(out/'ERROR_STOP_TAIL.json',dict(primary=first,stopping_error=repr(stopping),complete_tail=False)))
  finally:
   signal.setitimer(signal.ITIMER_REAL,0);evidence_quota.retire_grant()
   attempt('ENTER_PEER_CLOSE_PHASE',lambda:phases.transition('peer_close'))
   if modeled is not None:attempt('CLOSE_MODELED_PEER',modeled.close_event)
   if pump is not None:attempt('CLOSE_ACTUAL_SOCKET',pump.close)
   if pump is not None:attempt('WAIT_ACTUAL_ROS_CLOSE',lambda:phase_module.wait_actual_ROS_close(out,phases))
   if canonical is not None:attempt('CLOSE_CANONICAL_OWNER',canonical.close)
   if journal is not None:attempt('CLOSE_ACTUAL_JOURNAL',journal.close)
   inflight=bool((pump is not None and pump.prefix_inflight)or(canonical is not None and canonical.native.in_step))
   result.update(first_error=first,canonical_vehicle_initializations=None if creating else result['canonical_vehicle_initializations'],new_actual_native=None if inflight else(0 if v is None else v.count),actual_inflight_unknown=inflight)
   if v is not None:
    def state_first():
     module=exact('v1456_state_before_contact_closure',N/'state_capture.py')
     with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as initial:source={k:initial[k].copy()for k in initial.files}
     return module.save_current_prefix(v,source,out,evidence_quota,np)
    result['fullstate_prefix_before_contact']=attempt('SAVE_FULLSTATE_BEFORE_CONTACT_SERIALIZATION',state_first)
    result['physical']=attempt('SAVE_PHYSICAL_PREFIX',lambda:capture.finish(v))if capture is not None and not capture.finish_attempted else None
    if result['physical']is not None and not result['actual_inflight_unknown']and first is None and not save_errors and result.get('fullstate_prefix_before_contact',{}).get('complete')is True:
     def audit_allocation():
      phases.transition('allocator_recompute');end=phases.budget.deadlines()
      recorded=exact('v1423_complete_receipt_normalizer',R/'experiments/v1423_integrated_route_audit/recorded.py');allocation=exact('v1431_bound_allocator_audit',R/'experiments/v1430_actual_allocator_provenance/allocation.py')
      allrows,_,_=recorded.collect(out)
      with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as initial_stream:initial_source={k:initial_stream[k].copy()for k in initial_stream.files}
      proof=allocation.audit(v,allrows,read(out/'INITIAL_PACKET.json'),Adapter=Adapter,mj=mj,np=np,lock=lock,initial_fullstate=initial_source,setup=read(out/'physics/SETUP.json'),save=lambda value:atomic(out/'INDEPENDENT_ALLOCATION.json',value),maximum_recomputations=limits['maximum_allocator_recomputations'],deadline_unix=end['absolute_deadline_unix'],deadline_monotonic=end['hard_stop_monotonic'])
      return proof
     result['independent_allocation']=attempt('INDEPENDENT_ALLOCATION_RECOMPUTATION',audit_allocation)
    if canonical is not None:result['canonical_accounting']=canonical.native.exact_accounting();result['model_generation_and_audit_accounting']=dict(canonical.transaction.budget);result['current_reserve_accounting']=dict(canonical.reserve_accounting)
    if result['physical'] is not None and not result['actual_inflight_unknown']and first is None and not save_errors and result.get('fullstate_prefix_before_contact',{}).get('complete')is True and result.get('independent_allocation',{}).get('passed')is True:
     replaying=True
     def replay_once():
      phases.transition('own_fullstate_replay');end=phases.budget.deadlines()
      evidence_quota.admit(65536,'OWN_REPLAY_PROGRESS_AND_RESULT');return replay(v,end['absolute_deadline_unix'],out/'physics')
     proof=attempt('OWN_FULL_STATE_REPLAY',replay_once)
     if proof is not None:replaying=False;result.update(replay=proof,own_replay_native=proof['replay_native'])
   result.update(own_replay_native=None if replaying else result['own_replay_native'],own_replay_inflight_unknown=replaying,closed=True,save_errors=save_errors,wall_s=time.monotonic()-started,source_unchanged=all(sha(R/n)==h for n,h in approval['tested_source_hashes'].items()),physical_admission=False,evidence_quota_open_holds=dict(evidence_quota.holds),initializer_and_ROS_writer_source_qualified_full_route_runtime_not_yet_verified=True)
   # Full independent route source/coverage/allocation/pair audits are a separate
   # required stage. An exited owner or saved prefix is not navigation PASS.
   result['native_Mesa_cache_disabled']=os.environ.get('MESA_SHADER_CACHE_DISABLE')=='true'
   result['native_Mesa_cache_members']=[str(path.relative_to(out))for path in out.rglob('mesa_shader_cache*')]
   if not result['native_Mesa_cache_disabled']or result['native_Mesa_cache_members']:save_errors.append(dict(stage='NATIVE_MESA_OUTPUT_COVERAGE',error='Native cache must remain disabled and absent'))
   result['shared_phase_accounting']=attempt('SAVE_NATIVE_PHASE_HANDOFF',phases.finish)
   attempt('SAVE_NATIVE_RESULT',lambda:atomic(out/'RESULT.json',result))
   if save_errors:os.write(2,(json.dumps(dict(first_error=first,secondary_save_errors=save_errors,evidence_gap=True),allow_nan=False)+'\n').encode())
 return result


def run(task,approval,window):
 qualification=admit(task,approval,window)
 caches=exact('v1449_frozen_initializer_cache',R/'experiments/v1447_full_module_guard_identity/task_cache.py')
 guards=exact('v1449_frozen_original_guard_binding',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
 # This source cannot infer initialization success from a software entry pass.
 closed=read(R/'runs/v1454_bounded_gzip_closure/CLOSED_REVIEW.json');assert closed['passed']and closed['actual_native']==closed['independent_allocator_recomputations']==closed['own_replay_native']==200 and closed['maximum_replay_fullstate_ctrl_mocap_error']==0.,'ACTUAL_CLOSURE_PATH_NOT_QUALIFIED'
 initialized=read(R/'runs/v1447_full_module_guard_identity/COMPLETION.json')
 assert initialized['passed']is True and initialized['native']['passed']is True and initialized['native']['actual_native']==0,'CANONICAL_INITIALIZER_RUNTIME_NOT_QUALIFIED'
 with caches.TaskLocalCaches(task['output']),guards.bind_original_guard(task['output'])as receipt:
  value=_bounded_run(task,approval,window)
  assert receipt['installed_original_guard_count']==1,'CANONICAL_ROUTE_ORIGINAL_GUARD_NOT_BOUND'
  return value

def _bounded_run(task,approval,window):
 qualification=admit(task,approval,window);out=Path(task['output'])
 quota_module=exact('v1432_actual_pre_wire_byte_quota',C/'quota.py');quota=quota_module.EvidenceQuota(out,qualification['limits'])
 registry=read(out/'EXTERNAL_WRITER_RESERVATIONS.json');assert registry['source_identity']==approval['qualification_sha256']and registry['approval_sha256']==sha(out/'APPROVAL.json')
 assert set(registry['writers'])=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}
 quota.external_writers=[]
 for role,row in registry['writers'].items():
  assert row['source_hook_coverage_qualified']is True
  key='external:'+role;quota.hold(key,row['maximum_bytes']);quota.external_writers.append(dict(name=role,reservation_key=key,remaining_byte_cap=row['maximum_bytes'],source_and_byte_cap_verified=True,live=True))
 quota.bind_external_names(list(registry['writers']))
 boundary=exact('v1432_actual_native_output_interceptor',C/'bounded_io.py').OutputBoundary
 quota.write_enforcement_active=True
 try:
  with boundary(out,quota.charge_write):return _run(task,approval,window,quota)
 finally:quota.write_enforcement_active=False
