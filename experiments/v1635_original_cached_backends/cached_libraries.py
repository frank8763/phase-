"""Draft readonly binary plumbing; never calls any numerical function."""
import ast
import hashlib
import types
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def bind(output,*,planner,fast,source):
 output=Path(output).resolve();assert output.is_relative_to(R/'runs')and output.is_dir()
 assert Path(planner.__file__).resolve()==R/'experiments/v1067_causal_replan_brake_reserve/planner.py'
 assert Path(fast.__file__).resolve()==R/'experiments/v1046_retreat_entry_timed_route/fast_predict.py'
 cpp=R/'experiments/v1067_causal_replan_brake_reserve/search.cpp'
 dependency=R/'experiments/v1046_retreat_entry_timed_route/fast_predict.cpp'
 for path in [cpp,dependency,Path(planner.__file__),Path(fast.__file__)]:assert source[str(path.relative_to(R))]==sha(path)
 combined=hashlib.sha256(cpp.read_bytes()+dependency.read_bytes()).hexdigest()
 expand_digest=sha(dependency)
 original_search=R/'runs/v1281_partial_reconnection_fixed24/analytical_cache'/(combined[:20]+'.so')
 original_fast=R/'runs/v1635_original_cached_backends/analytical_rebuilt.so'
 for path in [original_search,original_fast]:assert source[str(path.relative_to(R))]==sha(path),'UNREGISTERED_OR_CHANGED_ORIGINAL_BINARY'
 cache=output/'analytical_cache';cache.mkdir(exist_ok=False)
 copies=[(original_search,cache/(combined[:20]+'.so')),
         (original_fast,cache/('analytical_'+expand_digest[:16]+'.so'))]
 for before,after in copies:
  assert not after.exists();after.write_bytes(before.read_bytes());assert sha(after)==sha(before)
 assert planner.O==output
 tree=ast.parse(Path(fast.__file__).read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='library')
 replaced=0;removed=0
 class CacheOnly(ast.NodeTransformer):
  def visit_Assign(self,node):
   nonlocal replaced
   if len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id=='cache':
    replaced+=1;node.value=ast.Name(id='_registered_current_cache',ctx=ast.Load())
   return node
  def visit_Expr(self,node):
   nonlocal removed
   if isinstance(node.value,ast.Call)and ast.unparse(node.value.func)=='cache.mkdir':removed+=1;return None
   return node
 function=CacheOnly().visit(function);assert replaced==removed==1
 namespace=vars(fast).copy();namespace['_registered_current_cache']=cache
 exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(Path(__file__)),'exec'),namespace)
 assert isinstance(namespace['library'],types.FunctionType)
 fast.library=namespace['library']
 # Bothfunctions now resolve exactexisting digesttargets. They remain lazy:
 # no CDLLload, modelconstructor or simulate/expand/search/stop call here.
 return dict(source_only=True,FFI_loads=0,FFI_calls=0,
             copies=[dict(original=str(a.relative_to(R)),current=str(b.relative_to(R)),sha256=sha(b),bytes=b.stat().st_size)for a,b in copies],
             fast_library_AST_changes=dict(cache_rebinding=replaced,mkdir_removed=removed),
             numerical_bodies_unchanged=True,models=0,physical_authorized=False)
