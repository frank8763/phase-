"""Exact import readiness only; zero calls to minimize or other optimizer APIs."""
from context import R,C,ROOT,P,read,put,sha
import sys,os,json
assert os.sched_getaffinity(0)=={3}
site=R/'runs/v1491_priest_dependency_target/site';files=read(P/'SOURCE_FREEZE.json')['files'];sys.path.insert(0,str(site));import numpy as np;import scipy;from scipy.optimize import minimize
from pathlib import Path
assert scipy.__version__=='1.14.1'and Path(scipy.__file__).resolve().is_relative_to(site)
seen={}
for name,m in list(sys.modules.items()):
 if name=='scipy'or name.startswith('scipy.'):
  path=getattr(m,'__file__',None)
  if path:
   p=Path(path).resolve();assert p.is_relative_to(site);n=str(p.relative_to(R));assert files[n]==sha(p),n;seen[n]=files[n]
assert seen and callable(minimize)
put(ROOT/'DEPENDENCY_IMPORT_PROOF.json',dict(passed=True,interpreter=sys.version,NumPy_version=np.__version__,SciPy_version=scipy.__version__,SciPy_minimize_module=minimize.__module__,imported_SciPy_modules_exactSHA=len(seen),source_files=seen,NLP_calls=0,models=0,physics=0,replay=0,nonphysical_numeric_library_loads_internal_unknown=True));print(json.dumps(dict(passed=True,imported_exact_modules=len(seen),NLP_calls=0)))
