"""Actual plugin feedback loop: exits 1 when the old early-turn symptom remains."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--attempt', choices=['repro01', 'repro02'], required=True); args = parser.parse_args()
    output = R / 'runs' / C.name / args.attempt
    if not (output / 'COMPLETION.json').exists():
        env = dict(os.environ, PHASE_MPPI_ATTEMPT=args.attempt)
        subprocess.run([sys.executable, '-B', str(C / 'run_software.py')], cwd=R, env=env, check=True)
    result = json.loads((output / 'COMPLETION.json').read_text())
    assert result['passed'] and result['review_pending_unchanged'], 'SOFTWARE_ENTRY_FAILED'
    median = result['controller']['cases'][0]['median_moving_w']
    proof = dict(passed=median >= .01, median_moving_w=median, required_diagnostic_minimum=.01,
                 actual_plugin=True, frozen_saved_state=5000, models=0, physical_native=0,
                 not_physical_safety_or_arrival_claim=True)
    (output / 'EARLY_TURN_SYMPTOM.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof)); return 0 if proof['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
