"""One new goal-bound policy/current API/lifecycle SOURCE target only.

All numerical arrays and policy poses here are explicitly SOFTWARE. No model,
Gear.select, physical binding, ROS node, old qualifier or old suite executes.
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
import sys
import time
import traceback
from types import SimpleNamespace
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1577_source_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def main():
 start=time.monotonic();resources=c.bootstrap();c.guard()
 lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,
  optimizer_calls=0,Allocator_recomputations=0,phase_FFI_loads=0,actual_capture_qualified=False,actual_runtime_qualified=False)
 def profile(frame,event,arg):
  if event=='call':
   path=Path(frame.f_code.co_filename)
   if path.is_absolute()and path.is_relative_to(c.R):
    assert not(path.name in {'model.py','coupled_model.py','prediction.py','engine.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','simulate','compute'}),'SOURCE_TARGET_MODEL_OR_ALLOCATOR_FORBIDDEN'
    assert not('gear_handoff.py'in str(path)and frame.f_code.co_name=='select'),'SOURCE_TARGET_ORIGINAL_GEAR_FORBIDDEN'
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'},'SOURCE_TARGET_NUMERICAL_BINDING_FORBIDDEN'
 sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  target=c.O/'source_target';target.mkdir(exist_ok=False)
  writer_module=c.load('v1577_source_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
  io=c.load('v1577_source_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  writer=writer_module.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'))
  negative=[]
  def refused(name,fn):
   try:fn()
   except BaseException as e:negative.append(dict(name=name,error=repr(e)));return e
   raise AssertionError('GOAL_BOUND_NEGATIVE_ACCEPTED:'+name)
  with io.OutputBoundary(target,writer.reserve)as boundary:
   tracker=c.load('v1577_new_goal_policy_target',C/'tracker.py')
   cases=[]
   for gear,last in [(1,[1.,0.,0.]),(-1,[-1.,0.,0.])]:
    segment=dict(gear=gear,poses=[[0.,0.,0.],last]);policy=tracker.SegmentTracker(segment,origin_body=[.3,0.,0.,0.,0.],origin_native=0,origin_sim_time=0.)
    decision=policy.select([.3,0.,0.,0.,0.],native_tick=0,sim_time=0.)
    assert abs(decision['raw_row'][0])<=1e-14 and decision['raw_row'][1:]==[.08 if gear==1 else -.03,0]
    refused('policy_pending_not_reselected_'+str(gear),lambda:policy.select([.3,0.,0.,0.,0.],native_tick=5,sim_time=.05))
    policy.commit(decision,applied_native=5,applied_request_receipts_sha256='a'*64)
    fork=policy.fork();assert fork.progress==policy.progress and fork is not policy
    cases.append(dict(gear=gear,decision=decision,software_policy_only=True))
   refused('entry_pose_not_captured',lambda:tracker.SegmentTracker(dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]),origin_body=[.5,0.,0.,0.,0.],origin_native=0,origin_sim_time=0.))
   witness=c.load('v1577_variable_witness_source',C/'witness.py')
   assert witness.budget(8200)['full_phase_native']==5300800 and len(witness.boundaries(2200))==1
   refused('variable_non5_timing',lambda:witness.boundaries(2201))
   work=c.load('v1577_new_exact_work_source',C/'work.py')
   ledger=work.Work(native=2200,nominal=0,witness=2200,copies=0,engine=1,predictor=0,batch_calls=1)
   ledger.bucket('witness');ledger.construct('Engine');ledger.constructed('Engine');ledger.claim(1)
   refused('unacknowledged_not_retried',lambda:ledger.claim(1));assert ledger.counts()['inflight_unknown']
   ledger.acknowledge(1);ledger.claim(2199,batch=True);ledger.acknowledge(2199,batch=True);ledger.complete()
   refused('complete_native_cap',lambda:ledger.claim(1))
   guards=c.load('v1577_private_live_separation',C/'capability.py')
   refused('private_cannot_grant_live',lambda:guards.Guard.__new__(guards.Guard).require_live_component('CURRENT_CPP_RESERVE',{}))
   binder=c.load('v1577_current_source_first_error',C/'current_input.py')
   registration=c.read(c.O/'SCIENTIFIC_REVISION_REGISTRATION.json');saved=[]
   error=refused('legacy_saved_input_not_current',lambda:binder.describe(dict(role='SAVED_ACTUAL_INPUT_MODEL_ONLY'),{}, {},registration=registration,
    registration_sha256=binder.digest(registration),source_manifest_sha256=c.sha(C/'entry.py'),save_proof=saved.append))
   assert saved and saved[0]['passed']is False and error.proof==saved[0]
   def denied(_):raise OSError('SOFTWARE_SOURCE_PROOF_WRITE_DENIED')
   error=refused('first_secondary_separate',lambda:binder.describe({}, {}, {},registration={},registration_sha256='0'*64,source_manifest_sha256='0'*64,save_proof=denied))
   assert error.secondary and error.proof['first_error']
   # One new complete current-stream schema exercise. The codec itself is
   # reused by SHA; these zero-valued arrays are NOT a stopping trajectory.
   import numpy as np
   stream=c.load('v1577_variable_names_source',C/'stream.py');codec=stream.record_codec();shapes=codec.dimensions(2200)
   arrays={k:np.zeros(shape,dtype=np.int64 if k in codec.INTS else np.float64)for k,shape in shapes.items()}
   arrays['native'][:]=np.arange(100,2301);arrays['sim_time'][:]=.01*arrays['native']
   store=c.load('v1577_new_actual_current_store',C/'actual_sink.py')
   # ActualSink has its own original32MiB writer in a distinct declared scope.
   folder=target/'actual_software';folder.mkdir();small=writer_module.WriterBudget(folder,role='PLANNER',maximum_bytes=32*1024**2,source_identity=c.sha(C/'entry.py'))
   with io.OutputBoundary(folder,small.reserve)as current_boundary:
    sink=store.ActualSink(folder=folder,writer=small,boundary=current_boundary,source=source,
     method={'response_method_sha256':'b'*64},native=SimpleNamespace(applied=100,vehicle=SimpleNamespace(count=100)))
    packet=dict(native_tick=100,software_fixture=True);identity=c.digest(packet)
    sink.origin(dict(source_packet=packet,source_packet_sha256=identity,software_only=True))
    durable=sink.complete(arrays,dict(source_packet_sha256=identity,model_counts={'model_native':0,'software_arrays':True}))
    proof=dict(passed=False,source_packet_sha256=identity,before_native=100,complete_native=2200,software_not_safety_proof=True)
    sink.after_gate(proof,durable)
    refused('unsafe_proof_cannot_apply',lambda:sink.before(dict(before_native=100,source_packet_sha256=identity,applied=False),proof,arrays['states'],arrays['ctrl']))
    sink.close(dict(model_native=0,software_arrays_not_integrations=True))
   closed=c.read(folder/'CURRENT_CLOSED.json');assert closed['current_branches']==1 and closed['applied_receipts']==0
   assert hashlib.sha256((folder/'CURRENT.bin').read_bytes()).hexdigest()==closed['whole_stream_sha256']
   # Only new CLI/scope refusal and actual-source dependency wiring, no old
   # initializer/ROS/OS/numerical fixture or saved numerical rerun.
   life=c.load('v1577_production_scope_target',C/'lifecycle.py')
   refused('actual_not_admitted',lambda:life.run(c.read(C/'TASKS.json')[0],{}))
   owner=c.load('v1577_actual_once_predicate',C/'supervisor.py')
   refused('once_missing_complete_source',owner.launch)
   assert owner.runtime_passed(0,{'passed':True,'closed':True},[])is False
   assert owner.runtime_passed(1,None,[])is False
   # Exact immutable original writer/ROS-body proof reuse. Changed entry
   # context is tested above; no ROS node/controller is started here.
   old=(c.R/'experiments/v1574_current_owner_capture/route_ros.py').read_text()
   now=(C/'route_ros.py').read_text().replace("R/'experiments/v1574_current_owner_capture/causal_provider.py'","C/'causal_provider.py'").replace("R/'experiments/v1479_retirement_scope_binding/entry_boundary.py'","C/'entry_boundary.py'")
   assert ast.dump(ast.parse(old))==ast.dump(ast.parse(now))
   c.put(target/'QUALIFICATION.json',dict(passed=True,software_only=True,policy_cases=cases,negative_cases=negative,
    exact_new_current2200_schema_preserved=True,actual_positive_capture_or_runtime_qualified=False,model_native=0))
  native=c.load('v1577_actual_production_CLI',C/'native_entry.py')
  task_path=target/'TASK.json';c.put(task_path,c.read(C/'TASKS.json')[0]);prior=sys.argv;sys.argv=['native_entry',str(task_path)]
  try:assert native.main()==1
  finally:sys.argv=prior
  assert c.read(c.O/'unadmitted/CLI_REFUSAL.json')['closed']
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  gates={k:True for k in ['goal_bound_policy','variable_complete_witness','unknown_and_first_error','current_source_runtime_binding','bounded_production_CLI','current_CPP2200_API','actual_durable_policy_and_reference','actual_lifecycle_and_replay_source_pipeline','once_owner_and_caps']}
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,
   models_authorized=False,actual_capture_qualified=False,actual_runtime_qualified=False),maximum=4*1024**2)
  result.update(passed=True,source_gates=gates,writer_source_coverage={k:True for k in ['ACTUAL_ROS','PLANNER','SUPERVISOR_LOG']},
   negative_cases=len(negative),source_members=len(source),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start)
  c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}))
 return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
