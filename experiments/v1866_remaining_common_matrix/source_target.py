"""Once source-only qualification of root/round separation and six valid admissions."""
import ast,copy,fcntl,importlib.abc,json,os,runpy,sys,time,traceback
from context import C,O,R,read,put,sha,load,digest
def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1852_original_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','ctypes','kernel','vehicle','factory','planner','fast_predict','scipy','OpenGL','rclpy'}:raise AssertionError('SOURCE_NO_NUMERICAL:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,optimizer_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  base=R/'runs/v1859_evening_complete_inputs'
  assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed']
  recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
  for n,h in read(base/'POST_SOURCE_STORAGE_BARRIER.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  # Earlier split qualification supplement is explicitly checked, not inferred.
  for a,h in [('index_path','index_sha256'),('full_remote_proof_path','full_remote_proof_sha256')]:assert sha(R/recovery[a])==recovery[h]
  files.update(read(base/'SOURCE_FREEZE.json')['files']);inherited=[dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
  assert read(O/'PRIOR_CLOSED_BARRIERS.json')['passed']
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  names=['v1862_remaining_routes_teb','v1863_remaining_routes_dwa','v1864_remaining_routes_rpccr_ns','v1865_remaining_routes_rpccr_ew','v1866_remaining_common_matrix','v1867_remaining_matrix_source_recovery','v1868_remaining_matrix_runtime_recovery']
  for name in names:
   for p in(R/'experiments'/name).iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['AUTHORIZATION.json','PLAN_LOCKED.json','PILOT_TASK.json','PRIOR_CLOSED_BARRIERS.json','EXACT_ORIGINAL_INPUTS.json','ROUTE_SOURCE_REUSE.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
  contract=load('v1852_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');assert contract.validate(plan,registry)
  auth=read(O/'AUTHORIZATION.json');boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();contract.time_admission(auth,time.time(),boot)
  ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
  for row in plan['assignments']:
   slot=next(x for x in ledger['slots']if x['method']==row['method']and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
   base=R/row['output_root'];assert not(base/'PILOT_ONCE_CLAIM.json').exists()and not(base/'COMPLETION.json').exists()
  for row in read(O/'ROUTE_SOURCE_REUSE.json')['files']:
   assert sha(R/row['path'])==sha(R/row['original_path'])==row['sha256']
   assert files[row['original_path']]==row['sha256'],'UNRECOVERED_ORIGINAL_ROUTE_SOURCE'
  for case in ['NORTH_SOUTH','EAST_WEST']:
   path=R/'runs/v1281_partial_reconnection_fixed24'/(case+'_STATIC_SOURCE.json');assert files[str(path.relative_to(R))]==sha(path)
  for row in read(O/'EXACT_ORIGINAL_INPUTS.json')['inputs']:
   assert sha(R/row['path'])==sha(R/row['original_path'])==row['sha256']
   assert files[row['path']]==row['sha256'],'CURRENT_INPUT_NOT_FROZEN'
  negatives=[]
  for kind in ['order','method','task','output']:
   bad=copy.deepcopy(plan)
   if kind=='order':bad['assignments'][0]['order']=1
   if kind=='method':bad['assignments'][0]['method']='SCCR'
   if kind=='task':bad['assignments'][0]['common_task']='common_01'
   if kind=='output':bad['assignments'][0]['output_root']='runs/elsewhere'
   try:contract.validate(bad,registry)
   except (AssertionError,KeyError):negatives.append(kind)
   else:raise AssertionError('INVALID_PLAN_ACCEPTED:'+kind)
  for kind in ['late','boot']:
   try:contract.time_admission(auth,auth['deadline_unix']-7199 if kind=='late'else time.time(),'wrong'if kind=='boot'else boot)
   except AssertionError:negatives.append(kind)
   else:raise AssertionError('INVALID_TIME_ACCEPTED')
  # Exact existing code reuse; no old numerical requalification.
  unchanged={}
  configs=[('v1862_remaining_routes_teb','v1856_evening_teb_complete_inputs'),('v1863_remaining_routes_dwa','v1857_evening_dwa_complete_inputs'),('v1864_remaining_routes_rpccr_ns','v1858_evening_rpccr_complete_inputs'),('v1865_remaining_routes_rpccr_ew','v1858_evening_rpccr_complete_inputs')]
  routefiles={r['path'] for r in read(O/'ROUTE_SOURCE_REUSE.json')['files']}
  for new,old in configs:
   unchanged[new]=[]
   for p in(R/'experiments'/old).glob('*.py'):
    q=R/'experiments'/new/p.name
    if str(q.relative_to(R))in routefiles:continue
    text=p.read_text().replace(old,new).replace('v1859_evening_complete_inputs','v1866_remaining_common_matrix')
    if 'rpccr_'in new:
     case='NORTH_SOUTH'if new.endswith('_ns')else'EAST_WEST'
     if p.name=='context.py':
      needle=" assert a['scope']=='RPCCR_COMMON_CONDITION_FULL_TASK'and a['assignment']==assignment"
      text=text.replace(needle,needle+f"\n assert assignment['case_id']=='{case}'and assignment['mechanism_variant']=='full'")
     if p.name=='driver.py':
      before="    static=R/'runs/v1281_partial_reconnection_fixed24/WEST_EAST_STATIC_SOURCE.json'\n    (out/'WEST_EAST_STATIC_SOURCE.json').write_bytes(static.read_bytes())"
      after=f"    assert task['case_id']=='{case}' and task['mechanism_variant']=='full'\n    static=R/'runs/v1281_partial_reconnection_fixed24/{case}_STATIC_SOURCE.json'\n    assert sha(static)==source[str(static.relative_to(R))], 'ROUTE_PUBLIC_PROPOSAL_IDENTITY'\n    (out/'{case}_STATIC_SOURCE.json').write_bytes(static.read_bytes())"
      assert before in text;text=text.replace(before,after)
    assert text==q.read_text(),'UNEXPECTED_PRODUCTION_CHANGE:'+str(q)
    unchanged[new].append(p.name)
  # Inspect original route binder and auditor definitions without importing
  # numerical executors. Actual numeric functions remain the exact old bytes.
  for path in ['v1765_ns_formal_binding/runtime_binding.py','v1818_prefix_auditor_exact_source/runtime_binding.py']:
   text=(R/'experiments'/path).read_text();ast.parse(text)
   assert 'cached.bind(output' in text and 'dispatch.execute('in text
  ew=R/'experiments/v1865_remaining_routes_rpccr_ew'
  original=R/'experiments/v1818_prefix_auditor_exact_source/worker_child.py';text=original.read_text()
  begin=text.index("  aid=os.environ.get('PHASE_FORMAL_ASSIGNMENT')");end=text.index('  import worker_pool',begin)
  child=(ew/'worker_child.py').read_text();new_begin=child.index('  from context import O,SOURCE');new_end=child.index('  import worker_pool',new_begin)
  assert text[:begin]==child[:new_begin]and text[end:]==child[new_end:],'EW_WORKER_NUMERICAL_BODY_CHANGED'
  assert files[str(original.relative_to(R))]==sha(original)
  validate=load('v1866_EW_worker_software_authority',ew/'worker_admission.py').validate
  worker_cases=[]
  for row in plan['assignments']:
   if row['production']!='v1865_remaining_routes_rpccr_ew':continue
   base=R/row['output_root'];task=read(base/'PILOT_TASK.json');now=time.time();mono=time.monotonic()
   adm=dict(scope='RPCCR_COMMON_CONDITION_FULL_TASK',models_authorized=True,assignment=task,source_freeze_sha256='SOFTWARE')
   window=dict(boot_id=boot,normal_end_unix=now+100,hard_stop_monotonic=mono+100)
   assert validate(base/'actual',base,task,adm,window,'SOFTWARE',now,mono,boot)
   for kind in ['out','method','authority','source','clock','boot']:
    bad=copy.deepcopy(adm);bad_task=copy.deepcopy(task)
    if kind=='authority':bad['models_authorized']=False
    if kind=='method':bad_task['common_method']='DWA';bad['assignment']=bad_task
    try:validate(base/'other'if kind=='out'else base/'actual',base,bad_task,bad,window,'WRONG'if kind=='source'else'SOFTWARE',now+101 if kind=='clock'else now,mono,'WRONG'if kind=='boot'else boot)
    except AssertionError:negatives.append(row['round_id']+'/worker/'+kind)
    else:raise AssertionError('WORKER_BAD_AUTHORITY_ACCEPTED:'+kind)
   worker_cases.append(row['round_id'])
  assert len(worker_cases)==4
  regression=load('v1852_real_admission_software_regression',C/'admission_regression.py').run(read,sha,load)
  assert regression['passed']and len(regression['valid_remaining_assignments'])==24
  put(O/'VALID_ADMISSION_SOFTWARE_PROOF.json',regression);negatives+=regression['negative_cases']
  # Every real unadmitted production entry rejects before numerical imports.
  for name,reason in [('v1862_remaining_routes_teb','TEB_NAVIGATION_NOT_ADMITTED'),('v1863_remaining_routes_dwa','DWA_NAVIGATION_NOT_ADMITTED'),('v1864_remaining_routes_rpccr_ns','RPCCR_COMMON_NOT_ADMITTED'),('v1865_remaining_routes_rpccr_ew','RPCCR_COMMON_NOT_ADMITTED')]:
   folder=R/'experiments'/name;prior=sys.modules.get('context');before=sys.path[:];load('context',folder/'context.py');sys.path.insert(0,str(folder))
   try:
    for entry in ['pilot_entry.py','driver.py']:
     try:runpy.run_path(str(folder/entry),run_name='__main__')
     except AssertionError as e:assert str(e)==reason;negatives.append(name+'/'+entry)
     else:raise AssertionError('UNADMITTED_NUMERICAL_ENTRY')
   finally:
    sys.path[:]=before
    if prior is None:sys.modules.pop('context',None)
    else:sys.modules['context']=prior
  assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited))
  put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,valid_admission_software_proof_path=str((O/'VALID_ADMISSION_SOFTWARE_PROOF.json').relative_to(R)),remaining24_fixed_order=True,original_methods_and_numeric_modules_byteidentical=unchanged,readonly_process_old_proof_reused='runs/v1844_evening_common_campaign/SOURCE_QUALIFICATION_PROOF.json',negative_cases=negatives,not_actual_runtime_qualification=True))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives),valid_admission_software_cases=24,original_alias_red_reproduced=True,old_algorithms_retained=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
