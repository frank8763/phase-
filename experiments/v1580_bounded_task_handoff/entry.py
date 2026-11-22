"""One task-handoff/real CLI SOURCE continuation, no prior numerical suite."""
import fcntl,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1580_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def main():
 start=time.monotonic();resources=c.bootstrap();c.guard()
 lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,optimizer_calls=0,Allocator_recomputations=0,phase_FFI_loads=0,actual_capture_qualified=False,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
 def profile(frame,event,arg):
  if event=='call':
   path=Path(frame.f_code.co_filename)
   if path.is_absolute()and path.is_relative_to(c.R):
    assert not(path.name in {'model.py','coupled_model.py','prediction.py','engine.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','simulate','compute'}),'SOURCE_MODEL_FORBIDDEN'
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'},'SOURCE_NUMERICAL_BINDING_FORBIDDEN'
    assert not('gear_handoff.py'in str(path)and frame.f_code.co_name=='select'),'SOURCE_GEAR_FORBIDDEN'
 sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  old=c.R/'runs/v1579_canonical_digest_scope';review=c.read(old/'CLOSED_REVIEW.json')
  assert review['closed']and not review['passed']and review['saved_remaining_storage_subtarget_passed']
  for name,key in [('source_target/QUALIFICATION.json','subtarget_sha256'),('source_target/actual_software/CURRENT_CLOSED.json','software_current_closed_sha256'),('source_target/actual_software/CURRENT.bin','software_current_stream_sha256')]:assert c.sha(old/name)==review[key]
  sub=c.read(old/'source_target/QUALIFICATION.json');assert sub['passed']and sub['software_only']
  target=c.O/'source_target';target.mkdir();task=c.read(C/'TASKS.json')[0]
  raw=json.dumps(task,sort_keys=True,separators=(',',':'),allow_nan=False).encode();assert 65536<len(raw)<=128*1024
  writers=c.load('v1580_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1580_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  writer=writers.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'))
  with io.OutputBoundary(target,writer.reserve):c.put(target/'TASK.json',task,maximum=128*1024)
  assert c.read(target/'TASK.json')==task
  native=c.load('v1580_real_native_CLI',C/'native_entry.py');prior=sys.argv;sys.argv=['native_entry',str(target/'TASK.json')]
  try:assert native.main()==1
  finally:sys.argv=prior
  refusal=c.read(c.O/'unadmitted/CLI_REFUSAL.json')
  assert refusal['closed']and not refusal['passed']and 'GOAL_BOUND_ACTUAL_RUNTIME_NOT_ADMITTED'in refusal['first_error']and refusal['source_binding_before_factory']and not refusal['actual_counts_unknown']
  assert not(c.O/'ROUND_WINDOW.json').exists()and not(c.O/'ACTUAL_ONCE_CLAIM.json').exists()
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,focused_task_handoff_qualification=True,models_authorized=False,actual_capture_qualified=False,actual_runtime_qualified=False),maximum=4*1024**2)
  result.update(passed=True,source_members=len(source),canonical_task_bytes=len(raw),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,old_storage_subtarget_reused_by_SHA_not_rerun=True,source_gates=dict(explicit_task_handoff=True,actual_CLI_refusal_saved=True,complete_actual_source_target=False))
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
