"""Exact production admission functions with explicit in-memory software metadata.
No fake admission file is written. No model, numerical module, DLL or FFI is used.
Only not-yet-created once/window/source proof metadata is supplied in memory;
real task/registry/plan/path resolution and function code execute unchanged.
"""
import copy,importlib.util,os,sys,time,types
from pathlib import Path
R=Path(__file__).resolve().parents[2];S=R/'runs/v1889_teb_remaining_exact'
def run(read,sha,load):
 plan=read(S/'PLAN_LOCKED.json')['assignments'];before=os.environ.get('PHASE_EVENING_ASSIGNMENT');original_is_file=Path.is_file
 outcomes=[];negative=[]
 def exercise(folder,rid,mutation=None):
  os.environ['PHASE_EVENING_ASSIGNMENT']=rid
  m=load('v1852_admission_'+folder.name,folder/'context.py');task=read(S/'rounds'/rid/'PILOT_TASK.json');out=S/'rounds'/rid
  # The real global/per-round resolver must agree before any simulated grant.
  if folder.name=='v1888_teb_unapplied_refusal_exact':
   assert m.SOURCE==S and m.O==out and m.C==folder,'GLOBAL_SOURCE_OUTPUT_ALIAS'
  scope={'TEB':'TEB_COMMON_CONDITION_FULL_TASK','DWA':'DWA_COMMON_CONDITION_FULL_TASK','RP-CCR':'RPCCR_COMMON_CONDITION_FULL_TASK'}[task['common_method']]
  now=time.time();mono=time.monotonic();a=dict(scope=scope,assignment=task,models_authorized=True,common_registry_sha256=sha(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json'),source_freeze_sha256='explicit-memory-software-fixture')
  w=dict(started_unix=now,absolute_deadline_unix=now+5400,started_monotonic=mono,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
  memory={out/'PILOT_ADMISSION.json':a,out/'PILOT_WINDOW.json':w,out/'SOURCE_FREEZE.json':dict(files={str((folder/'context.py').relative_to(R)):sha(folder/'context.py')}),out/'SOURCE_QUALIFICATION.json':dict(passed=True),out/'CURRENT_SOURCE_REMOTE_RECOVERY.json':dict(passed=True,all_frozen_members_remote_chain_covered=True)}
  if mutation=='authority':a['models_authorized']=False
  if mutation=='seed':a['assignment']=dict(task,seed=-1)
  if mutation=='clock':w['absolute_deadline_unix']=now-1
  if mutation=='source':a['source_freeze_sha256']='WRONG'
  if mutation=='qualification':memory[out/'SOURCE_QUALIFICATION.json']['passed']=False
  if mutation=='remote':memory[out/'CURRENT_SOURCE_REMOTE_RECOVERY.json']['passed']=False
  reads=[]
  def reader(p):
   p=Path(p);reads.append(str(p.relative_to(R)));return copy.deepcopy(memory[p])if p in memory else read(p)
  def hashfile(p):return 'explicit-memory-software-fixture'if Path(p)==out/'SOURCE_FREEZE.json'else sha(Path(p))
  Path.is_file=lambda p:True if p in {out/'PILOT_ADMISSION.json',out/'PILOT_ONCE_CLAIM.json'} else original_is_file(p)
  namespace=dict(m.__dict__,read=reader,sha=hashfile)
  namespace['sources']=types.FunctionType(m.sources.__code__,namespace)
  function=types.FunctionType(m.admission.__code__,namespace)
  try:
   value=function()if task['common_method']=='RP-CCR'else function(task)
   assert str((S/'PLAN_LOCKED.json').relative_to(R))in reads
   assert value[0]['assignment']==task and value[2], 'ADMISSION_MUST_REACH_EXACT_SOURCE_CHECK'
   # Execute exact real driver.run function through task/admission/limits reads
   # and stop at the first software module load. No numerical import or guard.
   import ast
   tree=ast.parse((folder/'driver.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
   module=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(module)
   class BootstrapReached(Exception):pass
   def stop_before_load(name,path):
    assert str(path).endswith('task_cache.py');raise BootstrapReached()
   driver_namespace=dict(namespace,Path=Path,admission=function,load=stop_before_load)
   exec(compile(module,str(folder/'driver.py'),'exec'),driver_namespace)
   try:driver_namespace['run']()
   except BootstrapReached:pass
   else:raise AssertionError('DID_NOT_REACH_REAL_DRIVER_BOOTSTRAP')
   return dict(real_driver_task_admission_limits_bootstrap_passed=True,round_id=rid,production=folder.name,real_admission_code_SHA=__import__('hashlib').sha256(__import__('marshal').dumps(m.admission.__code__)).hexdigest(),requested_paths=reads,passed=True,software_metadata_only=True)
  finally:Path.is_file=original_is_file
 try:
  prior=read(R/'runs/v1880_final_three_checked/VALID_ADMISSION_SOFTWARE_PROOF.json');assert prior['passed']
  red=prior['red_original_exact_admission'];missing_input_red=prior['original_missing_limits_driver_red']
  for row in plan:
   folder=R/'experiments'/row['production'];outcomes.append(exercise(folder,row['round_id']))
   for kind in ['authority','seed','clock','source','qualification','remote']:
    try:exercise(folder,row['round_id'],kind)
    except AssertionError:negative.append(row['round_id']+'/'+kind)
    else:raise AssertionError('INVALID_SOFTWARE_ADMISSION_ACCEPTED:'+kind)
 finally:
  Path.is_file=original_is_file
  if before is None:os.environ.pop('PHASE_EVENING_ASSIGNMENT',None)
  else:os.environ['PHASE_EVENING_ASSIGNMENT']=before
 return dict(passed=True,original_missing_limits_driver_red=missing_input_red,red_original_exact_admission=red,valid_remaining_assignments=outcomes,negative_cases=negative,no_actual_admission_files_written=True,software_metadata_not_model_or_actual_qualification=True,models=0,FFI_calls=0)
