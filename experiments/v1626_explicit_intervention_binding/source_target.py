"""Import actual original-runtime seams, ban constructors and numerical calls."""
import ast,fcntl,hashlib,importlib.abc,os,signal,sys,time,traceback
from pathlib import Path
from context import C,O,R,OLD,put,read,sha,load

def main():
 start=time.monotonic();os.environ.update(MUJOCO_GL='osmesa',CUDA_VISIBLE_DEVICES='',PYOPENGL_PLATFORM='osmesa',MESA_SHADER_CACHE_DISABLE='true')
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1625_original_scope_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory','jax','OpenGL'}:raise AssertionError('BINDING_NO_PHYSICAL:'+name)
 sys.meta_path.insert(0,Ban())
 def profile(frame,event,arg):
  if event=='call':
   filename=Path(frame.f_code.co_filename)
   if filename.is_absolute()and filename.is_relative_to(R):
    name=frame.f_code.co_name;self_=frame.f_locals.get('self');cls=type(self_).__name__
    if name=='__init__'and any(k in cls for k in ['Predictor','Engine','Vehicle','Adapter','Allocator','Expander']):raise AssertionError('BINDING_NO_CONSTRUCTOR:'+cls)
    assert name not in {'create_vehicle','physical_binding','simulate','step','compute','predict','synthesize','generate','execute','navigate','advance'},'BINDING_NO_NUMERICAL_OR_POLICY:'+name
   assert time.monotonic()-start<120,'BINDING_SOURCE120S'
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,
             actual_runtime_qualified=False,source_only=True,original_contract=True)
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 sys.setprofile(profile)
 try:
  prior=read(R/'runs/v1624_original_contract_evaluation/SOURCE_QUALIFICATION.json');assert prior['passed']and prior['models']==0
  inherited=read(R/'runs/v1615_private_namespace_scope/SOURCE_FREEZE.json')['files']
  original=read(OLD/'WORKER_FREEZE.json')['files'];source=dict(inherited)
  for p,h in original.items():
   if p in source:assert source[p]==h,('INHERITED_ORIGINAL_SOURCE_CONFLICT',p)
   source[p]=h
  for folder in [C,R/'experiments/v1620_mechanism_boundary',R/'experiments/v1624_original_contract_evaluation',R/'experiments/v1625_original_runtime_binding']:
   for p in folder.iterdir():
    if p.is_file():source[str(p.relative_to(R))]=sha(p)
  for n in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:
   source[str((O/n).relative_to(R))]=sha(O/n)
  source['runs/v1624_original_contract_evaluation/SOURCE_QUALIFICATION.json']=sha(R/'runs/v1624_original_contract_evaluation/SOURCE_QUALIFICATION.json')
  assert all(sha(R/n)==h for n,h in source.items())
  from runtime_binding import bind
  now=time.time();mono=time.monotonic();window=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=now+1800,hard_stop_monotonic=mono+1800,normal_end_unix=now+600)
  runtime=bind(O,window,'full',prepared_sources=source)
  q=runtime['q'];assert runtime['original_contract']and not runtime['parallel_model_jobs']
  identities=dict(Predictor=str(Path(q.model.Predictor.step.__code__.co_filename).relative_to(R)),Engine=str(Path(q.accelerator.Engine.simulate.__code__.co_filename).relative_to(R)),owner=str(Path(runtime['owner'].navigate.__code__.co_filename).relative_to(R)),goal=str(Path(runtime['dispatch'].current_executor().goal_entry.execute.__code__.co_filename).relative_to(R)))
  assert identities['Predictor']=='experiments/v1159_bounded_steering_load/model.py'
  assert identities['Engine']=='experiments/v1159_bounded_steering_load/engine.py'
  assert identities['owner']=='experiments/v1281_partial_reconnection_fixed24/owner.py'
  assert identities['goal']=='experiments/v1218_fixed24_current/goal_package/goal_entry.py'
  runtime2=bind(O,window,'no_onward',prepared_sources=source)
  assert runtime2['intervention']['variant']=='no_onward'and not runtime2['intervention']['physical_authorized']
  assert source=={n:sha(R/n)for n in source}
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,physical_admission=False))
  result.update(passed=True,source_members=len(source),actual_definitions_and_binding_imported=True,
                exact_original_function_files=identities,old_source_suites_reused_not_rerun=True,
                constructors_or_model_or_policy_calls=0,driver_scope_refusal_reused_from_V1624=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps({k:result.get(k)for k in ['passed','first_error','models','source_members','wall_s']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
