"""Original V1281 functions, explicit scope outputs, serialized original pools."""
import ast,concurrent.futures,copy,importlib.util,sys,types,subprocess
from context import C,O,R,OLD,load,read,sha,remaining

def function(path,name,globals_):
 tree=ast.parse(path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
 scope=globals_.copy();exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),scope)
 return scope[name]

class SerialExecutor:
 def __init__(self,*args,**kwargs):pass
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def submit(self,fn,job):
  job=copy.deepcopy(job);job['cpu']=2;future=concurrent.futures.Future()
  try:future.set_result(fn(job))
  except BaseException as error:future.set_exception(error)
  return future
 def map(self,fn,jobs):
  for job in jobs:yield self.submit(fn,job).result()

def serial_function(module,name):
 # Preserve code and every selection/proof/cap; substitute ONLY module-local
 # pool implementation. Never replace the global concurrent.futures module.
 namespace=vars(module).copy()
 namespace['concurrent']=types.SimpleNamespace(futures=types.SimpleNamespace(ProcessPoolExecutor=SerialExecutor))
 original=getattr(module,name)
 return types.FunctionType(original.__code__,namespace,original.__name__,original.__defaults__,original.__closure__)

def bind(output,window,variant,prepared_sources=None):
 assert variant in {'full','no_onward'} # EW awaits exact recovered proposals.
 sys.path.insert(0,str(OLD));original=load('v1624_readonly_worker_context',OLD/'worker_context.py')
 old=original.science();old.configure_owner(output,window['normal_end_unix'])
 import budget,kernel
 budget.O=output;budget.RAW=output;budget.LIMIT=224*1024**2
 budget.used=lambda:int(subprocess.check_output(['du','-sx','-B1',str(output)]).split()[0])
 def original_scope_check(extra=0):
  assert extra>=0 and remaining(window)>0
  assert kernel.O==output
  assert budget.used()+extra<=224*1024**2,'ORIGINAL_SCOPE_EVIDENCE_CAP'
  # The actual OutputBoundary additionally charges bytes before EVERY write.
  return True
 budget.check=original_scope_check;kernel.O=output;kernel.HARD_END=window['normal_end_unix']
 # No historical library/reference loader or old campaign main is called.
 dispatch=load('v1624_original_route_dispatch',OLD/'route_dispatch.py')
 current=dispatch.current_executor()
 transforms=load('v1624_explicit_ablation_transform',C/'transforms.py')
 goal_module=sys.modules[current.goal_entry.generate.__module__]
 generated,proof=transforms.bind(goal_module,prepared_sources if prepared_sources is not None else read(O/'SOURCE_FREEZE.json')['files'],kind='onward',variant=variant)
 current.goal_entry.generate=generated
 owner=types.ModuleType('v1624_current_normal_owner');owner.__file__=str(OLD/'owner.py')
 exec(compile((OLD/'owner.py').read_text(),str(OLD/'owner.py'),'exec'),owner.__dict__)
 owner.execute=lambda *args:dispatch.execute(*args,output=output,remaining_fn=lambda:remaining(window))
 # The only WE model pool in its original partial-static fallback.
 reconnect=load('v1624_original_reconnect',OLD/'reconnect.py')
 reconnect.renew_from_complete_partial=serial_function(reconnect,'renew_from_complete_partial')
 sys.modules['reconnect']=reconnect
 return dict(old=old,owner=owner,packet=old.packet,q=old.q,dispatch=dispatch,
             intervention=proof,original=original,original_contract=True,
             parallel_model_jobs=False)
