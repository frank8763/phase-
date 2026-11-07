"""No-physical-model import and candidate/state interface qualification."""
import ast
import importlib
import sys


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('PREPARATION_FORBIDS_PHYSICAL_MODELS')


sys.meta_path.insert(0, NoModels())
from common import *

ROOT.mkdir(parents=True, exist_ok=True)
assert read(GPU / 'QUALIFICATION.json')['component_passed']
states = {}
with (CELL / 'motion_estimate.jsonl').open() as stream:
    for line in stream:
        state = json.loads(line)
        if state['step'] in STEPS:
            assert state['information_mode'] == 'TRACKED' and not state['hidden_world_geometry_used']
            states[state['step']] = state
assert tuple(states) == STEPS
contract = read(CELL / 'ACTUATOR_COMMAND_CONTRACT.json')
limits, rate = np.asarray(contract['limits']), np.asarray(contract['rate'])
trace = read(CELL / 'trace.json')
checks = []
for step in STEPS:
    proposal = np.load(GPU / f'proposal_step{step:04d}.npz')
    commands = proposal['controls']
    previous = np.asarray(trace[step - 1]['applied_ctrl'][:4])
    assert commands.shape == (4, 42, 4) and np.isfinite(commands).all()
    assert np.all(commands >= limits[:, 0] - 1e-12) and np.all(commands <= limits[:, 1] + 1e-12)
    delta = np.diff(np.concatenate((np.tile(previous, (4, 1, 1)), commands), axis=1), axis=1)
    assert np.all(abs(delta) <= rate + 1e-12)
    plan = read(CELL / f'planning_{step:04d}.json')
    assert np.max(abs(np.asarray(plan['pose']) - np.asarray(trace[step-1]['pose']))) <= 1e-8
    dense = dense_poses(plan['pose'], np.repeat([plan['pose']], 336, axis=0))
    assert dense.shape == (673, 3)
    checks.append(dict(step=step, candidates=4, commands=42, native_ticks=336,
                       tracked_causal_state=True, command_bounds_and_slew=True))
for module in ['geometry_predictor', 'self_geometry', 'motion_tracker', 'independent_norm', 'dynamic_contact']:
    importlib.import_module(module)
for path in OWN.glob('*.py'):
    ast.parse(path.read_text())
save(ROOT / 'FIXED_STATES.json', states)
save(ROOT / 'PREPARATION.json', dict(passed=True, checks=checks, physical_models=0,
                                    physics_integrations=0, qualified_imports=5,
                                    prepared_steps=list(STEPS)))
print('NATIVE_INTERFACE_PREPARATION_PASS', flush=True)
