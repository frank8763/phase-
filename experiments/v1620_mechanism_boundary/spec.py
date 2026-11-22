"""Prospective fixed design; no environment, solver or numerical imports."""
import copy
import hashlib
import json
import math
from pathlib import Path

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
TAG = 'RPCCR_MECHANISM_BOUNDARY_V1620_20261122'
STOP = 1795395600
VARIANTS = ('full', 'no_time', 'no_onward')


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def manifest():
    base = R / 'experiments/v1281_partial_reconnection_fixed24'
    old = json.loads((base / 'TASKS.json').read_text())
    templates = {t['case_id']: t for t in old if t['task_id'] in
                 {'main_slot01', 'main_slot09', 'main_slot17'}}
    tasks = []
    for route in ['WEST_EAST', 'NORTH_SOUTH', 'EAST_WEST']:
        template = templates[route]
        for direction in [-1, 1]:
            for replicate in [0, 1]:
                index = len(tasks)
                key = f'{TAG}|{route}|{direction}|{replicate}'
                bits = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big')
                # Midpoint quantization strictly avoids cos(phi)==0 boundaries.
                u = ((bits >> 11) + .5) / 2**53
                phase = -math.pi/2 + math.pi*u
                if direction < 0:
                    phase += math.pi
                phase %= 2*math.pi
                assert math.cos(phase)*direction > 0
                assert all(abs(math.atan2(math.sin(phase-t['phase']),
                           math.cos(phase-t['phase']))) > 1e-8 for t in old)
                task = copy.deepcopy(template)
                task.update(task_id=f'phase_{index+1:02}', seed=10170001+index,
                            phase=phase, run_id=f'v1620-phase_{index+1:02}',
                            output=str(O / f'phase_{index+1:02}'), run_root=str(O),
                            stage='prospective_phase_boundary', role='main',
                            scope='same_known_course_new_phase_only',
                            original_pool_task=None, slot=None,
                            initial_axis_motion_direction=('POSITIVE_AXIS' if direction>0 else 'NEGATIVE_AXIS'),
                            phase_design=dict(key=key, direction=direction,
                                              replicate=replicate, sha256_bits=bits))
                variants = (['full', 'no_onward'] if route == 'WEST_EAST' else
                            ['full', 'no_time'] if route == 'EAST_WEST' else ['full'])
                if (replicate + (direction > 0)) % 2:
                    variants = list(reversed(variants))
                assignments = [dict(assignment_id=task['task_id']+'__'+variant,
                                    task_id=task['task_id'], variant=variant,
                                    output=str(O / (task['task_id']+'__'+variant)))
                               for variant in variants]
                tasks.append(dict(task=task, variants=variants,
                                  assignments=assignments,
                                  inherited_task_sha256=digest(template)))
    return dict(schema=1, tag=TAG, method='disclosed_V1281_evaluation_fork',
                new_map=False, new_motion_class=False, task_count=12,
                assignment_count=sum(len(t['assignments']) for t in tasks),
                root_stop_unix=STOP, maximum_root_seconds=28800,
                physical_admission=False, tasks=tasks,
                source_tasklist_sha256=hashlib.sha256((base/'TASKS.json').read_bytes()).hexdigest())


def authority(scope):
    raise PermissionError('NO_NUMERIC_OR_ACTUAL_ADMISSION:' + scope)
