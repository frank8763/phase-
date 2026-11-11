"""Legacy false-positive reproduced with an actual CPU context; 0 models."""
import sys,os,json,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
from resource_policy import apply
policy=apply()
import mujoco
from mujoco.rendering.classic import gl_context
from OpenGL import GL
from cpu_backend import require_cpu_backend
os.environ['MUJOCO_GL']='egl';assert os.environ['MUJOCO_GL']!='osmesa';proof=require_cpu_backend();ctx=gl_context.GLContext(16,16);ctx.make_current();renderer=GL.glGetString(GL.GL_RENDERER).decode();ctx.free();assert'llvmpipe'in renderer.lower();negative=[]
for name in ['actual_EGL_backend','wrong_OpenGL_dispatch','CUDA_visible']:
 try:
  if name=='actual_EGL_backend':require_cpu_backend(type('Wrong',(),dict(__module__='mujoco.egl')),'OpenGL.platform.osmesa')
  elif name=='wrong_OpenGL_dispatch':require_cpu_backend(gl_context.GLContext,'OpenGL.platform.egl')
  else:os.environ['CUDA_VISIBLE_DEVICES']='0';require_cpu_backend()
 except AssertionError:negative.append(name)
 else:raise AssertionError('GPU_POLICY_NEGATIVE_ACCEPTED')
 finally:os.environ['CUDA_VISIBLE_DEVICES']=''
result=dict(passed=True,legacy_label_false_positive_reproduced=True,real_CPU_renderer=renderer,positive_actual_backend=proof,negative_cases=negative,models=0,integrations=0,hardware_GPU_used=False,resource_policy=policy);(R/'runs/v1064_cpu_backend_entry_20261111/CPU_BACKEND_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
