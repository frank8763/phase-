"""One new zero-model production phase/close gate qualification.

Windows and owner fields are explicitly software inputs. No vehicle, measured
wire, response model, synthetic scan, old numeric branch or replay is created.
"""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('PHASE_QUALIFICATION_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'PHASE_QUALIFICATION.json').exists()and not(O/'ENTRY_CLOSED.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('PHASE_PROFILE_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 life=exact('v1437_actual_lifecycle_under_zero_model_guard',C/'lifecycle.py');phase=life.phase_module
 limits=json.loads((C/'LIMITS.json').read_text());exact('v1437_actual_limits',C/'budget.py').limits_check(limits)
 def window(age=0.):
  now=time.time();mono=time.monotonic();return dict(started_unix=now-age,started_monotonic=mono-age,absolute_deadline_unix=now-age+5400,hard_stop_monotonic=mono-age+5400,boot_id=parent['boot_id'])
 def runtime(name,age=0.):return phase.PhaseRuntime(window(age),limits,lambda value:life.io.atomic(O/(name+'.json'),value))
 negatives=[];active=[]
 def reject(label,fn,contains=None):
  try:fn()
  except (AssertionError,RuntimeError,OSError)as exc:
   if contains is not None:assert contains in str(exc),(label,repr(exc))
   negatives.append(dict(case=label,error=repr(exc)));return
  raise AssertionError('PHASE_NEGATIVE_ACCEPTED:'+label)
 def alarm(*_):raise TimeoutError('PHASE_QUALIFICATION_ACTUAL_ALARM')
 previous=signal.signal(signal.SIGALRM,alarm)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   normal=runtime('healthy_native');active.append(normal);normal.transition('normal')
   car=SimpleNamespace(count=39800);gate=phase.NativePhaseGate(normal,limits,lambda:car,lambda:None)
   reject('normal_native_cap_preserves200',lambda:gate('ACTUAL_NATIVE',1),'ACTUAL_ROUTE_NATIVE_BUDGET')
   reject('stop_not_allowed_during_normal',lambda:gate('ACTUAL_STOP_TAIL',1),'WRONG_EXECUTION_PHASE')
   reject('unknown_execution_stage',lambda:gate('UNREGISTERED',0),'UNKNOWN_NATIVE_BUDGET_STAGE')
   reject('non_action_stage_requested_native',lambda:gate('PUMP',1),'NON_ACTION_STAGE_REQUESTED_NATIVE')
   reject('negative_native_count',lambda:gate('ACTUAL_NATIVE',-1),'INVALID_NATIVE_COUNT_REQUEST')
   gate('PUMP',0)
   for name in ['complete_zero_tail','peer_close','allocator_recompute','own_fullstate_replay']:normal.transition(name)
   native_handoff=normal.finish();supervisor=phase.m.PhaseBudget(normal.budget.window,limits);supervisor.restore(native_handoff)
   for name in ['recorded_audit','main_repeat_pair','final_metadata']:supervisor.enter(name);supervisor.check();supervisor.leave()
   assert len(supervisor.records)==8 and all(r['completed_within_phase_bound']for r in supervisor.records)
   life.io.atomic(O/'SOFTWARE_SHARED_PHASE_HANDOFF.json',supervisor.snapshot())
   expired=runtime('expired_normal_then_stop',4141.);active.append(expired)
   reject('expired_normal_refused',lambda:expired.transition('normal'),'PHASE_RESERVED_FUTURE_EXHAUSTED')
   expired.transition('complete_zero_tail');stopgate=phase.NativePhaseGate(expired,limits,lambda:car,lambda:None);stopgate('ACTUAL_STOP_TAIL',1)
   reject('ordinary_action_forbidden_during_stop',lambda:stopgate('ACTUAL_NATIVE',1),'WRONG_EXECUTION_PHASE')
   car.count=40000;reject('stop_cannot_exceed_total40000',lambda:stopgate('ACTUAL_STOP_TAIL',1),'ACTUAL_ROUTE_NATIVE_BUDGET');car.count=39800
   source=dict(input_sha256='0'*64,causal_snapshot_sha256='1'*64,maximum_analytical_native=8000000,maximum_predictor_constructions=40000,**expired.budget.boundary('normal'))
   reserve=SimpleNamespace(authority=dict(source,current_input_sha256='0'*64),current={'input_sha256':'0'*64},snapshot_sha256='1'*64,accounting={'analytical_native':200},snapshot={'software_only':True},fixed_reference=['immutable-software-marker'])
   owner=SimpleNamespace(native=SimpleNamespace(vehicle=car,reserve=reserve),authority=copy.deepcopy(source),transaction=SimpleNamespace(authority=copy.deepcopy(source)))
   before=copy.deepcopy(owner);proof=phase.bind_stop_authority(owner,expired)
   clocks={'absolute_deadline_unix','hard_stop_monotonic','boot_id'}
   assert {k:v for k,v in owner.authority.items()if k not in clocks}=={k:v for k,v in before.authority.items()if k not in clocks}
   assert reserve.current==before.native.reserve.current and reserve.accounting==before.native.reserve.accounting and reserve.snapshot==before.native.reserve.snapshot and reserve.fixed_reference==before.native.reserve.fixed_reference
   assert car.count==before.native.vehicle.count and owner.transaction.authority==before.transaction.authority
   reject('stop_authority_cannot_rebind',lambda:phase.bind_stop_authority(owner,expired),'STOP_AUTHORITY_ALREADY_BOUND')
   transaction=life.owner_module.transaction_module.CuspTransaction
   reject('actual_transaction_refuses_stop_before_binding',lambda:transaction.run(owner.transaction,{}),'NEW_EVENT_FORBIDDEN_DURING_STOP_PHASE')
   life.io.atomic(O/'SOFTWARE_STOP_CLOCK_BINDING.json',dict(proof=proof,source_fields_and_counts_and_snapshot_reference_unchanged=True,new_generation_authority_not_extended=True,not_actual_owner_or_certificate=True))
   ended=expired.finish();reject('expired_native_handoff_cannot_pass_success_audit',lambda:phase.m.PhaseBudget(expired.budget.window,limits).restore(ended),'EXPIRED_NATIVE_PHASE_CANNOT_ENTER_SUCCESS_AUDIT')
   rewind=runtime('rewind');active.append(rewind);rewind.transition('complete_zero_tail');reject('phase_cannot_rewind',lambda:rewind.transition('normal'),'PHASE_REENTRY_OR_REWIND')
   bad=window();bad['hard_stop_monotonic']-=1;reject('dual_clock_duration_changed',lambda:phase.m.PhaseBudget(bad,limits))
   bad=window();bad['boot_id']='wrong';reject('foreign_boot_refused',lambda:phase.m.PhaseBudget(bad,limits).enter('normal'))
   def save_failure(_):raise OSError('SOFTWARE_SECONDARY_PHASE_SAVE')
   secondary=phase.PhaseRuntime(window(4141.),limits,save_failure);active.append(secondary)
   reject('secondary_save_preserves_expiry_first',lambda:secondary.transition('normal'),'PHASE_RESERVED_FUTURE_EXHAUSTED')
   assert secondary.secondary_save_errors and signal.getitimer(signal.ITIMER_REAL)[0]>0
   close=runtime('actual_close_software_receipt');active.append(close);close.transition('peer_close')
   folder=O/'actual_socket_close';folder.mkdir();software_owner=SimpleNamespace(output=folder,native=SimpleNamespace(run_id='V1437_SOFTWARE_CLOSE'),atomic=life.io.atomic)
   pump=life.pump_module.Pump(software_owner,check_budget=lambda *_:None,append=lambda _:None,model_peer=None)
   pump.close();assert not Path(pump.address).exists()and json.loads((folder/'PEER_STOP_REQUEST.json').read_text())['no_native_action']is True
   receipt=folder/'ROS_RESULT.json';life.io.atomic(receipt,dict(closed=True,controller_server_exited=False,evidence_write_errors=[]))
   reject('controller_incomplete_close_refused',lambda:phase.wait_actual_ROS_close(folder,close),'ACTUAL_ROS_CONTROLLER_CLOSE_INCOMPLETE')
   life.io.atomic(receipt,dict(closed=True,controller_server_exited=True,evidence_write_errors=[dict(error='SOFTWARE_WRITE_ERROR')]))
   reject('close_evidence_gap_refused',lambda:phase.wait_actual_ROS_close(folder,close),'ACTUAL_ROS_CLOSE_EVIDENCE_GAP')
   life.io.atomic(receipt,dict(software_only=True,closed=True,controller_server_exited=True,evidence_write_errors=[]));assert phase.wait_actual_ROS_close(folder,close)['software_only']
   close.finish()
   assert parent_path.read_bytes()==parent_before
   assert not(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()
   result=dict(passed=True,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,software_windows_and_owner_fields_only=True,normal_cutoff_to_reserved_stop_gate_exercised=True,actual_production_NativePhaseGate_and_stop_transaction_refusal=True,source_snapshot_reference_counts_preserved_in_software_binding=True,shared8stage_handoff_roundtrip=True,root_alarm_live_on_phase_save_failure=True,actual_Pump_Unix_socket_close_flag_exercised=True,close_receipts_explicitly_software_not_actual_ROS=True,negative_cases=negatives,complete_route_admission_absent=True,physical_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
   life.io.atomic(O/'PHASE_QUALIFICATION.json',result);print(json.dumps(result))
  finally:
   signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)

if __name__=='__main__':main()
