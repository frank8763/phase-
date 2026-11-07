"""Zero-model witness: exercise the original planner with a deterministic clock."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'experiments/v842_staged_long_navigation/planner.py'


class NoModels:
    def find_spec(self, name, *args):
        if name == 'mujoco' or name.startswith('mujoco.'):
            raise RuntimeError('ZERO_MODEL_BUDGET_WITNESS')


class Clock:
    elapsed = 0.

    def monotonic(self):
        return self.elapsed


class Field:
    config = SimpleNamespace(resolution=.1)
    clearance = np.ones((2, 2))

    def __init__(self, clock):
        self.clock = clock

    def pose_values(self, poses):
        if len(poses) > 1:
            self.clock.elapsed += 3.
        return np.ones(len(poses))


def run(limit):
    specification = importlib.util.spec_from_file_location('original_planner_budget_witness', SOURCE)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    clock = Clock()
    module.time = clock  # Does not patch process/global time or any repository file.
    _, result = module.spatial_search(Field(clock), [0., 0., 0.], [3., 0.], .6, .4,
                                      budget=2., work_limit=limit)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assert-wall-budget', action='store_true')
    args = parser.parse_args()
    sys.meta_path.insert(0, NoModels())
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    work_limited = run(2)
    clock_limited = run(None)
    assert work_limited['expanded'] == 2 and clock_limited['expanded'] == 1
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
    result = dict(scope='DETERMINISTIC_ORIGINAL_CODE_WITNESS_NOT_A_REAL_TIME_BENCHMARK',
                  original_source=str(SOURCE.relative_to(REPO)), original_sha256=before,
                  configured_budget_s=2., work_limit=2,
                  with_work_limit=work_limited, without_work_limit=clock_limited,
                  wall_condition_disabled_with_work_limit=True,
                  models=0, integrations=0, real_saved_map_queries=0,
                  source_changed=False)
    output = REPO / 'runs/overnight_plan_20261106/PLANNER_BUDGET_WITNESS.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if args.assert_wall_budget:
        assert work_limited['wall_s'] <= 2., 'WORK_LIMIT_DISABLES_CONFIGURED_WALL_BUDGET'


if __name__ == '__main__':
    main()
