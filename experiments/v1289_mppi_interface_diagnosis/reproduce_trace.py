"""Deterministically reproduce the captured raw command against the real validator."""
import json
from pathlib import Path
import sys
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'experiments/v1288_baseline_interface'))
from contract import twist
rows = json.loads((R / 'runs/v1288_baseline_interface/RAW_COMMANDS.json').read_text())
for row in rows:
    if row['contract_error']:
        print(json.dumps(dict(captured_raw_command=row, applying_real_validator=True)), flush=True)
        twist(row['v'], row['w'])
raise AssertionError('EXPECTED_CAPTURED_REJECTION_NOT_REPRODUCED')
