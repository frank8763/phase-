"""One current archived t0 author PRIEST solve on CPU7, no Phase vehicle."""
from common import R,C,S,read,put,sha,load,authority
import importlib.abc,importlib.metadata,os,resource,sys,time,traceback,types
def main():
 a,source=authority('PRIEST');out=S/'priest_output';assert not(out/'ONCE.json').exists();put(out/'ONCE.json',dict(pid=os.getpid(),CPU=7,models=0,unix=time.time()));resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,)*2);resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(600,610));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'mujoco','torch','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('PRIEST_NO_PHASE_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());result=dict(closed=False,passed=False,models=0,physics=0,replay=0,formal_tasks=0,author_constructor_attempts=0,author_optimizer_attempts=0,author_optimizer_returns=0,internal_optimizer_kinematic_work=None,first_error=None);start=time.monotonic();budget=None
 try:
  deps=read(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json');assert all(sha(R/x['path'])==x['sha256']for x in deps['files']);sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'))
  expected=read(R/'runs/v1504_priest_namespace_worker/OPTIMIZER_ONLY_ADMISSION.json')['qualified_distribution_versions'];versions={k:importlib.metadata.version(k)for k in expected};assert versions==expected
  import jax,jax.numpy as jnp,numpy as np
  assert jax.config.x64_enabled and all(d.platform=='cpu'for d in jax.devices());port=load('exact_author_CPU_source_port',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();request=read(S/'OPTIMIZER_REQUEST.json');current=read(S/'CURRENT_INPUT.json');assert port['ported_sha256']==request['port_identity']['ported_sha256']==a['kernel_source_sha256']and a['request_sha256']==request['request_sha256']and a['input_sha256']==current['input_sha256']
  helper=R/'runs/v1484_baseline_disposition_priest/upstream/priest/src/bernstein_coeff_order10_arbitinterval.py';load('bernstein_coeff_order10_arbitinterval',helper);module=types.ModuleType('source_bound_author_PRIEST_CPU');module.__file__=str(C/'ported_author_core_not_written.py');sys.modules[module.__name__]=module;exec(compile(port['source'],module.__file__,'exec'),module.__dict__);kernel=types.SimpleNamespace(module=module,author_sha256=port['author_sha256'],ported_sha256=port['ported_sha256']);observer=load('source_bound_namespace_thread_observer',C/'thread_observation.py');put(out/'THREADS_AFTER_KERNEL.json',observer.observe('AFTER_KERNEL'))
  work=load('new_scope_exact_work_counter',C/'work_budget.py');budget=work.WorkBudget(receipt=lambda v:put(out/'WORK_PROGRESS.json',v),absolute_deadline_unix=a['absolute_deadline_unix'],hard_stop_monotonic=a['hard_stop_monotonic']);call=load('exact_author_call_new_admission_scope',C/'optimizer_call.py');output=call.run(request,current=current,kernel=kernel,jax=jax,jnp=jnp,np=np,budget=budget,authority=a);put(out/'THREADS_AFTER_OPTIMIZER.json',observer.observe('AFTER_OPTIMIZER'));put(out/'POLYNOMIAL_PROPOSAL.json',output)
  result.update(passed=True,author_constructor_attempts=budget.counts['constructor_attempts'],author_constructor_returns=budget.counts['constructor_returns'],author_optimizer_attempts=budget.counts['optimizer_call_attempts'],author_optimizer_returns=budget.counts['optimizer_calls'],work_accounting_subset=budget.counts,proposal_only=True,full_Phase_response_not_qualified=True,actual_controller_not_qualified=True,versions=versions,archived_current_t0_not_fresh_wire=True)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc())
  if budget is not None:result['work_accounting_subset']=budget.counts
 finally:result.update(closed=True,wall_s=time.monotonic()-start,all_source_SHA_after=all(sha(R/n)==h for n,h in source.items()));put(out/'RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
