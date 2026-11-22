"""Once production nested-output target; SOFTWARE2200 arrays, zero models."""
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1578_target_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 start=time.monotonic();resources=c.bootstrap();c.guard()
 lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,optimizer_calls=0,
  Allocator_recomputations=0,phase_FFI_loads=0,actual_capture_qualified=False,actual_runtime_qualified=False,
  complete_actual_source_target_passed=False,whole_route_passed=False)
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
  predecessor=c.read(c.R/'runs/v1577_goal_bound_segment_bridge/ENTRY_QUALIFICATION.json')
  assert predecessor['closed']and not predecessor['passed']and predecessor['models']==0
  assert 'WRITABLE_RAW_DESCRIPTOR_REQUIRES_BOUNDED_PIPE_OR_EXPLICIT_NATIVE_SAVE'in predecessor['first_error']
  target=c.O/'source_target';target.mkdir()
  writers=c.load('v1578_original_budget',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
  io=c.load('v1578_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  scopes=c.load('v1578_production_scope_composition',C/'scoped_output.py')
  root=writers.WriterBudget(target,role='PLANNER',maximum_bytes=4*1024**2,source_identity=c.sha(C/'entry.py'))
  negative=[]
  def refused(name,fn,contains=None):
   try:fn()
   except BaseException as error:
    if contains is not None:assert contains in repr(error),(name,repr(error))
    negative.append(dict(name=name,error=repr(error)));return error
   raise AssertionError('SOURCE_NEGATIVE_ACCEPTED:'+name)
  with io.OutputBoundary(target,root.reserve)as parent:
   broken=target/'red_original_nested';broken.mkdir()
   refused('original_nested_constructor_red',lambda:writers.WriterBudget(broken,role='PLANNER',maximum_bytes=32768,source_identity='a'*64),'WRITABLE_RAW_DESCRIPTOR_REQUIRES_BOUNDED_PIPE_OR_EXPLICIT_NATIVE_SAVE')
   folder=target/'owned_persistent';folder.mkdir()
   owned=scopes.Scope(parent=parent,folder=folder,writers=writers,io=io,maximum_bytes=1024**2,source_identity='b'*64)
   with owned.activate():
    handle=(folder/'held.bin').open('xb');handle.write(b'first');handle.flush()
    refused('sibling_overlap',lambda:scopes.Scope(parent=parent,folder=folder,writers=writers,io=io,maximum_bytes=1024**2,source_identity='b'*64))
    with owned.activate():handle.write(b'second')
    refused('child_path_escape',lambda:(target/'escaped.bin').write_bytes(b'forbidden'),'BOUNDED_OUTPUT_PATH_ESCAPE')
   refused('inactive_persistent_handle',lambda:handle.write(b'forbidden'),'CHILD_SCOPE_NOT_ACTIVE')
   with owned.activate():handle.write(b'third');handle.close()
   assert(folder/'held.bin').read_bytes()==b'firstsecondthird'
   for label,maximum in [('child_cap',32768),('root_cap',1024**2)]:
    sub=target/label;sub.mkdir();limited=scopes.Scope(parent=parent,folder=sub,writers=writers,io=io,maximum_bytes=maximum,source_identity='c'*64)
    if label=='root_cap':
     original=parent.reserve
     def denied(path,size):raise OSError('SOFTWARE_ROOT_PREDEBIT_REFUSED')
     parent.reserve=denied
    try:
     with limited.activate():refused(label,lambda:(sub/'denied.bin').write_bytes(b'x'*65536),'CHILD_OUTPUT_BYTE_CAP_EXHAUSTED'if label=='child_cap'else'SOFTWARE_ROOT_PREDEBIT_REFUSED')
    finally:
     if label=='root_cap':parent.reserve=original
    assert limited.failed
    refused('poison_no_retry_'+label,lambda:limited.activate().__enter__(),'CHILD_SCOPE_POISONED')
   import numpy as np
   stream=c.load('v1578_current_schema',C/'stream.py');codec=stream.record_codec()
   arrays={k:np.zeros(shape,dtype=np.int64 if k in codec.INTS else np.float64)for k,shape in codec.dimensions(2200).items()}
   arrays['native'][:]=np.arange(100,2301);arrays['sim_time'][:]=.01*arrays['native']
   actual=target/'actual_software';actual.mkdir()
   lease=scopes.Scope(parent=parent,folder=actual,writers=writers,io=io,maximum_bytes=32*1024**2,source_identity=c.sha(C/'entry.py'))
   module=c.load('v1578_actual_production_sink',C/'actual_sink.py')
   with lease.activate()as boundary:
    sink=module.ActualSink(folder=actual,writer=lease.writer,boundary=boundary,scope=lease,source=source,method={'response_method_sha256':'d'*64},native=SimpleNamespace(applied=100,vehicle=SimpleNamespace(count=100)))
   packet=dict(native_tick=100,software_fixture=True);identity=c.digest(packet)
   sink.origin(dict(source_packet=packet,source_packet_sha256=identity,software_only=True))
   saved=sink.complete(arrays,dict(source_packet_sha256=identity,model_counts=dict(model_native=0,software_arrays=True)))
   proof=dict(passed=False,source_packet_sha256=identity,before_native=100,complete_native=2200,software_not_safety_proof=True)
   sink.after_gate(proof,saved)
   refused('unsafe_proof_cannot_apply',lambda:sink.before(dict(before_native=100,source_packet_sha256=identity,applied=False),proof,arrays['states'],arrays['ctrl']))
   sink.close(dict(model_native=0,software_arrays_not_integrations=True))
   seal=c.read(actual/'CURRENT_CLOSED.json');assert seal['current_branches']==1 and seal['applied_receipts']==0
   assert c.sha(actual/'CURRENT.bin')==seal['whole_stream_sha256']
   assert lease.writer._read()['charged_bytes']>16384 and root._read()['charged_bytes']>lease.writer._read()['charged_bytes']
   life=c.load('v1578_actual_scope_refusal',C/'lifecycle.py')
   refused('actual_missing_admission',lambda:life.run(c.read(C/'TASKS.json')[0],{}),'GOAL_BOUND_ACTUAL_RUNTIME_NOT_ADMITTED')
   c.put(target/'QUALIFICATION.json',dict(passed=True,software_only=True,negative_cases=negative,original_red_scoped_green=True,full_current2200_storage_not_numerics=True,root_charged_bytes=root._read()['charged_bytes'],child_charged_bytes=lease.writer._read()['charged_bytes']))
  native=c.load('v1578_native_CLI',C/'native_entry.py');task=target/'TASK.json';c.put(task,c.read(C/'TASKS.json')[0]);prior=sys.argv;sys.argv=['native_entry',str(task)]
  try:assert native.main()==1
  finally:sys.argv=prior
  assert c.read(c.O/'unadmitted/CLI_REFUSAL.json')['closed']
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,focused_scoped_output_qualification=True,models_authorized=False,actual_capture_qualified=False,actual_runtime_qualified=False),maximum=4*1024**2)
  result.update(passed=True,source_members=len(source),negative_cases=len(negative),resources=resources,source_gates=dict(nested_original_budget_composition=True,persistent_current_sink_scope=True,root_and_child_caps=True,unsafe_proof_no_apply=True,complete_actual_source_target=False),writer_charged_bytes=root._read()['charged_bytes'])
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start)
  c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}))
 return 0 if result['passed']else 1

if __name__=='__main__':raise SystemExit(main())
