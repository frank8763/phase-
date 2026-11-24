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
  base=R/'runs/v1852_evening_checked_campaign'
  assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed']
  recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
  for n,h in read(base/'POST_SOURCE_STORAGE_BARRIER.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  # Earlier split qualification supplement is explicitly checked, not inferred.
  for a,h in [('index_path','index_sha256'),('full_remote_proof_path','full_remote_proof_sha256')]:assert sha(R/recovery[a])==recovery[h]
  files.update(read(base/'SOURCE_FREEZE.json')['files']);inherited=[dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
  assert read(O/'PRIOR_CLOSED_BARRIERS.json')['passed']
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  names=['v1856_evening_teb_complete_inputs','v1857_evening_dwa_complete_inputs','v1858_evening_rpccr_complete_inputs','v1859_evening_complete_inputs','v1860_evening_complete_source_recovery','v1861_evening_complete_runtime_recovery']
  for name in names:
   for p in(R/'experiments'/name).iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['AUTHORIZATION.json','PLAN_LOCKED.json','PILOT_TASK.json','PRIOR_CLOSED_BARRIERS.json','EXACT_ORIGINAL_INPUTS.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
  contract=load('v1852_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');assert contract.validate(plan,registry)
  auth=read(O/'AUTHORIZATION.json');boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();contract.time_admission(auth,time.time(),boot)
  original_plan=read(R/plan['previous_plan_path']);assert sha(R/plan['previous_plan_path'])==plan['previous_plan_sha256']
  ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
  for row,old in zip(plan['assignments'],original_plan['assignments'][1:]):
   assert (row['round_id'],row['method'],row['common_task'],row['original_order'])==(old['round_id'],old['method'],old['common_task'],old['order'])
   slot=next(x for x in ledger['slots']if x['method']==row['method']and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
   oldtask=read(R/old['output_root']/'PILOT_TASK.json');task=read(R/row['output_root']/'PILOT_TASK.json')
   assert {k:v for k,v in oldtask.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in task.items()if k not in {'output','run_root','run_id'}}
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
  # ALL numerical/algorithm files are byte-identical to original evening source.
  unchanged={}
  for new,old in [('v1856_evening_teb_complete_inputs','v1849_evening_teb_bound'),('v1857_evening_dwa_complete_inputs','v1850_evening_dwa_bound'),('v1858_evening_rpccr_complete_inputs','v1851_evening_rpccr_bound')]:
   unchanged[new]=[]
   for p in(R/'experiments'/old).glob('*.py'):
    q=R/'experiments'/new/p.name
    if p.name in {'context.py','owner.py','pilot_entry.py','native_worker.py'}:continue
    assert p.read_bytes()==q.read_bytes(),'UNCHANGED_BODY:'+str(q);unchanged[new].append(p.name)
   # Other changed files can differ ONLY by namespace replacements, prior
   # closed barriers and the RPCCR SOURCE=O deletion. No numeric edits.
   for name in ['context.py','pilot_entry.py','native_worker.py']:
    p=R/'experiments'/old/name;q=R/'experiments'/new/name
    if not p.exists():continue
    text=p.read_text().replace(old,new).replace('v1852_evening_checked_campaign','v1859_evening_complete_inputs')
    if new=='v1858_evening_rpccr_complete_inputs':text=text.replace(';SOURCE=O;ROOT=',';ROOT=')
    assert text==q.read_text(),'UNEXPECTED_INTERFACE_CHANGE:'+str(q)
  regression=load('v1852_real_admission_software_regression',C/'admission_regression.py').run(read,sha,load)
  assert regression['passed']and len(regression['valid_remaining_assignments'])==5
  put(O/'VALID_ADMISSION_SOFTWARE_PROOF.json',regression);negatives+=regression['negative_cases']
  # Every real unadmitted production entry rejects before numerical imports.
  for name,reason in [('v1856_evening_teb_complete_inputs','TEB_NAVIGATION_NOT_ADMITTED'),('v1857_evening_dwa_complete_inputs','DWA_NAVIGATION_NOT_ADMITTED'),('v1858_evening_rpccr_complete_inputs','RPCCR_COMMON_NOT_ADMITTED')]:
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
  put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,valid_admission_software_proof_path=str((O/'VALID_ADMISSION_SOFTWARE_PROOF.json').relative_to(R)),remaining5_fixed_order=True,original_methods_and_numeric_modules_byteidentical=unchanged,readonly_process_old_proof_reused='runs/v1844_evening_common_campaign/SOURCE_QUALIFICATION_PROOF.json',negative_cases=negatives,not_actual_runtime_qualification=True))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives),valid_admission_software_cases=5,original_alias_red_reproduced=True,old_algorithms_retained=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
