"""One new fixed-plan/authority/process SOURCE; no old numerical suite rerun."""
import ast,copy,fcntl,importlib.abc,json,os,runpy,sys,time,traceback,selectors
from context import C,O,R,read,put,sha,load,digest
def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1844_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','ctypes','kernel','vehicle','factory','planner','fast_predict','scipy','OpenGL','rclpy'}:raise AssertionError('EVENING_SOURCE_NO_NUMERICAL:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,optimizer_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  inherited=[]
  for name in ['v1834_teb_common_entry_gate','v1810_rpccr_common_phase','v1818_prefix_auditor_exact_source']:
   base=R/'runs'/name;assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed']
   recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
   for k,v in read(base/'SOURCE_FREEZE.json')['files'].items():assert k not in files or files[k]==v;files[k]=v
   inherited.append(dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json')))
  for row in read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')['slots']:
   if row['registered']:
    assert row['closed']and row['remote_closed']
    # Original first common DWA/RPCCR use source-version roots; old TEB too.
    base=R/row['source_version'];bar=read(base/'POST_ROUND_STORAGE_BARRIER.json');assert bar['passed']
    assert sha(base/'POST_ROUND_STORAGE_BARRIER.json')==row['remote_barrier_sha256']
  for name in ['v1840_teb_readonly_process','v1841_evening_teb','v1842_evening_dwa','v1843_evening_rpccr','v1844_evening_common_campaign','v1845_evening_common_source_recovery','v1846_evening_runtime_recovery']:
   for p in(R/'experiments'/name).iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','PROCESS_BOUNDARY_PROOF.json','RED_REPRODUCTION.json','EXACT_NATIVE_ALIASES.json']:
   p=R/'runs/v1840_teb_readonly_process'/name;files[str(p.relative_to(R))]=sha(p)
  fixproof=read(R/'runs/v1840_teb_readonly_process/PROCESS_BOUNDARY_PROOF.json')
  assert fixproof['passed']and fixproof['old_real_Popen_DEVNULL_error_reproduced']and fixproof['production_spawn_same_original_boundaries_passed']and not fixproof['raw_writable_descriptor_granted']
  assert read(R/'runs/v1840_teb_readonly_process/SOURCE_OUTER_CLOSED.json')['passed']
  for name in ['AUTHORIZATION.json','PLAN_LOCKED.json','PILOT_TASK.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  for p in(O/'rounds').rglob('*.json'):files[str(p.relative_to(R))]=sha(p)
  p=R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json';files[str(p.relative_to(R))]=sha(p)
  contract=load('v1844_fixed_campaign_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(p);assert contract.validate(plan,registry)
  auth=read(O/'AUTHORIZATION.json');boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();contract.time_admission(auth,time.time(),boot)
  negatives=[]
  for kind in ['order','method','task','output']:
   bad=copy.deepcopy(plan)
   if kind=='order':bad['assignments'][0]['order']=1
   if kind=='method':bad['assignments'][0]['method']='SCCR'
   if kind=='task':bad['assignments'][0]['common_task']='common_01'
   if kind=='output':bad['assignments'][0]['output_root']='runs/elsewhere'
   try:contract.validate(bad,registry)
   except (AssertionError,KeyError):negatives.append(kind)
   else:raise AssertionError('INVALID_EVENING_PLAN_ALLOWED:'+kind)
  for kind in ['late','boot']:
   try:contract.time_admission(auth,auth['deadline_unix']-7199 if kind=='late'else time.time(),'wrong'if kind=='boot'else boot)
   except AssertionError:negatives.append(kind)
   else:raise AssertionError('INVALID_TIME_ADMISSION_ALLOWED')
  unchanged={}
  for new,old in [('v1841_evening_teb','v1834_teb_common_entry_gate'),('v1842_evening_dwa','v1806_dwa_common_phase'),('v1843_evening_rpccr','v1810_rpccr_common_phase')]:
   names=['driver.py','runtime_binding.py','resources.py','capture.py','response.py','work.py','history_binding.py','transforms.py','error_stop.py']if new!='v1843_evening_rpccr'else ['driver.py','runtime_binding.py','resources.py','capture.py','work.py','history_binding.py','transforms.py','error_stop.py','audit_binding.py','audit_seams.py','clock_window.py']
   unchanged[new]=[]
   for name in names:
    a=R/'experiments'/new/name;b=R/'experiments'/old/name;assert a.read_bytes()==b.read_bytes(),'NUMERICAL_BODY_CHANGED:'+str(a);unchanged[new].append(name)
  teb=R/'experiments/v1841_evening_teb';assert(teb/'spawn.py').read_bytes()==(R/'experiments/v1840_teb_readonly_process/spawn.py').read_bytes()
  for name in ['frames.py','velocity.py','api.py','session_contract.py','response.py','navigation.py']:
   if name=='velocity.py':continue
   assert(teb/name).read_bytes()==(R/'experiments/v1834_teb_common_entry_gate'/name).read_bytes()
  # Full production Client.start in the original OutputBoundary and original
  # namespace. Only numerical worker argv is replaced by explicit software
  # EOF/write-denial child. No admission is fabricated and no native DLL loaded.
  previous_context=sys.modules.get('context');prior_path=sys.path[:];prior_env=os.environ.get('PHASE_EVENING_ASSIGNMENT')
  os.environ['PHASE_EVENING_ASSIGNMENT']='common_02__TEB'
  current=load('context',teb/'context.py');sys.path.insert(0,str(teb));client=load('v1844_real_current_client',teb/'client.py');original_load=client.load
  def fixture_load(name,path):
   module=original_load(name,path)
   if Path(path)==teb/'native_namespace.py':
    original=module.command
    def command(argv,output):
     assert str(teb/'native_worker.py')in argv
     copied=[str(R/'experiments/v1840_teb_readonly_process/child.py')if x==str(teb/'native_worker.py')else x for x in argv]
     return original(copied,output)
    module.command=command
   return module
  from pathlib import Path
  client.load=fixture_load;obj=client.Client.__new__(client.Client);obj.source=files;obj.process=None;obj.closed=False;obj.out=O/'PRODUCTION_PROCESS_FIXTURE';obj.native=obj.out/'teb_native';obj.identity=None;obj.selector=None
  for name in ['build','tmp','build/empty_cwd','build/home','requests']:(obj.native/name).mkdir(parents=True,exist_ok=False)
  boundary=load('v1844_exact_OutputBoundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charged=[]
  def charge(path,size):
   assert path.is_relative_to(O)and size>=0;charged.append(size);assert sum(charged)<1024**2
  def save(name,value):put(obj.out/name,value)
  obj.save=save
  try:
   with boundary.OutputBoundary(O,charge):
    obj.start();data,_=obj.process.communicate(timeout=10)
    assert obj.process.returncode==0 and len(data)<16384
    answer=json.loads(data.decode().splitlines()[-1]);assert answer['passed']and answer['stdin_eof']and answer['readonly_namespace']
   assert obj.identity and not Path('/proc',str(obj.identity['pid'])).exists()
  finally:
   if obj.process is not None and obj.process.poll()is None:obj.process.kill();obj.process.wait(timeout=5)
   sys.path[:]=prior_path
   if previous_context is None:sys.modules.pop('context',None)
   else:sys.modules['context']=previous_context
   if prior_env is None:os.environ.pop('PHASE_EVENING_ASSIGNMENT',None)
   else:os.environ['PHASE_EVENING_ASSIGNMENT']=prior_env
  # Exercise every real no-admission CLI with its actual method context.
  for name,reason in [('v1841_evening_teb','TEB_NAVIGATION_NOT_ADMITTED'),('v1842_evening_dwa','DWA_NAVIGATION_NOT_ADMITTED'),('v1843_evening_rpccr','RPCCR_COMMON_NOT_ADMITTED')]:
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
  put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,fixed9task_order_and_authority_verified=True,deadline_2100_and7200reserve_verified=True,original_methods_and_numeric_modules_byteidentical=unchanged,original_output_boundary_and_native_namespace_retained=True,real_TEB_Client_start_with_software_fixture_passed=True,software_fixture_not_TEB_or_physics=True,readonly_spawn_regression_proof_path='runs/v1840_teb_readonly_process/PROCESS_BOUNDARY_PROOF.json',no_old_numeric_suite_repeated=True,negative_cases=negatives,not_actual_runtime_qualification=True))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives),new_software_process_spawns=1,old_algorithms_retained=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
