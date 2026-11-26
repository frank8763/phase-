"""Cold OSMesa loader seam; no MuJoCo import, model or graphics context."""
from pathlib import Path
import hashlib,importlib.abc,json,os,sys
C=Path(__file__).resolve().parent;R=C.parents[1]
assert os.environ.get('PHASE_GL_METADATA_PROBE')=='1'and os.sched_getaffinity(0)=={6}
class NoPlant(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','jax','kernel','factory','vehicle','planner','fast_predict'}:raise AssertionError('COLD_GL_METADATA_NO_MODEL:'+name)
sys.meta_path.insert(0,NoPlant());sys.path.insert(0,str(C));import cpu_policy
cpu_policy.install()
from OpenGL import GL
assert bool(GL.glGetError),'COLD_OSMESA_GL_SYMBOL_MISSING'
paths={line.split(None,5)[5]for line in Path('/proc/self/maps').read_text().splitlines()if len(line.split(None,5))==6 and 'libOSMesa.so' in line}
expected=R/'runs/v1063_entry_preparation_20261111/mesa_runtime/usr/lib/x86_64-linux-gnu/libOSMesa.so.8.0.0'
assert str(expected)in paths and all(Path(p).resolve()==expected.resolve()for p in paths)
assert 'mujoco'not in sys.modules
print(json.dumps(dict(passed=True,OSMesa_actual_mapped_paths=sorted(paths),OSMesa_sha256=hashlib.sha256(expected.read_bytes()).hexdigest(),GL_error_symbol_resolved=True,graphics_context_created=False,MuJoCo_imports=0,models=0,algorithm_DLLs=0,queries=0,physical_steps=0,actual_CPU_report=cpu_policy.report(),GL_loader_internal_calls=None)))
