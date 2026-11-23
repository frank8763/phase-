"""Once software qualification of conservative clocks and imported audit scope."""
import ast,fcntl,importlib.abc,math,os,runpy,sys,time,traceback,types,copy
from context import C,O,R,ROOT,SOURCE,put,read,sha,load

def main():
 start=time.monotonic();assert O==SOURCE
 os.environ['MUJOCO_GL']='osmesa'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1744_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1649_error_stop_sensor_capture';source=read(prior/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  negatives=[];positives=[]
  for case in ['phase_03__no_onward','phase_03__full']:
   barrier=read(ROOT/'rounds'/case/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
   for a,b in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/barrier[a])==barrier[b]
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'SOURCE_OUTER_CLOSED.json',SOURCE/'ROUND_AUTHORIZATION.json',ROOT/'rounds/phase_03__full/ROUND_WINDOW.json',ROOT/'rounds/phase_03__full/CONSOLE_RECOVERED_FAILURE_RECORD.json',ROOT/'rounds/phase_03__no_onward/AUDIT_SCOPE_DIAGNOSIS.json']:
   source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for n in ['context.py','phase_contract.py','resources.py','capture.py','history_binding.py','work.py','quota.py','transforms.py','runtime_binding.py','entry.py','driver.py','error_stop.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1649_error_stop_sensor_capture'/n).read_bytes();reused.append(n)
  clock=load('v1744_clock_software',C/'clock_window.py')
  w=read(ROOT/'rounds/phase_03__full/ROUND_WINDOW.json');old=w['hard_stop_monotonic']-w['started_monotonic'];assert old>5400
  beginnings=[0.,1.,64049.809282792,65535.99999999999,65536.,1795424612.4527948]
  for exponent in range(1,43):
   v=float(2**exponent);beginnings.extend([math.nextafter(v,-math.inf),v,math.nextafter(v,math.inf)])
  for v in beginnings:
   for duration in [4200,5400]:
    end=clock.earlier_deadline(v,duration);assert 0<end-v<=duration and end<v+duration
  for bad in [float('nan'),float('inf'),-1.,1e308]:
   try:clock.earlier_deadline(bad,5400)
   except AssertionError:negatives.append('invalid_or_unrepresentable_clock')
   else:raise AssertionError('BAD_CLOCK_ACCEPTED')
  for duration in [0,-1,5401,float('nan')]:
   try:clock.earlier_deadline(64049.809282792,duration)
   except AssertionError:negatives.append('invalid_duration')
   else:raise AssertionError('BAD_DURATION_ACCEPTED')
  win=clock.make_window(w['started_unix'],w['started_monotonic'],w['boot_id']);assert win['started_unix']==w['started_unix']and win['started_monotonic']==w['started_monotonic']and win['boot_id']==w['boot_id']
  tree=ast.parse((C/'context.py').read_text());admit=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='admission');gate=next(n for n in admit.body if isinstance(n,ast.Assert)and "w['hard_stop_monotonic']"in ast.unparse(n.test))
  exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(gate)],type_ignores=[])),str(C/'context.py'),'exec'),dict(w=win,remaining=lambda _:100.))
  try:exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(gate)],type_ignores=[])),str(C/'context.py'),'exec'),dict(w=w,remaining=lambda _:100.))
  except AssertionError:negatives.append('observed_old_float_boundary_rejected')
  else:raise AssertionError('OLD_CLOCK_FAILURE_NOT_REPRODUCED')
  positives.append(dict(clock_samples=len(beginnings)*2,old_duration_repr=repr(old),new_duration_repr=repr(win['hard_stop_monotonic']-win['started_monotonic']),unchanged_context_strict_gate=True,start_clocks_not_reset=True))
  oldowner=(R/'experiments/v1649_error_stop_sensor_capture/owner.py').read_text();line="window=dict(started_unix=now,started_monotonic=started,absolute_deadline_unix=now+5400,hard_stop_monotonic=started+5400,normal_end_unix=now+4200,boot_id=boot)"
  replacement="clock_spec=importlib.util.spec_from_file_location('v1744_conservative_clock',C/'clock_window.py');clock_module=importlib.util.module_from_spec(clock_spec);clock_spec.loader.exec_module(clock_module)\n  window=clock_module.make_window(now,started,boot);root=window['absolute_deadline_unix']"
  assert(C/'owner.py').read_text()==oldowner.replace(line,replacement)
  assert(C/'audit_seams.py').read_text().startswith((R/'experiments/v1649_error_stop_sensor_capture/audit_seams.py').read_text())
  old_binding=(R/'experiments/v1649_error_stop_sensor_capture/audit_binding.py').read_text()
  binding_line="if path==seams.PARENT:seam_proofs.append(seams.fresh_phase_auditor(module,source))"
  binding_new="if path==seams.PARENT:\n   seam_proofs.append(seams.bind_goal_verify_import(module,source,task['mechanism_variant']))\n   seam_proofs.append(seams.fresh_phase_auditor(module,source))\n   assert module.audit.__globals__['verify']is module.verify,'GOAL_VERIFY_IMPORTED_ALIAS_NOT_BOUND'"
  assert(C/'audit_binding.py').read_text()==old_binding.replace(binding_line,binding_new).replace("assert result['passed']and len(seam_proofs)==2","assert result['passed']and len(seam_proofs)==3")
  seams=load('v1744_production_audit_seams',C/'audit_seams.py')
  class Ref:
   def __init__(self):self.values=[[0.,0.,0.],[1.,2.,0.]]
   def __len__(self):return len(self.values)
   def __getitem__(self,key):
    if isinstance(key,tuple):return self.values[key[0]][key[1]]
    return self.values[key]
  x=dict(goal=[4.,-2.],packet={'same':'unmodified'},marker='whole_task');reference=Ref()
  selection=dict(method='refuge_onward',measured_onward_still_required=True,prefix_counts_as_whole_arrival=False,prefix_rows=[[0.,0.,1,0]],rows=[[0.,0.,1,0]],prefix_native=1,admission=dict(passed=True,shadow_memory_reset=False))
  local=seams.prefix_proof_input(x,selection,reference,'no_onward');assert local['goal']==[1.,2.]and x['goal']==[4.,-2.]and local['packet']==x['packet']
  for variant,choice in [('full',dict(method='refuge_onward')),('no_onward',dict(method='direct'))]:assert seams.prefix_proof_input(x,choice,reference,variant)is x
  for label,patch,variant in [('flag_missing',{'measured_onward_still_required':False},'no_onward'),('prefix_is_arrival',{'prefix_counts_as_whole_arrival':True},'no_onward'),('state_reset',{'admission':dict(passed=True,shadow_memory_reset=True)},'no_onward'),('bad_length',{'prefix_native':2},'no_onward'),('wrong_variant',{},'full')]:
   try:seams.prefix_proof_input(x,dict(selection,**patch),reference,variant)
   except AssertionError:negatives.append(label)
   else:raise AssertionError('BAD_PREFIX_SCOPE_ACCEPTED:'+label)
  goal_tree=ast.parse(seams.GOAL.read_text());original_goal=next(n for n in goal_tree.body if isinstance(n,ast.FunctionDef)and n.name=='verify')
  parent_tree=ast.parse(seams.PARENT.read_text());original_parent=next(n for n in parent_tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
  def module():
   m=types.ModuleType('software_parent');m.__file__=str(seams.PARENT)
   namespace={'__file__':str(seams.GOAL)};exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(original_goal)],type_ignores=[])),str(seams.GOAL),'exec',dont_inherit=True),namespace);m.verify=namespace['verify']
   exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(original_parent)],type_ignores=[])),str(seams.PARENT),'exec',dont_inherit=True),vars(m));return m
  for variant in ['full','no_onward']:
   m=module();scope=seams.bind_goal_verify_import(m,source,variant);assert scope['all_other_original_verify_AST_unchanged']
   seams.fresh_phase_auditor(m,source);assert m.audit.__globals__['verify']is m.verify
   transformed=ast.parse((C/'audit_seams.py').read_text());helper=next(n for n in transformed.body if isinstance(n,ast.FunctionDef)and n.name=='bind_goal_verify_import')
   inserted=next(n for n in ast.walk(helper)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='parse'and isinstance(n.args[0],ast.Constant)and isinstance(n.args[0].value,str)and '_v1744_prefix_input'in n.args[0].value)
   statement=ast.parse(inserted.args[0].value).body[0]
   for index,choice in [(0,selection if variant=='no_onward'else dict(method='refuge_onward')),(1,selection)]:
    namespace=dict(local=x,index=index,selection=choice,saved=dict(states=reference),_v1744_prefix_input=seams.prefix_proof_input,_v1744_variant=variant)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(statement)],type_ignores=[])),str(C/'audit_seams.py'),'exec'),namespace)
    assert namespace['local']['goal']==([1.,2.]if variant=='no_onward'and index==0 else [4.,-2.])and x['goal']==[4.,-2.]
   positives.append(dict(variant=variant,actual_imported_verify_alias_bound_before_audit_global_copy=True,original_full_auditor_not_executed=True,all_unrelated_verify_AST_unchanged=True,initial_prefix_only=True,onward_and_actual_wholegoal_unchanged=True))
  m=module();m.verify=lambda *_:None
  try:seams.bind_goal_verify_import(m,source,'no_onward')
  except(AssertionError,KeyError):negatives.append('original_verify_code_identity')
  else:raise AssertionError('FORGED_VERIFY_ACCEPTED')
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as error:assert str(error)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED';negatives.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ACCEPTED')
  proof=dict(passed=True,source_only=True,models=0,physical_native=0,replay_native=0,FFI_loads=0,actual_old_audit_not_executed=True,unchanged_modules_reused=reused,positive_cases=positives,negative_cases=negatives,new_scientific_tasks=0,all20denominator_unchanged=True,automatic_next_round=False)
  target=SOURCE/'source_target';target.mkdir();put(target/'QUALIFICATION.json',proof);put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],negative_cases=len(negatives),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as error:
  result.update(first_error=repr(error),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
