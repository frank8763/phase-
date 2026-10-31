"""Import/load only. No environment instance, reset, physical step, or training."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys

root = Path('/home/linghu/catkin_ws/src/mk-mini')
repo = Path(os.environ['PHASE_REPO'])
sys.path[:0] = [str(root / 'experiments/phase_rpccr_p0b76_online_gate_v1'),
                str(root / 'experiments/phase_rpccr_p0b68_v1'), str(root)]
import mujoco


def blocked(*args, **kwargs):
    raise RuntimeError('MIGRATION_MUST_NOT_SIMULATE')


for name in ('mj_step', 'mj_step1', 'mj_step2', 'mj_resetData', 'mj_resetDataKeyframe'):
    setattr(mujoco, name, blocked)

import search_worker as H
from contact_contract import GeometryCatalog, ContactRecorder
from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import MkMiniPhase22V1ContinuousCorridorEnv
from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import MkMiniPhase21V11CandidateRecoveryEnv
from training.phase21_risk_switch_fusion_sac.tests import eval_phase21_v3_exact_pair_5ep
from stable_baselines3 import SAC

model = SAC.load(str(H.B.MODEL), device='cpu')
sys.path.insert(0, str(repo / 'current'))
for name in ('runner', 'footprint_map_b69_v513', 'footprint_map_b70_v513',
             'phase_v345_runtime', 'v115_live_view'):
    spec = importlib.util.spec_from_file_location(name, repo / 'current' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

versions = {name: importlib.metadata.version(name) for name in
            ('numpy', 'torch', 'mujoco', 'gymnasium', 'stable-baselines3')}
modules = sorted({str(Path(m.__file__).resolve()) for m in sys.modules.values()
                  if getattr(m, '__file__', None) and str(m.__file__).startswith(str(root))})
assert not Path('/home/linghu/Documents/Codex/2026-10-30/new-chat/winkun').exists()
assert not Path('/home/linghu/mkmini_phase_rpccr_p0e_v1').exists()
print(json.dumps({'status': 'READY_PAUSED', 'local_modules': modules,
                  'model_sha256': hashlib.sha256(Path(H.B.MODEL).read_bytes()).hexdigest(),
                  'versions': versions,
                  'current_runner_sha256': hashlib.sha256((repo / 'current/runner.py').read_bytes()).hexdigest(),
                  'environment_instances': 0, 'simulation_steps': 0, 'training_updates': 0,
                  'stage_visible': False, 'original_phase_runs_visible': False}, indent=2))
