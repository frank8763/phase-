"""Four fixed saved inputs, actual pure planner seam, zero model construction."""
import hashlib
import importlib.abc
import importlib.util
import json
from pathlib import Path
import signal
import sys
import time
import numpy as np

own = Path(__file__).parent
repo = own.parents[1]
out = repo / 'runs/v810_forward_reference_global/pre_navigation'
out.mkdir(exist_ok=False)

class NoPhysics(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname == 'mujoco' or fullname.startswith('mujoco.'):
            raise RuntimeError('ZERO_MODEL_QUALIFICATION_FORBIDS_MUJOCO')

sys.meta_path.insert(0, NoPhysics())
sys.path.insert(0, str(own))
sys.path.insert(0, str(repo / 'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1'))
from exact_footprint import build
from planner import search
from timed_reference import attach, route_world, scheduled_samples, HORIZON

spec = importlib.util.spec_from_file_location('qualification_footprint', repo / 'current/footprint_map_b70_v513.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
freeze = read(own / 'CANDIDATE_FREEZE.json')
assert all(sha(repo / p) == h for p, h in freeze['files'].items())
cell = repo / 'runs/v809_time_reference_global/main_slot01/paired/geometry_memory'
states = {x['step']: x for x in map(json.loads, (cell / 'motion_estimate.jsonl').open())}
records = []
started = time.time()
deadline = min(started + 600, read(own / 'DEVELOPMENT_WINDOW.json')['absolute_deadline_unix'])
window = dict(started_unix=started, absolute_deadline_unix=deadline, round_closed=False, models=0, integrations=0)
def dump(name, value):
    (out / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

dump('ROUND_WINDOW.json', window)
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('FIXED_QUALIFICATION_600S')))
signal.alarm(max(1, int(deadline - time.time())))
status = 'RUNNING'
try:
    for fixed in read(own / 'QUALIFICATION_INPUTS.json'):
        source = repo / fixed['source']
        assert sha(source) == fixed['sha256']
        old = read(source)
        step = fixed['step']
        state = states[step]
        world, metadata = route_world(old['causal_input'], state)
        field = build(F, world)
        field.base_heuristic = F.base._heuristic_grid
        attach(field, state)
        start, goal = np.asarray(old['pose']), np.array([4., -2.])
        path, stats = search(field, start, goal, world['wheel_base'], world['max_steer'],
            guard=.18, budget=2., dense_requested_guard=True, work_limit=4000)
        if stats['status'] != 'GLOBAL_GOAL_PATH':
            preferred, preferred_stats = path, stats
            path, stats = search(field, start, goal, world['wheel_base'], world['max_steer'],
                guard=.155, budget=8., resolution=.05, heading_bins=144,
                dense_requested_guard=True, work_limit=16000)
            if path is None and preferred is not None:
                path, stats = preferred, dict(preferred_stats)
            stats['preferred_search'] = preferred_stats
        old_path = np.asarray(old['path'])
        row = dict(step=step, input_file=fixed['source'], input_sha256=fixed['sha256'],
            causal_state=state, causal_world=world, start=start.tolist(), goal=goal.tolist(),
            metadata=metadata, path=None if path is None else path.tolist(), stats=stats,
            old_status=old['stats']['status'], old_reverse_nodes=int(np.sum(old_path[:, 3] < 0)),
            old_endpoint_goal_distance_m=float(np.linalg.norm(old_path[-1, :2] - goal)))
        if path is not None:
            schedule = np.asarray(stats['reference_arrival_times_s'])
            dense, dtimes = scheduled_samples(path, schedule)
            value = field.reference_values(dense, dtimes)
            assert value.min() >= stats['guard_m'] - 1e-8
            np.savez_compressed(out / f'step{step:04d}.npz', path=path, arrivals=schedule,
                dense=dense, times=dtimes, values=value)
            row.update(saved_arrays=f'step{step:04d}.npz',
                new_endpoint_goal_distance_m=float(np.linalg.norm(path[-1, :2] - goal)),
                new_reverse_nodes=int(np.sum(path[:, 3] < 0)),
                within_horizon_samples=int(np.sum(dtimes <= HORIZON)),
                uncertified_guidance_samples=int(np.sum(dtimes > HORIZON)))
        records.append(row)
        dump('RESULTS.json', records)
        print(json.dumps(dict(step=step, old_reverse=row['old_reverse_nodes'],
            new_reverse=row.get('new_reverse_nodes'), new_status=stats['status'],
            remaining=row.get('new_endpoint_goal_distance_m'),
            policy=stats.get('forward_reference_preference'))), flush=True)
    status = 'FIXED_FORWARD_REFERENCE_SEARCH_COMPLETE'
except BaseException as exc:
    import traceback
    status = 'STOPPED_EXCEPTION'
    dump('ERROR.json', dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc()))
finally:
    signal.alarm(0)
    window.update(round_closed=True, status=status, elapsed_s=time.time() - started)
    dump('ROUND_WINDOW.json', window)
    dump('COMPLETION.json', dict(status=status, records=records, models=0, integrations=0))

