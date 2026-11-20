"""Real isolated OSMesa GL context; no vehicle/model initialization."""
import json
import os
from pathlib import Path
import sys
os.environ.update(MUJOCO_GL='osmesa', PYOPENGL_PLATFORM='osmesa', CUDA_VISIBLE_DEVICES='', LIBGL_ALWAYS_SOFTWARE='1')
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
import mujoco
from cpu_backend import require_cpu_backend
proof = require_cpu_backend()
context = mujoco.GLContext(1, 1)
context.make_current()
from OpenGL.GL import glGetString, GL_RENDERER
renderer = glGetString(GL_RENDERER).decode()
assert 'llvmpipe' in renderer.lower() or 'soft' in renderer.lower(), 'SOFTWARE_CPU_RENDERER_REQUIRED'
context.free()
print(json.dumps(dict(passed=True, actual_renderer=renderer, backend=proof, models=0, native_integrations=0)))
