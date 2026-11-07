"""Probe CUDA arithmetic only, with all MuJoCo imports blocked."""
import json
import os
from pathlib import Path
import sys
import time


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('GPU_PROPOSAL_ONLY_NO_PHYSICAL_MODELS')


sys.meta_path.insert(0, NoModels())
assert os.environ.get('PHASE_GPU_COMPONENT_ONLY') == '1'
assert os.environ['CUDA_VISIBLE_DEVICES'] == '0'
import torch

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
assert torch.cuda.is_available(), 'CUDA_NOT_AVAILABLE_NO_CPU_FALLBACK'
torch.cuda.set_per_process_memory_fraction(.25, 0)
start = time.perf_counter()
value = torch.arange(128, device='cuda', dtype=torch.float64)
assert float((value * value).sum().cpu()) == sum(i * i for i in range(128))
torch.cuda.synchronize()
assert time.time() < float(os.environ['PHASE_GPU_COMPONENT_DEADLINE'])
result = dict(status='CUDA_ARITHMETIC_AND_ISOLATION_PASS', device=torch.cuda.get_device_name(0),
              torch_version=torch.__version__, cuda_build=torch.version.cuda,
              compute_capability=list(torch.cuda.get_device_capability(0)),
              architecture_list=torch.cuda.get_arch_list(), first_arithmetic_s=time.perf_counter()-start,
              gpu_memory_allocated_bytes=torch.cuda.memory_allocated(), models=0,
              physics_integrations=0, proposal_model_steps=0, training_updates=0)
output = Path(os.environ['PHASE_RUNS']) / 'v844_gpu_proposal_qualification'
(output / 'GPU_PROBE.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result), flush=True)
