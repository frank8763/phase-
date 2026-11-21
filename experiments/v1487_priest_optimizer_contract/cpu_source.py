"""Produce an auditable CPU-only source port without compiling/importing it."""
import ast
import copy
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
CAPTURE=R/'runs/v1484_baseline_disposition_priest'
EXPECTED='dbe9cf267c78a9f56e6169fb4c73aca9d1a20d787b0f53562e2a769e43527555'

def prepare_cpu_source():
 raw=(CAPTURE/'upstream/priest/src/mpc_non_dy.py').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==EXPECTED,'PINNED_AUTHOR_SOURCE_CHANGED'
 tree=ast.parse(raw.decode());original=copy.deepcopy(tree)
 deprecated=[n for n in tree.body if isinstance(n,ast.ImportFrom)and n.module=='jax.ops']
 assert len(deprecated)==1 and [a.name for a in deprecated[0].names]==['index_update','index']
 assert not any(isinstance(n,ast.Name)and isinstance(n.ctx,ast.Load)and n.id=='index_update'for n in ast.walk(tree))
 # Every remaining `index` read is a function-local assigned nearest-point index.
 for fn in [n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)]:
  reads=[n for n in ast.walk(fn)if isinstance(n,ast.Name)and isinstance(n.ctx,ast.Load)and n.id=='index']
  if reads:assert any(isinstance(n,ast.Name)and isinstance(n.ctx,ast.Store)and n.id=='index'for n in ast.walk(fn))
 tree.body.remove(deprecated[0]);changed=[]
 for fn in [n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)]:
  for decorator in fn.decorator_list:
   if isinstance(decorator,ast.Call):
    for keyword in decorator.keywords:
     if keyword.arg=='backend':
      assert isinstance(keyword.value,ast.Constant)and keyword.value.value=='gpu'
      keyword.value=ast.Constant(value='cpu');changed.append(fn.name)
 assert changed==['path_spline','compute_contouring_error','compute_obs_traj_prediction','compute_boundary_vec','compute_warm_traj','compute_traj_guess','compute_projection','initial_alpha_d']
 orig_cls=next(n for n in original.body if isinstance(n,ast.ClassDef));new_cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
 assert len(orig_cls.body)==len(new_cls.body)
 for before,after in zip(orig_cls.body,new_cls.body):
  if isinstance(before,ast.FunctionDef):assert ast.dump(ast.Module(body=before.body,type_ignores=[]))==ast.dump(ast.Module(body=after.body,type_ignores=[]))
  else:assert ast.dump(before)==ast.dump(after)
 source=ast.unparse(ast.fix_missing_locations(tree))+'\n'
 return dict(source=source,author_sha256=EXPECTED,ported_sha256=hashlib.sha256(source.encode()).hexdigest(),cpu_backend_methods=changed,removed_unused_import='from jax.ops import index_update, index',numerical_method_bodies_AST_identical=True,author_module_executed=False,runtime_compatibility_qualified=False,requires=['jax','jaxlib','numpy','scipy','matplotlib'])
