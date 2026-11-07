"""A bounded saved-input probe of the original planner. No models or physics."""
import copy
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
import signal
import sys
import time
from pathlib import Path

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
import numpy as np

repo = Path(__file__).resolve().parents[2]
own = Path(__file__).parent
root = repo / 'runs/v823_global_continuation_diagnosis/renewal_probe'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('V823_RENEWAL_FORBIDS_MODELS_AND_INTEGRATIONS')

sys.meta_path.insert(0, NoPhysics())
sys.path.insert(0, str(repo / 'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
sys.path.insert(0, str(repo / 'experiments/v821_norm_route_development'))
from exact_footprint import build
from current_guide import attach
from planner import search
spec = importlib.util.spec_from_file_location('saved_renewal_F', repo / 'current/footprint_map_b70_v513.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

assert read(root.parent / 'COMPLETION.json')['status'] == 'FIXED_ZERO_MODEL_DIAGNOSIS_COMPLETE'
assert not root.exists(), 'OUTPUT_EXISTS_NO_RESTART'
original_freeze = read(own / 'INPUT_FREEZE.json')['files']
for name, expected in original_freeze.items():
    assert sha(repo / name) == expected, name
frozen = read(own / 'RENEWAL_INPUT_FREEZE.json')['files']
for name, expected in frozen.items():
    assert sha(repo / name) == expected, name
guard = (repo / 'REVIEW_PENDING').read_bytes()
root.mkdir()
started = time.time()
deadline = started + 600
window = dict(started_unix=started, absolute_deadline_unix=deadline, round_closed=False,
              models=0, integrations=0, fixed_observation_interval=[266, 500],
              max_original_search_calls=4)
dump(root / 'ROUND_WINDOW.json', window)
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('RENEWAL_600S_LIMIT')))
signal.alarm(600)
rows = []
queries = []
status = 'RUNNING'
try:
    cell = repo / 'runs/v821_norm_route_development/main_slot02/paired/geometry_memory'
    states = {x['step']: x for x in map(json.loads, (cell / 'motion_estimate.jsonl').read_text().splitlines())}
    executions = {x['step']: x for x in map(json.loads, (cell / 'v648_execution.jsonl').read_text().splitlines())}
    protocol = read(cell.parent / 'STATIC_PROTOCOL.json')
    template = read(cell / 'planning_0265.json')['causal_route_input']

    def make_input(step):
        world = copy.deepcopy(template)
        world['rectangles'] = [*protocol['known_rectangles'], states[step]['current_outer_rectangle']]
        world['circles'] = copy.deepcopy(protocol['known_circles'])
        q = np.asarray(executions[step - 1]['qpos_full'])
        yaw = math.atan2(2 * (q[3]*q[6] + q[4]*q[5]), 1 - 2 * (q[5]**2 + q[6]**2))
        pose = np.r_[q[:2], yaw]
        world['start'] = pose.tolist()
        field = build(F, world)
        field.base_heuristic = F.base._heuristic_grid
        attach(field, states[step])
        field.free = field.clearance >= .15 - field.config.resolution / math.sqrt(2)
        guide = field.base_heuristic(field, np.asarray(world['goal']))
        index = field.indices([pose[:2]])[0]
        finite = bool((index >= 0).all() and (index < guide.shape).all() and np.isfinite(guide[tuple(index)]))
        return world, pose, field, finite

    first_finite = None
    for step in range(266, 501):
        if not states[step]['observed_this_frame']:
            continue
        world, pose, field, finite = make_input(step)
        rows.append(dict(step=step, age_s=states[step]['age_s'], goal_guide_finite=finite))
        if finite and first_finite is None:
            first_finite = step
    dump(root / 'OBSERVATION_CONNECTIVITY.json', dict(records=rows, first_finite_observed_step=first_finite))
    fixed_steps = list(dict.fromkeys([x for x in (first_finite, 500) if x is not None]))
    print(json.dumps(dict(first_finite_observed_step=first_finite, original_planner_steps=fixed_steps)), flush=True)
    for step in fixed_steps:
        world, pose, field, finite = make_input(step)
        dump(root / f'INPUT_{step:04d}.json', dict(world=world, pose=pose.tolist(), motion_state=states[step]))
        first, stats = search(field, pose, world['goal'], world['wheel_base'], world['max_steer'],
            guard=.18, budget=2., dense_requested_guard=True, work_limit=4000)
        records = [dict(role='ORIGINAL_PREFERRED4000', stats=stats, path=None if first is None else first.tolist())]
        if stats['status'] != 'GLOBAL_GOAL_PATH':
            second, stats2 = search(field, pose, world['goal'], world['wheel_base'], world['max_steer'],
                guard=.155, budget=8., resolution=.05, heading_bins=144,
                dense_requested_guard=True, work_limit=16000)
            records.append(dict(role='ORIGINAL_FALLBACK16000', stats=stats2, path=None if second is None else second.tolist()))
            if second is None and first is not None:
                chosen, chosen_stats = first, stats
            else:
                chosen, chosen_stats = second, stats2
        else:
            chosen, chosen_stats = first, stats
        item = dict(step=step, goal_guide_finite=finite, records=records,
                    selected_status=chosen_stats['status'], models=0, integrations=0,
                    remaining_goal_m=None if chosen is None else float(np.linalg.norm(chosen[-1,:2]-world['goal'])),
                    reference_only_not_native_execution_certificate=True)
        dump(root / f'ORIGINAL_SEARCH_{step:04d}.json', item)
        queries.append(dict(step=step, selected_status=item['selected_status'], remaining_goal_m=item['remaining_goal_m'],
                            original_search_calls=len(records)))
        print(json.dumps(queries[-1]), flush=True)
    status = 'FIXED_RENEWAL_REFERENCE_DIAGNOSIS_COMPLETE'
except BaseException as error:
    import traceback
    status = 'STOPPED_EXCEPTION'
    dump(root / 'ERROR.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
finally:
    signal.alarm(0)
    same_guard = (repo / 'REVIEW_PENDING').read_bytes() == guard
    original_unchanged = all(sha(repo / name) == expected for name, expected in original_freeze.items())
    window.update(round_closed=True, status=status, elapsed_s=time.time()-started)
    dump(root / 'ROUND_WINDOW.json', window)
    dump(root / 'COMPLETION.json', dict(status=status, observed_grid_queries=len(rows), queries=queries,
        models=0, integrations=0, original_sources_and_inputs_unchanged=original_unchanged,
        review_guard_bytes_unchanged=same_guard, no_new_algorithm_or_control=True))
print(json.dumps(read(root / 'COMPLETION.json')), flush=True)
