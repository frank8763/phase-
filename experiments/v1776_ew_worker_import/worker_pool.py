"""Original solve_job in one fresh spawn CPU2 process; parent actual is paused."""
import ast,concurrent.futures,hashlib,importlib.util,json,multiprocessing,os,sys,types
from pathlib import Path
from context import R,C,SOURCE,sha,read,load
accounting=dict(scope='original EW isolated analytical jobs only; not all modelwork',jobs=[],cpu=2,maximum_concurrent_workers=1,physical_model_factory_calls=0,total_modelwork_unknown=True)
_OUTPUT=None;_WINDOW=None;_SOURCE=None

def initialize(output,window,source):
 os.sched_setaffinity(0,{2});assert os.environ.get('PHASE_REPO')==str(R)
 assert not any(n in sys.modules for n in ['mujoco','vehicle','torch']),'WORKER_PHYSICAL_MODULE_NOT_ISOLATED'
 original=load('v1773_worker_context',R/'experiments/v1281_partial_reconnection_fixed24/worker_context.py');old=original.science()
 import planner,fast_predict,brake_reserve
 output=Path(output);planner.O=output
 proof=read(output/'CACHED_LIBRARY_BINDING.json');assert proof['numerical_bodies_unchanged']and not proof['compiler_fallback']
 targets={p['original']:p for p in proof['copies']}
 helper=load('v1773_exact_cache_identity',R/'experiments/v1635_original_cached_backends/cached_libraries.py')
 for module,path in [(planner,R/'experiments/v1067_causal_replan_brake_reserve/planner.py'),(fast_predict,R/'experiments/v1046_retreat_entry_timed_route/fast_predict.py')]:
  assert source[str(path.relative_to(R))]==sha(path)and helper.identity(module.library.__code__)==helper.identity(helper.original_code(path))
  record=next(p for p in targets.values()if ('analytical_' in Path(p['current']).name)==(module is fast_predict))
  expected_original='runs/v1635_original_cached_backends/analytical_rebuilt.so'if module is fast_predict else 'runs/v1281_partial_reconnection_fixed24/analytical_cache/1d946e4ed4b6172d3b54.so'
  assert record['original']==expected_original and record['sha256']==source[expected_original], 'WORKER_BINARY_SOURCE_IDENTITY'
  target=R/record['current'];assert target.is_relative_to(output/'analytical_cache')and not target.is_symlink()and sha(target)==record['sha256']
  tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='library')
  before=[ast.dump(n,include_attributes=False)for n in fn.body if isinstance(n,ast.Return)or(isinstance(n,ast.Assign)and not any(isinstance(t,ast.Name)and t.id in {'source','digest','cache','target'}for t in n.targets))]
  class OnlyCurrent(ast.NodeTransformer):
   def visit_Assign(self,n):
    if len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='cache':n.value=ast.Name(id='_current_cache',ctx=ast.Load())
    return n
   def visit_Expr(self,n):return None if isinstance(n.value,ast.Call)and ast.unparse(n.value.func)=='cache.mkdir'else n
   def visit_If(self,n):
    assert ast.unparse(n.test)in {'not target.is_file()','not target.exists()'}
    return ast.If(test=n.test,body=[ast.Raise(exc=ast.Call(func=ast.Name(id='AssertionError',ctx=ast.Load()),args=[ast.Constant('NO_WORKER_COMPILER_FALLBACK')],keywords=[]),cause=None)],orelse=[])
  fn=OnlyCurrent().visit(fn);after=[ast.dump(n,include_attributes=False)for n in fn.body if isinstance(n,ast.Return)or(isinstance(n,ast.Assign)and not any(isinstance(t,ast.Name)and t.id in {'source','digest','cache','target'}for t in n.targets))];assert before==after
  namespace=vars(module).copy();namespace['_current_cache']=output/'analytical_cache';exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(C/'worker_pool.py'),'exec'),namespace)
  inner=namespace['library']
  def guarded(inner=inner,target=target,expected=record['sha256']):
   assert sha(target)==expected and not target.is_symlink();return inner()
  module.library=guarded
 brake_reserve.library=planner.library
 # Child cannot write ANY filesystem artifact or create another physical model.
 def readonly(event,args):
  if event=='open'and len(args)>2 and isinstance(args[0],(str,bytes,os.PathLike)):
   mode=args[1];flags=args[2]or 0
   assert not(isinstance(mode,str)and any(c in mode for c in 'wax+'))and not(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),'EW_WORKER_FILESYSTEM_WRITE_REFUSED'
  if event in {'os.mkdir','os.remove','os.rename','os.rmdir'}:raise AssertionError('EW_WORKER_FILESYSTEM_MUTATION_REFUSED')
 sys.addaudithook(readonly)

class Tracked:
 def __init__(self,future,job):self.future=future;self.job=job
 def result(self,*a,**kw):
  result=self.future.result(*a,**kw);assert result['cpu']==2
  accounting['jobs'].append({k:result.get(k)for k in ['id','cpu','calls','analytical_cpp_native','partial_unknown','error','models','physical_native']})
  known=[x['analytical_cpp_native']for x in accounting['jobs']if type(x.get('analytical_cpp_native'))is int];assert sum(known)<=150000000,'EW_WORKER_SUBSET_NATIVE_LIMIT'
  return result
class Pool:
 def __init__(self,max_workers,mp_context):
  assert max_workers==4 and mp_context.get_start_method()=='spawn'
  self.pool=concurrent.futures.ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'),initializer=initialize,initargs=(_OUTPUT,_WINDOW,_SOURCE))
 def __enter__(self):self.pool.__enter__();return self
 def __exit__(self,*args):return self.pool.__exit__(*args)
 def submit(self,fn,job):
  assert fn.__name__=='solve_job'and Path(fn.__code__.co_filename)==R/'experiments/v1271_ew_joint_phase_validation/ew_retained_parallel.py'
  updated=dict(job,cpu=2);return Tracked(self.pool.submit(fn,updated),updated)
def bind(module,output,window,source):
 global _OUTPUT,_WINDOW,_SOURCE
 assert _OUTPUT is None,'WORKER_POOL_BIND_NO_RETRY';_OUTPUT=str(output);_WINDOW=window;_SOURCE=source
 path=R/'experiments/v1271_ew_joint_phase_validation/ew_retained_parallel.py';assert source[str(path.relative_to(R))]==sha(path)and Path(module.__file__).resolve()==path
 helper=load('v1773_function_identity',C/'audit_seams.py');helper.original_function(module,path,'generate');helper.original_function(module,path,'solve_job')
 original=module.generate;namespace=vars(module).copy();namespace['concurrent']=types.SimpleNamespace(futures=types.SimpleNamespace(ProcessPoolExecutor=Pool));module.generate=types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)
 assert module.generate.__code__ is original.__code__
 return dict(original_optimizer_generate_solve_job_code_unchanged=True,spawn_worker_physical_modules_absent=True,maximum_workers=1,cpu=2,original_job_deadlines_worklimits_and_fixed_order_unchanged=True)

def import_identity_probe():
 import importlib.util
 assert __name__=='worker_pool'and Path(importlib.util.find_spec('worker_pool').origin).resolve()==Path(__file__).resolve()
 assert sorted(os.sched_getaffinity(0))==[2]and not any(n in sys.modules for n in ['numpy','scipy','mujoco','vehicle','ctypes'])
 return dict(module_name=__name__,file=str(Path(__file__).resolve()),cpu=2,models=0,FFI_loads=0,physical_native=0)
