"""New actual native driver; scope authorization precedes physical lazy binding.

Qualified originals supply factory/Adapter/state-first/contact serialization,
Allocator and applied-control replay. New owner/Pump remain explicit sources.
"""
import ast
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def physical_binding(output):
 import numpy as np
 from types import SimpleNamespace
 bound=exact('v1423_complete_frozen_adapter_binding',R/'experiments/v1115_coupled_complete_source/bindings.py');Adapter=bound.Adapter
 pinpath=R/'experiments/v1179_frozen_recovery_native/recovery_tools.py';pin=next(x for x in ast.parse(pinpath.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='pin');scope=dict(Path=Path,os=os);exec(compile(ast.Module(body=[pin],type_ignores=[]),str(pinpath),'exec'),scope);old=SimpleNamespace(np=np,pin=scope['pin'])
 factory=exact('v1423_canonical_scene_factory',R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py');factory.O=output.parent
 replay=exact('v1423_exact_applied_control_replay',R/'experiments/v882_runtime_evidence_repair/physical.py').replay
 assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
 return old,Adapter,factory,replay


def run(task,window):
 life=exact('v1606_new_actual_lifecycle',C/'lifecycle.py');authority,source=life.authorize(task,window)
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)
 out=Path(task['output']);limits=read(C/'LIMITS.json');assert limits==authority['limits']
 caches=life.exact('v1606_frozen_task_cache',R/'experiments/v1447_full_module_guard_identity/task_cache.py',source)
 guards=life.exact('v1606_immutable_original_guard',R/'experiments/v1447_full_module_guard_identity/guard_binding.py',source)
 with caches.TaskLocalCaches(out),guards.bind_original_guard(out):
  quota_module=life.exact('v1606_original_pre_wire_quota',C/'quota.py',source)
  quota=quota_module.EvidenceQuota(out,limits)
  registry=read(out/'EXTERNAL_WRITER_RESERVATIONS.json')
  assert registry['source_identity']==authority['qualification_sha256']and registry['approval_sha256']==sha(out/'APPROVAL.json')
  assert set(registry['writers'])=={'ACTUAL_ROS','PLANNER','SUPERVISOR_LOG'}
  quota.external_writers=[]
  for role,row in registry['writers'].items():
   assert row['source_hook_coverage_qualified']is True
   key='external:'+role;quota.hold(key,row['maximum_bytes'])
   quota.external_writers.append(dict(name=role,reservation_key=key,remaining_byte_cap=row['maximum_bytes'],source_and_byte_cap_verified=True,live=True))
  quota.bind_external_names(list(registry['writers']));quota.write_enforcement_active=True
  boundary=life.exact('v1606_native_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py',source).OutputBoundary
  try:
   with boundary(out,quota.charge_write) as root_boundary:
    quota.output_boundary=root_boundary
    return execute(task,window,authority,source,quota,life)
  finally:quota.write_enforcement_active=False


def phase_limits(authority):
 # JSON authority is content-bound, not insertion-order-bound. The immutable
 # registered LIMITS supplies the original stage order; no value changes.
 limits=read(C/'LIMITS.json')
 assert limits==authority['limits'],'ACTUAL_LIMITS_CONTENT_CHANGED'
 return limits


def execute(task,window,authority,source,quota,life):
 out=Path(task['output']);limits=phase_limits(authority);v=None;canonical=None;pump=None;capture=None;journal=None;owner=None
 creating=False;replaying=False;first=None;secondary=[];started=time.monotonic();np=None;Adapter=None;mj=None;replay=None
 result=dict(passed=False,closed=False,first_error=None,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,
  actual_native=0,actual_inflight_unknown=False,own_replay_native=0,own_replay_inflight_unknown=False,
  whole_route_passed=False,partial_navigation_attempt=True,shared_bridge_disclosed=True)
 evidence=life.exact('v1606_original_atomic_evidence',R/'experiments/v1383_exact_timed_handoff/evidence_io.py',source)
 def atomic(path,value):
  if Path(path).name in {'FIRST_ERROR.json','ERROR_STOP_TAIL.json'}:return quota.error_atomic(path,value,evidence.atomic)
  return quota.atomic(path,value,evidence.atomic)
 phase_module=life.exact('v1606_original_shared_phases',R/'experiments/v1449_route_initializer_binding/phase_runtime.py',source)
 phases=phase_module.PhaseRuntime(window,limits,lambda p:atomic(out/'NATIVE_PHASES.json',p))
 gate=phase_module.NativePhaseGate(phases,limits,lambda:v,lambda:capture)
 startup=life.exact('v1606_original_ready_handoff',R/'experiments/v1479_retirement_scope_binding/startup.py',source)
 def check(stage,count):
  startup.check_native_stop(out,run_id=task['run_id'],source_identity=authority['qualification_sha256']);gate(stage,count)
 def attempt(stage,fn):
  try:return fn()
  except BaseException as error:
   secondary.append(dict(stage=stage,error=repr(error)))
   try:phases.arm_root()
   except BaseException as clock:secondary.append(dict(stage=stage+'_ROOT_CLOCK',error=repr(clock)))
   return None
 def stop(*_):raise TimeoutError('GOAL_BOUND_ACTUAL_ROOT_OR_PHASE_STOP')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   phases.transition('normal');check('INITIALIZATION',0)
   quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_PREPARATION',valid_for_s=180,external_writers=quota.external_writers)
   old,Adapter,factory,replay=physical_binding(out);np=old.np
   creating=True;atomic(out/'INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),actual_native=0))
   import mujoco as mj
   bounded=life.exact('v1606_original_native_model_save',R/'experiments/v1436_pathlib_control_rename/bounded_io.py',source)
   end=startup.initializer_deadlines(window,phases.budget.deadlines(),cap_s=180)
   signal.setitimer(signal.ITIMER_REAL,max(.001,min(end['absolute_deadline_unix']-time.time(),end['hard_stop_monotonic']-time.monotonic())))
   with bounded.native_model_saves(mj,quota.charge_write):v=factory.create_vehicle(out/'physics',task)
   creating=False;result['canonical_vehicle_initializations']=1;phases.arm(phases.budget.deadlines());check('INITIALIZATION',0)
   old.pin();capture_module=life.exact('v1606_original_complete_capture',R/'experiments/v1454_bounded_gzip_closure/capture_budget.py',source)
   capture=capture_module.CaptureBudget(quota);capture.update(v)
   before={k:getattr(v.d,k).copy()for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat')}
   previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
   assert all(np.array_equal(before[k],getattr(v.d,k))for k in before)
   owner=life.Lifecycle(task=task,window=window,lock=lock,atomic=atomic,quota=quota,check_budget=check)
   canonical=owner.bind_initialized_t0(v,read(out/'physics/SETUP.json'))
   quota.save_npz(out/'INITIAL_FULL_STATE.npz',dict(time=np.asarray(v.d.time),**{k:np.asarray(getattr(v.d,k)).copy()for k in before}),np)
   atomic(out/'INITIAL_PACKET.json',canonical.native.packet(None))
   journal=(out/'ACTUAL_OWNER_JOURNAL.jsonl').open('x',buffering=1)
   def append(row):
    raw=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n';quota.admit(2*len(raw.encode())+16384,'ROOT_ACTUAL_RECEIPT');journal.write(raw);journal.flush()
   pump_module=life.exact('v1606_actual_prefix_and_bridge_pump',C/'pump.py',source)
   pump=pump_module.Pump(canonical,check_budget=check,append=append)
   startup.emit_ready(v,canonical,out,run_id=task['run_id'],source_identity=authority['qualification_sha256'],atomic=atomic)
   while not pump.stopped:pump.iteration()
   assert canonical.bridge is not None and canonical.bridge.closed,'GOAL_BOUND_CURRENT_EVENT_NOT_COMPLETED'
   assert canonical.native.last_zero_count>=2200
   result['actual_goal_bound_segment_completed']=True
  except BaseException as error:
   first=dict(error=repr(error),traceback=traceback.format_exc());result['first_error']=first
   close_resources=life.exact('v1606_close_resource_preparation',C/'closure_resources.py',source)
   if quota is not None:attempt('PREPARE_FAILURE_RESOURCE_GRANT',lambda:close_resources.prepare(quota))
   attempt('SAVE_FIRST_ERROR',lambda:atomic(out/'FIRST_ERROR.json',first))
   # A refused current certificate is not retried and no uncertified bridge
   # action is added. Before the event, the original bounded error zero tail
   # remains available; all failure/nonexecuted tail status stays explicit.
   if pump is not None and canonical is not None and not canonical.native.bridge_started and not pump.prefix_inflight:
    def original_error_tail():
     close_resources.prepare(quota);phases.transition('complete_zero_tail')
     for _ in range(200):pump.prefix_step(None,stop_tail=True)
     return dict(actual_zero_tail_native=200)
    result['error_tail']=attempt('ORIGINAL_PREFIX_ERROR_ZERO_TAIL',original_error_tail)
  finally:
   close_resources=life.exact('v1606_final_resource_preparation',C/'closure_resources.py',source)
   attempt('CLOSE_BYTE_GRANT',lambda:close_resources.prepare(quota))
   attempt('ENTER_CLOSE',lambda:phases.transition('peer_close'))
   if pump is not None:attempt('CLOSE_ACTUAL_SOCKET',pump.close)
   if pump is not None:attempt('WAIT_ACTUAL_ROS_CLOSE',lambda:phase_module.wait_actual_ROS_close(out,phases))
   if owner is not None:attempt('CLOSE_NEW_CANONICAL_OWNER',owner.close)
   if journal is not None:attempt('CLOSE_ROOT_JOURNAL',journal.close)
   inflight=bool(pump is not None and pump.prefix_inflight)or bool(canonical is not None and canonical.native.in_step)
   result.update(canonical_vehicle_initializations=None if creating else result['canonical_vehicle_initializations'],
    actual_native=None if inflight else(0 if v is None else v.count),actual_inflight_unknown=inflight)
   if v is not None:
    def save_state():
     state=life.exact('v1606_original_state_first_capture',R/'experiments/v1479_retirement_scope_binding/state_capture.py',source)
     with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as s:initial={k:s[k].copy()for k in s.files}
     return state.save_current_prefix(v,initial,out,quota,np)
    result['fullstate_prefix']=attempt('SAVE_STATE_BEFORE_CONTACT',save_state)
    if capture is not None and not capture.finish_attempted:result['physical']=attempt('SAVE_PHYSICAL',lambda:capture.finish(v))
    if canonical is not None:result['actual_accounting']=canonical.native.exact_accounting()
    if owner is not None and owner.components is not None:result['private_current_accounting']=owner.components.guard.counts()
    # New recorded schema is explicit; original collect()'s old200 event
    # layout is never used to claim integrated success.
    if first is None and not secondary and result.get('physical')is not None and result.get('fullstate_prefix',{}).get('complete'):
     def allocator():
      phases.transition('allocator_recompute');end=phases.budget.deadlines()
      recorded=life.exact('v1606_new_recorded_schema',C/'recorded.py',source);rows,_,_=recorded.collect(out,source=source)
      allocation=life.exact('v1606_original_actual_source_Allocator',R/'experiments/v1430_actual_allocator_provenance/allocation.py',source)
      with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as s:initial={k:s[k].copy()for k in s.files}
      return allocation.audit(v,rows,read(out/'INITIAL_PACKET.json'),Adapter=Adapter,mj=mj,np=np,lock=lock,initial_fullstate=initial,
       setup=read(out/'physics/SETUP.json'),save=lambda p:atomic(out/'INDEPENDENT_ALLOCATION.json',p),maximum_recomputations=40000,
       deadline_unix=end['absolute_deadline_unix'],deadline_monotonic=end['hard_stop_monotonic'])
     result['independent_allocation']=attempt('ALLOCATOR_RECOMPUTATION',allocator)
     if result.get('independent_allocation',{}).get('passed'):
      def own_replay():
       phases.transition('own_fullstate_replay');return replay(v,phases.budget.deadlines()['absolute_deadline_unix'],out/'physics')
      replaying=True;proof=attempt('OWN_FULLSTATE_REPLAY',own_replay)
      if proof is not None:replaying=False;result['own_replay_native']=proof['replay_native'];result['replay']=proof
      if proof is not None and proof.get('passed')and owner.components is not None and not secondary:
       def integrated_audit():
        phases.transition('recorded_audit')
        module=life.exact('v1606_complete_new_schema_audit',C/'actual_audit.py',source)
        result['source_unchanged']=all(sha(R/n)==h for n,h in source.items())
        review=module.integrated(task,result,components=owner.components,source=source,check=lambda:phases.check('recorded_audit'))
        atomic(out/'INDEPENDENT_INTEGRATED_AUDIT.json',review);return review
       result['integrated_audit']=attempt('INDEPENDENT_INTEGRATED_AUDIT',integrated_audit)
       result['passed']=bool(result.get('integrated_audit',{}).get('passed')and not secondary)
   result.update(own_replay_native=None if replaying else result['own_replay_native'],own_replay_inflight_unknown=replaying,
    closed=True,secondary_errors=secondary,wall_s=time.monotonic()-started,
    source_unchanged=all(sha(R/n)==h for n,h in source.items()),whole_route_passed=False)
   if (out/'goal_bound_private/TRANSACTION_RESULT.json').exists():
    result['private_transaction']=attempt('READ_PRIVATE_ACCOUNTING',lambda:read(out/'goal_bound_private/TRANSACTION_RESULT.json'))
   else:result['private_transaction']=None
   if first is not None or secondary or not result['source_unchanged']:result['passed']=False
   result['shared_phase_accounting']=attempt('NATIVE_PHASE_CLOSE',phases.finish)
   if secondary:result['passed']=False
   attempt('NATIVE_RESULT_SAVE',lambda:atomic(out/'RESULT.json',result))
   if secondary:os.write(2,(json.dumps(dict(first_error=first,secondary_errors=secondary,evidence_gap=True),allow_nan=False)+'\n').encode())
 return result
