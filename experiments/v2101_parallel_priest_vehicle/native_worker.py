"""One fresh PRIEST author solve on CPU6; zero Phase model or plant access."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from context import R,C,O,SOURCE,read,load,sha,digest,native_authority
import importlib.abc,importlib.metadata,json,os,resource,time,traceback,types

def main():
 a,source=native_authority();resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(600,610));os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,n,*args):
   if n.split('.')[0]in{'mujoco','torch','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('PRIEST_NATIVE_NO_PHASE_MODEL:'+n)
 sys.meta_path.insert(0,Ban());counts=None
 try:
  raw=sys.stdin.buffer.read(1024**2+1);assert len(raw)<=1024**2;frame=json.loads(raw);current=frame['current'];request=frame['request'];authority=read(O/'actual/PRIEST_OPTIMIZER_ADMISSION.json')
  assert authority['scope']=='PRIEST_OPTIMIZER_ONLY'and not authority['models_authorized']and authority['input_sha256']==current['input_sha256']and authority['request_sha256']==request['request_sha256']
  assert current['kind']=='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT'and current['fixed_origin_native']==0 and not current['fullstate_or_actor_truth_transmitted']and 'fullstate'not in current
  deps=read(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json');assert all(source[x['path']]==x['sha256']==sha(R/x['path'])for x in deps['files']);sys.path.insert(0,str(R/'runs/v1491_priest_dependency_target/site'))
  expected=read(R/'runs/v1504_priest_namespace_worker/OPTIMIZER_ONLY_ADMISSION.json')['qualified_distribution_versions'];assert {k:importlib.metadata.version(k)for k in expected}==expected
  import jax,jax.numpy as jnp,numpy as np
  assert jax.config.x64_enabled and all(d.platform=='cpu'for d in jax.devices())
  port=load('PRIEST_exact_cpu_port',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();assert port['ported_sha256']==request['port_identity']['ported_sha256']==authority['kernel_source_sha256']
  load('bernstein_coeff_order10_arbitinterval',R/'runs/v1484_baseline_disposition_priest/upstream/priest/src/bernstein_coeff_order10_arbitinterval.py');m=types.ModuleType('source_bound_PRIEST_CPU6');m.__file__=str(C/'author_core_never_written.py');sys.modules[m.__name__]=m;exec(compile(port['source'],m.__file__,'exec'),m.__dict__)
  observer=load('PRIEST_cpu6_threads',C/'thread_observation.py');before=observer.observe('BEFORE_SOLVE')
  def receipt(value):print('PRIEST_EVENT '+json.dumps(value,allow_nan=False),flush=True)
  budget=load('PRIEST_original_work_accounting',C/'work_budget.py').WorkBudget(receipt=receipt,absolute_deadline_unix=authority['absolute_deadline_unix'],hard_stop_monotonic=authority['hard_stop_monotonic']);counts=budget.counts
  answer=load('PRIEST_exact_author_call',C/'optimizer_call.py').run(request,current=current,kernel=types.SimpleNamespace(module=m,author_sha256=port['author_sha256'],ported_sha256=port['ported_sha256']),jax=jax,jnp=jnp,np=np,budget=budget,authority=authority)
  print('PRIEST_REPLY '+json.dumps(dict(passed=True,answer=answer,input_bytes=len(raw),input_byte_sha256=__import__('hashlib').sha256(raw).hexdigest(),threads_before=before,threads_after=observer.observe('AFTER_SOLVE'),models=0,physics=0),allow_nan=False),flush=True);return 0
 except BaseException as e:print('PRIEST_ERROR '+json.dumps(dict(error=repr(e),traceback=traceback.format_exc(),counts=counts,models=0,physics=0)),flush=True);return 1
 finally:print('PRIEST_CLOSED '+json.dumps(dict(counts=counts,models=0,physics=0,internal_optimizer_kinematic_work=None)),flush=True)
if __name__=='__main__':raise SystemExit(main())
