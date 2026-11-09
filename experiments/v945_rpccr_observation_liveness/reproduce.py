"""Specific V943 monitor regression; synthetic age, not the unsaved fault packet."""
import argparse
import copy
import importlib.abc
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'runs/v945_rpccr_observation_liveness'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'vehicle', 'factory', 'physical', 'rclpy'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)


sys.meta_path.insert(0, NoModel())
sys.path.insert(0, str(ROOT/'experiments/v938_rpccr_recovery_segments'))


def load_transaction(path):
    spec = importlib.util.spec_from_file_location('tested_transaction', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', action='store_true')
    args = parser.parse_args()
    folder = Path(__file__).parent if args.candidate else ROOT/'experiments/v938_rpccr_recovery_segments'
    module = load_transaction(folder/'transaction.py')
    first = json.loads((ROOT/'runs/v936_rpccr_corridor_search/ENTRY_QUALIFICATION.json').read_text())['first_actual_trigger']
    packet, source = copy.deepcopy(first['packet']), copy.deepcopy(first['source'])
    # At an exactly representable synthetic timestamp avoid mislabelling float boundaries.
    now = 1.
    packet['body_measured_at'] = now-.1
    source['decision_at'] = now
    source['source_age_s'] = .01
    m = module.RecoveryTransaction([4., -2.], [])
    m.mode = 'FOLLOW_RECOVERY'
    m.path = [[0., 0., 0.], [1., 0., 0.]]
    m.path_sha256 = module.fingerprint(m.path)
    m.installed_at = 0.
    error = None
    try:
        m.monitor(packet, source, now)
    except AssertionError as e:
        error = str(e)
    result = dict(passed=error is None, error=error, synthetic_body_age_s=now-packet['body_measured_at'],
                  module=str(folder.relative_to(ROOT)/'transaction.py'), models=0, integrations=0,
                  exact_v943_fault_replay=False, original_command_guards_required=True)
    (OUT/('REPRO_CANDIDATE.json' if args.candidate else 'REPRO_ORIGINAL.json')).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    assert result['passed'], 'MONITOR_ABORTS_DURING_VALID_OBSERVATION_LIVENESS'


if __name__ == '__main__':
    main()
