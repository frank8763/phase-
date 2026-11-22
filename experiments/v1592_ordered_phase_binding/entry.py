"""Once changed production phase-limit SOURCE target; inherited suite not rerun."""
import ast,copy,fcntl,importlib.abc,importlib.util,json,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1592_phase_source_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 start=time.monotonic();resources=c.bootstrap();c.guard();lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as stream:json.dump(dict(unix=time.time(),models_authorized=False),stream)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,Allocator_recomputations=0,optimizer_calls=0,phase_FFI_loads=0,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
 class NoNumerics(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','rclpy','runtime','factory','vehicle'}:raise AssertionError('PHASE_BINDING_NO_NUMERICS:'+name)
 finder=NoNumerics();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call':
   path=Path(frame.f_code.co_filename)
   if path.is_absolute()and path.is_relative_to(c.R):
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future'}
    assert not(path.name in {'engine.py','coupled_model.py','prediction.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','compute','step','simulate'})
   assert time.monotonic()-start<120
 sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  prior=c.read(c.R/'runs/v1588_signed_policy_source/ENTRY_QUALIFICATION.json');rec=c.read(c.R/'runs/v1588_signed_policy_source/CURRENT_SOURCE_REMOTE_RECOVERY.json')
  assert prior['passed']and prior['closed']and prior['complete_actual_source_target_passed']and prior['models']==prior['physical_native']==0
  assert rec['all_frozen_members_remote_chain_covered']and rec['source_freeze_sha256']==c.sha(c.BASE)
  native=c.load('v1592_real_native_phase_binding',C/'native_driver.py')
  original=c.load('v1592_original_phase_runtime',c.R/'experiments/v1449_route_initializer_binding/phase_runtime.py')
  target=c.O/'source_target';target.mkdir();wm=c.load('v1592_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1592_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'));negative=[]
  def refused(name,fn):
   try:fn()
   except(AssertionError,KeyError,ValueError)as error:negative.append(dict(name=name,error=repr(error)));return
   raise AssertionError('PHASE_BINDING_NEGATIVE_ACCEPTED:'+name)
  now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
  frozen=c.read(C/'LIMITS.json');authority=json.loads(json.dumps(dict(limits=frozen),sort_keys=True))
  with io.OutputBoundary(target,writer.reserve):
   refused('original_sorted_authority_order_refused',lambda:original.PhaseRuntime(window,authority['limits'],lambda p:None))
   bound=native.phase_limits(authority);assert bound==frozen==authority['limits']
   phases=original.PhaseRuntime(window,bound,lambda p:None)
   assert list(phases.budget.caps)==list(frozen['phase_wall_caps_s'])
   assert phases.budget.boundary('normal')['absolute_deadline_unix']==window['started_unix']+4140
   assert phases.budget.boundary('normal')['hard_stop_monotonic']==window['started_monotonic']+4140
   for name,key,value in [('changed_actual_cap','maximum_actual_native',40001),('changed_root_cap','storage_limit_bytes',16*1024**3)]:
    bad=copy.deepcopy(authority);bad['limits'][key]=value;refused(name,lambda bad=bad:native.phase_limits(bad))
   bad=copy.deepcopy(authority);bad['limits']['phase_wall_caps_s']['normal']+=1;refused('changed_phase_time',lambda:native.phase_limits(bad))
   bad=copy.deepcopy(authority);del bad['limits']['phase_wall_caps_s']['normal'];refused('missing_phase_time',lambda:native.phase_limits(bad))
   # Every production module is inherited by exact normalized AST. Only this
   # new phase_limits helper and its one execute call are different.
   base=c.R/'experiments/v1588_signed_policy_source';reused=[]
   for path in C.glob('*.py'):
    if path.name in {'entry.py','common.py','source_owner_entry.py','source_cases.py','phase_cases.py','writer_coverage.py'}:continue
    before=ast.parse((base/path.name).read_text());text=path.read_text().replace('v1592_ordered_phase_binding','v1588_signed_policy_source').replace('v1592','v1588')
    if path.name=='native_driver.py':
     text=text.replace('limits=phase_limits(authority)','limits=authority[\'limits\']');after=ast.parse(text);after.body=[n for n in after.body if not(isinstance(n,ast.FunctionDef)and n.name=='phase_limits')]
    else:after=ast.parse(text)
    assert ast.dump(before)==ast.dump(after),path.name;reused.append(path.name)
   barrier=c.load('v1592_new_round_barrier',C/'round_barrier.py').before_next(c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),current_round=C.name)
   assert 'v1588_signed_policy_source'in barrier['reviewed_new_authority_rounds']
   c.put(target/'QUALIFICATION.json',dict(passed=True,software_source_only=True,negative_cases=negative,original_sorted_order_red_then_canonical_binding_green=True,limits_values_byte_semantics_unchanged=True,phase_snapshot=phases.snapshot(),source_reuse=reused,prior_complete_source_proof_sha256=c.sha(c.R/'runs/v1588_signed_policy_source/ENTRY_QUALIFICATION.json'),prior_round_storage_barrier=barrier,models=0,physical_native=0))
  assert not(c.O/'ROUND_WINDOW.json').exists()and not(c.O/'ACTUAL_ONCE_CLAIM.json').exists()
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=True,actual_runtime_qualified=False,whole_route_passed=False),maximum=4*1024**2)
  result.update(passed=True,complete_actual_source_target_passed=True,source_gates=prior['source_gates'],writer_source_coverage=prior['writer_source_coverage'],source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,prior_full_suite_reused_by_exact_SHA_AST_not_rerun=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
