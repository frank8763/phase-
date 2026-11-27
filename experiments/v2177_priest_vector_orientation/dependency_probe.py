"""Real pinned SciPy import under original output boundary, no optimization."""
from context import R,C,ROOT,P,read,sha,load
from pathlib import Path
import os,sys,json
assert os.sched_getaffinity(0)=={3}and not(ROOT/'SOURCE_ONCE.json').exists()
output=ROOT/'dependency_probe_output';assert output.is_dir()
site=R/'runs/v1491_priest_dependency_target/site';pins=read(P/'SOURCE_FREEZE.json')['files'];io=load('C2177_pinned_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
from write_budget import Budget
budget=Budget(output)
with io.OutputBoundary(output,budget.reserve):
 sys.path.insert(0,str(site));import numpy as np;import scipy;from scipy.optimize import minimize
 assert scipy.__version__=='1.14.1'and Path(scipy.__file__).resolve().is_relative_to(site)
 seen={}
 for name,m in list(sys.modules.items()):
  if name=='scipy'or name.startswith('scipy.'):
   f=getattr(m,'__file__',None)
   if f:
    p=Path(f).resolve();assert p.is_relative_to(site);n=str(p.relative_to(R));assert pins[n]==sha(p),'PINNED_SCIPY_SOURCE_CHANGED:'+n;seen[n]=pins[n]
 import collocation,normalized,runner
 assert len(collocation.Projection(read(ROOT/'PUBLIC_VECTOR_INPUT.json')).initial)==92
 assert 'torch'not in sys.modules and 'mujoco'not in sys.modules and 'jax'not in sys.modules
 proof=dict(passed=True,scope='NEW_REAL_READONLY_NAMESPACE_PINNED_SCIPY_IMPORT_ONLY',SciPy_version=scipy.__version__,NumPy_version=np.__version__,interpreter=sys.version,imported_exact_SciPy_modules=len(seen),source_files=seen,optimizer_calls=0,models_NN_physics=0,original_output_boundary_used=True,nonphysical_numeric_library_loads_internal_unknown=True)
 print(json.dumps(proof))
