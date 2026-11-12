"""Verify the loaded renderer, not a mutable legacy environment label."""
import os

def require_cpu_backend(backend_class=None,dispatch_module=None):
 if backend_class is None:
  from mujoco.rendering.classic import gl_context
  backend_class=gl_context.GLContext
 if dispatch_module is None:
  from OpenGL import platform
  dispatch_module=type(platform.PLATFORM).__module__
 module=backend_class.__module__
 assert 'osmesa'in module.lower()and 'osmesa'in dispatch_module.lower(),'ACTUAL_GPU_RENDER_BACKEND_FORBIDDEN'
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='','CUDA_DEVICE_VISIBILITY_CHANGED'
 os.environ['MUJOCO_GL']='osmesa';os.environ['PYOPENGL_PLATFORM']='osmesa'
 return dict(passed=True,actual_context_module=module,actual_OpenGL_dispatch_module=dispatch_module,hardware_GPU_used=False,legacy_environment_label_restored=True)
