"""Import/version/device preflight without constructing a physical model."""
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / 'runs/v846_parallel_backend_qualification'
sys.path.insert(0, str(ROOT / 'deps'))
assert os.environ.get('PHASE_GPU_BACKEND_COMPONENT') == '1'
import warp as wp
import mujoco_warp as mjw
import mujoco

assert mujoco.__version__ == '3.9.0'
assert importlib.metadata.version('mujoco-warp') == '3.9.0.1'
assert wp.__version__ == '1.13.0'
wp.config.kernel_cache_dir = str(ROOT / 'warp_cache')
wp.init()
device = wp.get_device('cuda:0')
assert device.is_cuda
for path in Path(__file__).parent.glob('*.py'):
    ast.parse(path.read_text())
result = dict(status='GPU_PARALLEL_BACKEND_IMPORT_PASS', physical_models=0, physics_integrations=0,
              mujoco_version=mujoco.__version__, warp_version=wp.__version__,
              backend_version=mjw.__version__, device=str(device),
              shared_environment_changed=False, training_updates=0)
(ROOT / 'PREPARATION.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
