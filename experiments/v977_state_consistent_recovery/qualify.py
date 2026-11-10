"""Fixed saved-input, model-forbidden reference qualification."""
import argparse
import importlib.abc
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np

R = Path(__file__).resolve().parents[2]
C = Path(__file__).parent
O = R / 'runs/v977_state_consistent_recovery'


class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self, name, *args):
        if name.split('.')[0] in {'mujoco', 'torch', 'vehicle', 'physical', 'factory'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN ' + name)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def initial_k(packet):
    t = np.tan(packet['steering']['position'])
    return float(np.mean([t[0] / (.6 + .27*t[0]), t[1] / (.6 - .27*t[1])]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    sys.meta_path.insert(0, NoModel())
    O.mkdir(exist_ok=True)
    saved = json.loads((R / 'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
    rows = []
    if args.baseline:
        sys.path.insert(0, str(R / 'experiments/v968_rpp_closed_loop_night'))
        old = load(R / 'experiments/v968_rpp_closed_loop_night/recovery.py', 'v977_actual_old_constructor')
        for i, row in enumerate(saved['rows']):
            packet, source = row['search_packet'], row['search_source']
            result = old.construct(packet['body'][:3], row['original_goal'], saved['known'], source['periodic'])
            k = None
            if result['passed']:
                a, b = np.asarray(result['path'][:2])
                k = math.atan2(math.sin(b[2]-a[2]), math.cos(b[2]-a[2]))/.1
            checks = dict(reference_generated=result['passed'], measured_initial_steering_continuous=k is not None and abs(k-initial_k(packet)) < 1e-6)
            rows.append(dict(index=i, passed=all(checks.values()), checks=checks, status=result['status'], initial_curvature=k, measured_curvature=initial_k(packet)))
        report = dict(passed=all(x['passed'] for x in rows), models=0, integrations=0, actual_old_constructor=True, rows=rows)
        (O/'BASELINE_RED.json').write_text(json.dumps(report, indent=2)+'\n')
    else:
        module = load(C / 'saved_qualification.py', 'v977_saved_qualification')
        report = module.run(saved)
        (O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
