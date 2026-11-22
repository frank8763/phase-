"""Once real context.dump under original writer boundary; no old suite/model."""
import ast,fcntl,importlib.abc,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1599_context_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 start=time.monotonic();resources=c.bootstrap();c.guard();lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,Allocator_recomputations=0,optimizer_calls=0,phase_FFI_loads=0,OS_library_loads=0,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
 class NoNumerics(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','OpenGL','torch','rclpy','factory','vehicle','kernel','runtime'}:raise AssertionError('CONTEXT_SOURCE_NO_NUMERICS:'+name)
 finder=NoNumerics();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call':
   p=Path(frame.f_code.co_filename)
   if p.is_absolute()and p.is_relative_to(c.R):
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future','create_vehicle'}
    assert not(p.name in {'engine.py','coupled_model.py','prediction.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','step','compute','simulate'})
   assert time.monotonic()-start<120
 sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  prior=c.read(c.R/'runs/v1596_bootstrap_alias_repair/ENTRY_QUALIFICATION.json');rec=c.read(c.R/'runs/v1596_bootstrap_alias_repair/CURRENT_SOURCE_REMOTE_RECOVERY.json')
  assert prior['passed']and prior['complete_actual_source_target_passed']and prior['models']==prior['physical_native']==0
  assert rec['all_frozen_members_remote_chain_covered']and rec['source_freeze_sha256']==c.sha(c.BASE)
  # Same production module and same ACTUAL_ROS wrapper as the real failure.
  context=c.load('v1599_actual_current_context',C/'route_context.py');wm=c.load('v1599_original_actual_ROS_writer',c.R/'experiments/v1479_retirement_scope_binding/writer_budget.py');io=c.load('v1599_original_actual_ROS_boundary',c.R/'experiments/v1479_retirement_scope_binding/bounded_io.py')
  target=c.O/'source_target';target.mkdir();writer=wm.WriterBudget(target,role='ACTUAL_ROS',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'));negative=[]
  def refused(name,fn):
   try:fn()
   except(AssertionError,KeyError,ValueError,OSError)as error:negative.append(dict(name=name,error=repr(error)));return
   raise AssertionError('CONTEXT_NEGATIVE_ACCEPTED:'+name)
  with io.OutputBoundary(target,writer.reserve):
   payload=dict(scope='SOFTWARE_CONTEXT_IO_NOT_SENSING',body=[.3,0.,0.,0.,0.],counter=0,text='完整来源')
   path=target/'DURABLE_CONTEXT.json';context.dump(path,payload);assert c.read(path)==payload and not path.with_name(path.name+'.tmp').exists()
   first=c.sha(path);payload['counter']=1;context.dump(path,payload);assert c.read(path)==payload and c.sha(path)!=first
   refused('nonfinite_JSON_refused',lambda:context.dump(target/'NONFINITE.json',dict(value=float('nan'))))
   refused('metadata_cap_unchanged',lambda:context.dump(target/'OVERSIZED.json',dict(value='x'*(4*1024**2))))
   refused('relative_path_refused',lambda:context.dump(Path('not_absolute.json'),{}))
   with(target/'RAW_WRITER_PROBE.txt').open('x')as stream:
    stream.write('SOFTWARE')
    refused('writable_raw_descriptor_still_refused',stream.fileno)
   assert not(target/'NONFINITE.json').exists()and not(target/'OVERSIZED.json').exists()
   # Confirm exactly one durability change plus version relocation. All
   # original writer/policy/model/current/lifecycle implementation is inherited.
   base=c.R/'experiments/v1596_bootstrap_alias_repair';reused=[]
   for path in C.glob('*.py'):
    if path.name in {'entry.py','common.py','source_owner_entry.py','source_cases.py','phase_cases.py','writer_coverage.py'}:continue
    before=(base/path.name).read_text();text=path.read_text().replace('v1599_readonly_context_durability','v1596_bootstrap_alias_repair').replace('v1599','v1596')
    if path.name=='route_context.py':before=before.replace('stream.write(data);stream.flush();os.fsync(stream.fileno())',"stream.write(data);stream.flush()\n    descriptor=os.open(temporary,os.O_RDONLY)\n    try:os.fsync(descriptor)\n    finally:os.close(descriptor)")
    assert ast.dump(ast.parse(before))==ast.dump(ast.parse(text)),path.name;reused.append(path.name)
   barrier=c.load('v1599_previous_round_barrier',C/'round_barrier.py').before_next(c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),current_round=C.name)
   assert 'v1596_bootstrap_alias_repair'in barrier['reviewed_new_authority_rounds']
   c.put(target/'QUALIFICATION.json',dict(passed=True,source_only=True,real_context_dump_called=True,original_actual_ROS_boundary_source_sha256=c.sha(c.R/'experiments/v1479_retirement_scope_binding/bounded_io.py'),durable_first_SHA=first,durable_replaced_SHA=c.sha(target/'DURABLE_CONTEXT.json'),negative_cases=negative,source_reuse=reused,previousround_barrier=barrier,models=0,physical_native=0))
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=True,actual_runtime_qualified=False,whole_route_passed=False),maximum=4*1024**2)
  result.update(passed=True,complete_actual_source_target_passed=True,source_gates=prior['source_gates'],writer_source_coverage=prior['writer_source_coverage'],source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,old_suites_reused_not_rerun=True,real_context_original_boundary_qualified=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
