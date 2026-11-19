"""Exact saved allocator rejection; no model constructor or integration."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
RAW = R / 'runs/v858_nav2_verified/v1345/rpp_async_default_dynamic_main'


def main():
    spec = importlib.util.spec_from_file_location('saved_signed_allocator', R / 'experiments/v1035_signed_timed_input_source/signed_control.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    row = json.loads((RAW / 'APPLIED_JOURNAL.json').read_text())[-1]
    owner = object.__new__(module.Adapter)
    owner.last = np.asarray(row['last_ctrl'])
    owner.integral = row['integral']
    owner.max_curvature = 1. / 1.32
    assert row['before_native'] == 16255 and not row['applied']
    # Use the original production allocator at the exact failing call boundary.
    # A successful fix must send braking here, never weaken the assertion.
    try:
        owner.compute(*row['request'][:2], *row['body'][3:], False)
    except AssertionError as error:
        assert str(error) == 'FORWARD_BEFORE_COMPLETE_REVERSE_STOP'
        proof = dict(red_reproduced=True, error=str(error), native_tick=16255,
                     request=row['request'], last_ctrl=row['last_ctrl'],
                     actual_signed_speed_m_s=row['body'][3], models=0, integrations=0)
        (O / 'EXACT_RED.json').write_text(json.dumps(proof, indent=2) + '\n')
        print(json.dumps(proof))
        return 1
    raise AssertionError('ORIGINAL_FAILURE_NOT_REPRODUCED')


if __name__ == '__main__':
    raise SystemExit(main())
