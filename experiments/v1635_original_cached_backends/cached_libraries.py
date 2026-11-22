"""Exact original cached DLL plumbing; no compiler fallback or numerical call."""
import ast
import hashlib
import types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def identity(code):
 return (code.co_code,code.co_names,code.co_flags,code.co_varnames,tuple(identity(c)if isinstance(c,types.CodeType)else c for c in code.co_consts))

def original_code(path):
 code=compile(path.read_bytes(),str(path),'exec',dont_inherit=True)
 return next(c for c in code.co_consts if isinstance(c,types.CodeType)and c.co_name=='library')

def bind(output,*,planner,fast,source):
 output=Path(output).resolve();assert output.is_relative_to(R/'runs')and output.is_dir()
 assert not hasattr(planner,'_registered_cache_binding')and not hasattr(fast,'_registered_cache_binding'),'CACHE_BIND_NO_RETRY'
 paths=[R/'experiments/v1067_causal_replan_brake_reserve/planner.py',R/'experiments/v1046_retreat_entry_timed_route/fast_predict.py']
 for module,path in zip([planner,fast],paths):
  assert Path(module.__file__).resolve()==path and source[str(path.relative_to(R))]==sha(path),'ORIGINAL_LIBRARY_SOURCE_CHANGED'
  assert identity(module.library.__code__)==identity(original_code(path)),'ORIGINAL_LIBRARY_CODE_CHANGED'
 cpp=R/'experiments/v1067_causal_replan_brake_reserve/search.cpp';dependency=R/'experiments/v1046_retreat_entry_timed_route/fast_predict.cpp'
 for path in [cpp,dependency]:assert source[str(path.relative_to(R))]==sha(path),'ORIGINAL_CPP_SOURCE_CHANGED'
 combined=hashlib.sha256(cpp.read_bytes()+dependency.read_bytes()).hexdigest();expand_digest=sha(dependency)
 original_search=R/'runs/v1281_partial_reconnection_fixed24/analytical_cache'/(combined[:20]+'.so')
 original_fast=R/'runs/v1635_original_cached_backends/analytical_rebuilt.so'
 originals=[original_search,original_fast]
 for path in originals:assert source[str(path.relative_to(R))]==sha(path),'UNREGISTERED_OR_CHANGED_ORIGINAL_BINARY'
 assert planner.O==output,'PLANNER_OUTPUT_MISMATCH'
 cache=output/'analytical_cache';assert not cache.exists(),'CURRENT_CACHE_MUST_BE_NEW'
 # Poison before the first write: a partial installation cannot be retried.
 marker=dict(passed=False,poisoned=True,output=str(output));planner._registered_cache_binding=fast._registered_cache_binding=marker
 cache.mkdir()
 targets=[cache/(combined[:20]+'.so'),cache/('analytical_'+expand_digest[:16]+'.so')]
 copies=[];functions=[]
 for module,path,before,target in zip([planner,fast],paths,originals,targets):
  expected=source[str(before.relative_to(R))];target.write_bytes(before.read_bytes());assert sha(target)==expected
  tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='library')
  originals_tail=[ast.dump(n,include_attributes=False)for n in fn.body if isinstance(n,ast.Return)or (isinstance(n,ast.Assign)and not any(isinstance(t,ast.Name)and t.id in {'source','digest','cache','target'}for t in n.targets))]
  class CacheOnly(ast.NodeTransformer):
   rebound=removed=refused=0
   def visit_Assign(self,node):
    if len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id=='cache':
     self.rebound+=1;node.value=ast.Name(id='_registered_current_cache',ctx=ast.Load())
    return node
   def visit_Expr(self,node):
    if isinstance(node.value,ast.Call)and ast.unparse(node.value.func)=='cache.mkdir':self.removed+=1;return None
    return node
   def visit_If(self,node):
    assert ast.unparse(node.test)in {'not target.is_file()','not target.exists()'},'UNEXPECTED_LIBRARY_CONDITIONAL'
    self.refused+=1
    return ast.If(test=node.test,body=[ast.Raise(exc=ast.Call(func=ast.Name(id='AssertionError',ctx=ast.Load()),args=[ast.Constant('REGISTERED_BINARY_MISSING_NO_COMPILER')],keywords=[]),cause=None)],orelse=[])
  transform=CacheOnly();fn=transform.visit(fn);assert transform.rebound==transform.refused==1
  assert transform.removed==(1 if module is fast else 0)
  new_tail=[ast.dump(n,include_attributes=False)for n in fn.body if isinstance(n,ast.Return)or (isinstance(n,ast.Assign)and not any(isinstance(t,ast.Name)and t.id in {'source','digest','cache','target'}for t in n.targets))]
  assert originals_tail==new_tail,'DLL_SIGNATURE_OR_RETURN_CHANGED'
  namespace=vars(module).copy();namespace['_registered_current_cache']=cache
  exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(Path(__file__)),'exec'),namespace)
  inner=namespace['library']
  def guarded(inner=inner,target=target,expected=expected):
   assert marker['passed']and not marker['poisoned'],'CACHE_BINDING_NOT_COMPLETE'
   assert target.is_file()and not target.is_symlink()and sha(target)==expected,'REGISTERED_BINARY_MISSING_OR_CHANGED'
   return inner()
  functions.append(guarded);copies.append(dict(original=str(before.relative_to(R)),current=str(target.relative_to(R)),sha256=expected,bytes=target.stat().st_size))
 planner.library,fast.library=functions
 marker.update(passed=True,poisoned=False)
 return dict(source_only=True,FFI_loads=0,FFI_calls=0,copies=copies,compiler_fallback=False,
             numerical_bodies_unchanged=True,ctypes_signatures_and_return_AST_identical=True,models=0,physical_authorized=False)
