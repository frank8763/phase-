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
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
io=exact('v1421_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
owner_module=exact('v1421_canonical_owner',C/'canonical_owner.py')
pump_module=exact('v1421_actual_pump',C/'pump.py')
peer_module=exact('v1423_current_model_peer_lifecycle',C/'model_peer.py')

class NotAdmitted(RuntimeError):pass

def admit(task,approval,window):
 # Must fail here, before importing any physical factory or MuJoCo, until the
 # separate full route qualification and exact shared budget actually exist.
 path=O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json'
 if not path.is_file():raise NotAdmitted('ACTUAL_ROUTE_FULL_QUALIFICATION_AND_BUDGET_MISSING')
 qualification=read(path);assert qualification['passed']is True and qualification['physical_admission']is True
 assert approval['scope']=='ACTUAL_ROUTE_EVENT_WITNESS'and approval['models_authorized']is True
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']==approval['round_id']and parent['models_now_authorized']
 original=next(t for t in read(R/'experiments/v1370_overnight_controller_matrix/TASKS.json')if t['task_id']=='rpp_default_horizon_m1_s01_main')
 remapped={'task_id','run_id','output','run_root','native_limit','depends_on','role'}
 assert task['role']==task['task_id']and task['role']in {'main','repeat'}
 assert {k:v for k,v in task.items()if k not in remapped}=={k:v for k,v in original.items()if k not in remapped}
 assert approval['qualification_sha256']==sha(path)and qualification['tested_source_hashes']==approval['tested_source_hashes']
 assert all(sha(R/n)==h for n,h in approval['tested_source_hashes'].items())
 assert window['boot_id']==parent['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert window['absolute_deadline_unix']<=1795395600 and window['hard_stop_monotonic']<=parent['hard_stop_monotonic']
 assert sorted(os.sched_getaffinity(0))==[2]and os.environ.get('PHASE_REPO')==str(R)and os.environ.get('CUDA_VISIBLE_DEVICES')==''
 assert not(R/'REVIEW_PENDING').exists()
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
 qualification=admit(task,approval,window);out=Path(task['output']);limits=qualification['limits'];v=None;canonical=None;pump=None;modeled=None;creating=False;replaying=False;first=None;save_errors=[];journal=None;capture=None
 quota_module=exact('v1432_actual_pre_wire_quota',C/'quota.py')
 capture_module=exact('v1431_complete_physical_capture_budget',C/'capture_budget.py')
 def atomic(path,value):
  if Path(path).name in {'FIRST_ERROR.json','TRANSACTION_ERROR.json','CUSP_BIND_ERROR.json','ERROR_STOP_TAIL.json'}:return evidence_quota.error_atomic(path,value,io.atomic)
  return evidence_quota.atomic(path,value,io.atomic)
 result=dict(passed=False,closed=False,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,own_replay_native=0,new_actual_native=0,actual_inflight_unknown=False,historical_controls_used=0)
 started=time.monotonic();next_storage=0.
 def remaining():
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==window['boot_id']
  return min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())
 def check(stage,requested):
  nonlocal next_storage
  assert remaining()>limits['finalization_reserve_s'],'ACTUAL_ROUTE_DUAL_CLOCK_RESERVE'
  if v is not None:
   if capture is not None and requested:capture.update(v,requested_native=requested)
   cap=limits['maximum_actual_native']-(0 if stage=='ACTUAL_STOP_TAIL'else 200)
   assert v.count+requested<=cap,'ACTUAL_ROUTE_NATIVE_BUDGET'
  # Byte snapshots are prepared by Pump.publish before a fresh actual wire;
  # each write is charged by OutputBoundary, never by a hot full-tree walk.

 def attempt(stage,fn):
  try:return fn()
  except BaseException as exc:save_errors.append(dict(stage=stage,error=repr(exc)));return None
 def stop(*_):raise TimeoutError('ACTUAL_ROUTE_HARD_STOP_SAVE_PREFIX')
 signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.setitimer(signal.ITIMER_REAL,max(.01,remaining()-5))
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   check('INITIALIZATION',0);evidence_quota.admit(16*1024**2,'CANONICAL_INITIALIZER_FILE_HEADROOM');old,Adapter,factory,replay=physical_binding(out);np=old.np
   creating=True;atomic(out/'INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),physical_native=0))
   import mujoco as mj
   saves=exact('v1432_native_model_file_admission',C/'bounded_io.py')
   with saves.native_model_saves(mj,evidence_quota.charge_write):v=factory.create_vehicle(out/'physics',task)
   creating=False;result['canonical_vehicle_initializations']=1;old.pin();capture=capture_module.CaptureBudget(evidence_quota);capture.update(v)
   import mujoco as mj
   assert v.count==0 and v.d.time==0.
   before=owner_module.native_module.state_digest(v);previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
   assert owner_module.native_module.state_digest(v)==before
   journal=(out/'ACTUAL_OWNER_JOURNAL.jsonl').open('x',buffering=1)
   def append(row):
    encoded=json.dumps(row,separators=(',',':'),allow_nan=False)+'\n';evidence_quota.admit(2*len(encoded.encode())+16384,'ROOT_ACTUAL_OWNER_RECEIPT');journal.write(encoded);journal.flush()
   modeled=peer_module.EventPeer(out,run_id=task['run_id'],check_budget=check,atomic=atomic)
   canonical=owner_module.CanonicalOwner(v,task=task,output=out,setup=read(out/'physics/SETUP.json'),authority=approval,lock=lock,budget=dict(generation_native=0,audit_native=0,generation_inflight_unknown=False,audit_inflight_unknown=False),limits=limits['witness'],reserve_accounting=dict(analytical_native=0,predictor_constructions=0,analytical_inflight_unknown=False,construction_inflight_unknown=False),reserve_limits=limits['current_reserve'],atomic=atomic,np=np,peer_command=modeled.command,peer_replies=modeled.replies,check_budget=check,quota=evidence_quota)
   # All private generation/audit/reserve must leave the same finalization reserve.
   private_deadline=dict(approval,absolute_deadline_unix=window['absolute_deadline_unix']-limits['finalization_reserve_s'],hard_stop_monotonic=window['hard_stop_monotonic']-limits['finalization_reserve_s'])
   canonical.authority=private_deadline
   canonical.transaction.authority=private_deadline
   evidence_quota.save_npz(out/'INITIAL_FULL_STATE.npz',dict(time=np.asarray([v.d.time]),**{k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}),np)
   atomic(out/'INITIAL_PACKET.json',canonical.native.packet(None));pump=pump_module.Pump(canonical,check_budget=check,append=append,model_peer=modeled)
   while not pump.stopped:pump.iteration()
   evidence_quota.retire_grant();evidence_quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=evidence_quota.external_writers)
   for _ in range(200):
    if canonical.native.bridge_started:
     check('ACTUAL_STOP_TAIL',1);canonical.native.apply(0.,0.,phase='COMPLETE_STOP_TAIL',control_owner='APPLIED_STOP_TAIL',delivery=None,stop_tail=True)
    else:pump.prefix_step(None,stop_tail=True)
   canonical.envelope();body=list(v.body());distance=math.dist(body[:2],task['goal_xy']);progress=sum((body[i]-task['start_xy'][i])*[math.cos(task['start_yaw']),math.sin(task['start_yaw'])][i]for i in range(2))
   result['functional_checks']=dict(original_action_succeeded=pump.ros_pass,whole_goal_distance=distance<=.45,whole_forward_progress=progress>=7.5,body_stopped=max(abs(x)for x in body[3:])<=.03,steering_settled=max(abs(x)for x in v.steering_sample()[2:])<=.03,drive_zero=max(abs(x)for x in v.adapter.last[2:])<=1e-8,complete200_applied_zero_tail=canonical.native.last_zero_count>=200)
   result.update(whole_goal_distance_m=distance,whole_forward_progress_m=progress,functional_passed=all(result['functional_checks'].values()),independent_complete_route_audit_required=True)
  except BaseException as exc:
   first=dict(error=repr(exc),traceback=traceback.format_exc());attempt('SAVE_FIRST_ERROR',lambda:atomic(out/'FIRST_ERROR.json',first))
   if pump is not None and canonical is not None and not pump.prefix_inflight and not canonical.native.in_step:
    try:
     evidence_quota.retire_grant();evidence_quota.prepare_grant(32*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=300,external_writers=evidence_quota.external_writers)
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
   if modeled is not None:attempt('CLOSE_MODELED_PEER',modeled.close_event)
   if pump is not None:attempt('CLOSE_ACTUAL_SOCKET',pump.close)
   if canonical is not None:attempt('CLOSE_CANONICAL_OWNER',canonical.close)
   if journal is not None:attempt('CLOSE_ACTUAL_JOURNAL',journal.close)
   inflight=bool((pump is not None and pump.prefix_inflight)or(canonical is not None and canonical.native.in_step))
   result.update(first_error=first,canonical_vehicle_initializations=None if creating else result['canonical_vehicle_initializations'],new_actual_native=None if inflight else(0 if v is None else v.count),actual_inflight_unknown=inflight)
   if v is not None:
    result['physical']=attempt('SAVE_PHYSICAL_PREFIX',lambda:capture.finish(v))
    if result['physical']is not None and not result['actual_inflight_unknown']:
     def audit_allocation():
      recorded=exact('v1423_complete_receipt_normalizer',R/'experiments/v1423_integrated_route_audit/recorded.py');allocation=exact('v1431_bound_allocator_audit',R/'experiments/v1430_actual_allocator_provenance/allocation.py')
      allrows,_,_=recorded.collect(out)
      with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as initial_stream:initial_source={k:initial_stream[k].copy()for k in initial_stream.files}
      proof=allocation.audit(v,allrows,read(out/'INITIAL_PACKET.json'),Adapter=Adapter,mj=mj,np=np,lock=lock,initial_fullstate=initial_source,setup=read(out/'physics/SETUP.json'),save=lambda value:atomic(out/'INDEPENDENT_ALLOCATION.json',value),maximum_recomputations=limits['maximum_allocator_recomputations'],deadline_unix=min(time.time()+120,window['absolute_deadline_unix']-limits['replay_wall_s']-120),deadline_monotonic=min(time.monotonic()+120,window['hard_stop_monotonic']-limits['replay_wall_s']-120))
      return proof
     result['independent_allocation']=attempt('INDEPENDENT_ALLOCATION_RECOMPUTATION',audit_allocation)
    if canonical is not None:result['canonical_accounting']=canonical.native.exact_accounting();result['model_generation_and_audit_accounting']=dict(canonical.transaction.budget);result['current_reserve_accounting']=dict(canonical.reserve_accounting)
    if result['physical'] is not None and not result['actual_inflight_unknown']and remaining()>limits['replay_reserve_s']:
     replaying=True
     def replay_once():
      evidence_quota.admit(65536,'OWN_REPLAY_PROGRESS_AND_RESULT');return replay(v,min(time.time()+limits['replay_wall_s'],window['absolute_deadline_unix']),out/'physics')
     proof=attempt('OWN_FULL_STATE_REPLAY',replay_once)
     if proof is not None:replaying=False;result.update(replay=proof,own_replay_native=proof['replay_native'])
   result.update(own_replay_native=None if replaying else result['own_replay_native'],own_replay_inflight_unknown=replaying,closed=True,save_errors=save_errors,wall_s=time.monotonic()-started,source_unchanged=all(sha(R/n)==h for n,h in approval['tested_source_hashes'].items()),physical_admission=False,evidence_quota_open_holds=dict(evidence_quota.holds),initializer_and_ROS_child_byte_enforcement_not_qualified=True)
   # Full independent route source/coverage/allocation/pair audits are a separate
   # required stage. An exited owner or saved prefix is not navigation PASS.
   atomic(out/'RESULT.json',result)
 return result


def run(task,approval,window):
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
