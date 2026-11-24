"""Once SOURCE for exact unapplied TEB mapping refusal audit, no numerics."""
import ast,copy,fcntl,importlib.abc,sys,time,traceback
from context import C,O,R,read,put,sha,load

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1884_original_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','ctypes','kernel','vehicle','factory','planner','fast_predict','scipy','OpenGL','rclpy'}:raise AssertionError('SOURCE_NO_NUMERICAL:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,optimizer_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  prior=R/'runs/v1880_final_three_checked';assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']
  rec=read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and not rec['uncovered_members']
  assert read(prior/'FINAL_CLOSURE_CHECK.json')['passed']
  for n,h in read(prior/'POST_SOURCE_STORAGE_BARRIER.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  files.update(read(prior/'SOURCE_FREEZE.json')['files'])
  inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  names=['v1888_teb_unapplied_refusal_exact','v1889_teb_remaining_exact','v1890_teb_exact_source_recovery','v1891_teb_exact_runtime_recovery']
  for name in names:
   for p in(R/'experiments'/name).iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['AUTHORIZATION.json','PLAN_LOCKED.json','PILOT_TASK.json','PRIOR_CLOSED_BARRIERS.json','SAVED_REJECTION_BINDING.json','MAPPING_SOFTWARE_INPUT.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
  old=R/'experiments/v1862_remaining_routes_teb';new=R/'experiments/v1888_teb_unapplied_refusal_exact';unchanged=[]
  for p in old.glob('*.py'):
   if p.name in {'driver.py','resources.py','audit_component.py'}:continue
   expected=p.read_text().replace(old.name,new.name).replace('v1866_remaining_common_matrix','v1889_teb_remaining_exact')
   assert expected==(new/p.name).read_text(),'UNRELATED_PRODUCTION_CHANGE:'+p.name;unchanged.append(p.name)
  text=(old/'driver.py').read_text();a=text.index('     if initial is not None:');b=text.index('     if capture is not None:',a);block=text[a:b];expected=text[:a]+text[b:];i=expected.index("     if result.get('evidence_saved')and not inside")
  block=block.replace('resources.prepare_closed_capture(quota,phase,inside)',"resources.prepare_nplus1_after_capture(quota,phase,inside,result.get('evidence_saved'))")
  assert expected[:i]+block+expected[i:]==(new/'driver.py').read_text()
  assert sha(new/'resources.py')==sha(R/'experiments/v1879_capture_before_nplus1_checked/resources.py')
  assert read(prior/'CLOSE_ORDER_SOFTWARE_PROOF.json')['passed']
  before="""   row=read(out/f'cycle_{cycle:04d}_query.json');mapped=frames.command(answer['proposal'],config)
   assert row['command']==mapped['body_request'][:2]and row['original_ROS_saturation_explicit_port']==mapped
   assert row['reference_trajectory_body_centre']==frames.trajectory(answer['proposal'],config)"""
  after="""   row=read(out/f'cycle_{cycle:04d}_query.json')
   rejection=load('v1883_unapplied_command_audit',C/'rejected_mapping.py')
   mapping_scope=rejection.verify(frames,answer,config,row,result['first_error'],path==query_paths[-1])
   if mapping_scope['refused_unapplied']:
    assert not any(p.name.startswith(f'cycle_{cycle:04d}_')for p in out.glob('cycle_*_admission_*.json')),'REJECTED_COMMAND_HAS_ADMISSION'
    assert not(out/f'cycle_{cycle:04d}_shadow.json').exists(),'REJECTED_COMMAND_HAS_SHADOW'"""
  text=(old/'audit_component.py').read_text();assert text.count(before)==1 and text.replace(before,after)==(new/'audit_component.py').read_text()
  contract=load('v1884_exact_seven_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');assert contract.validate(plan,registry)
  boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();auth=read(O/'AUTHORIZATION.json');contract.time_admission(auth,time.time(),boot)
  original=read(R/plan['previous_plan_path']);assert sha(R/plan['previous_plan_path'])==plan['previous_plan_sha256'];ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
  for row in plan['assignments']:
   parent=next(r for r in original['assignments']if r['round_id']==row['round_id']);a=read(R/parent['output_root']/'PILOT_TASK.json');b=read(R/row['output_root']/'PILOT_TASK.json')
   assert {k:v for k,v in a.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in b.items()if k not in {'output','run_root','run_id'}}
   for name in ['TEB_CONFIG.json','LIMITS_DRAFT.json','NATIVE_BINDING.json','BINARY_BINDING.json','EXACT_NATIVE_ALIASES.json']:assert sha(R/parent['output_root']/name)==sha(R/row['output_root']/name)
   slot=next(x for x in ledger['slots']if x['method']=='TEB'and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
   assert not(R/row['output_root']/'PILOT_ONCE_CLAIM.json').exists()
  negative=[]
  for kind in ['order','method','task','output']:
   bad=copy.deepcopy(plan)
   if kind=='order':bad['assignments'][0]['order']=1
   if kind=='method':bad['assignments'][0]['method']='DWA'
   if kind=='task':bad['assignments'][0]['common_task']='common_01'
   if kind=='output':bad['assignments'][0]['output_root']='runs/elsewhere'
   try:contract.validate(bad,registry)
   except (AssertionError,KeyError):negative.append(kind)
   else:raise AssertionError('FALSE_PLAN_ACCEPTED:'+kind)
  for kind in ['boot','late']:
   try:contract.time_admission(auth,time.time()if kind=='boot'else auth['deadline_unix']-7199,'wrong'if kind=='boot'else boot)
   except AssertionError:negative.append(kind)
   else:raise AssertionError('FALSE_CLOCK_ACCEPTED:'+kind)
  import runpy
  try:runpy.run_path(str(new/'pilot_entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='TEB_NAVIGATION_NOT_ADMITTED';negative.append('real_production_CLI_before_numerical_import')
  else:raise AssertionError('PRODUCTION_CLI_ACCEPTED_WITHOUT_ADMISSION')
  mapping=load('v1884_saved_mapper_regression',C/'mapping_regression.py').run();assert mapping['passed'];put(O/'MAPPING_REFUSAL_SOFTWARE_PROOF.json',mapping)
  regression=load('v1884_current_admission_software',C/'admission_regression.py').run(read,sha,load);assert regression['passed']and len(regression['valid_remaining_assignments'])==7;put(O/'VALID_ADMISSION_SOFTWARE_PROOF.json',regression)
  proof=dict(passed=True,unchanged_production_modules=unchanged,exact_original_numeric_algorithm_preserved=True,only_unapplied_final_mapping_refusal_audit_scope=True,no_old_trajectory_audit_or_qualification=True,original_closed_failures_unchanged=True,closure_order_reused_from_passed_source=str(prior.relative_to(R)),closure_order_proof_sha256=sha(prior/'CLOSE_ORDER_SOFTWARE_PROOF.json'),mapping_proof_sha256=sha(O/'MAPPING_REFUSAL_SOFTWARE_PROOF.json'),models=0,physical_native=0)
  assert all(sha(R/n)==h for n,h in files.items());put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited));put(O/'SOURCE_QUALIFICATION_PROOF.json',proof);put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
  result.update(passed=True,source_members=len(files),negative_cases=len(negative)+len(mapping['negative_cases'])+len(regression['negative_cases']),valid_admission_software_cases=7)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
