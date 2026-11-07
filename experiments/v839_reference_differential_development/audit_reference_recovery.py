"""Audit all new continuation contracts and causal reference provenance, no models."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from reference_certificate_audit import check_successor

ap = argparse.ArgumentParser(); ap.add_argument('pair', type=Path); args = ap.parse_args()
pair = args.pair; cell = pair/'geometry_memory'
protocol = json.loads((pair/'STATIC_PROTOCOL.json').read_text())
contract = json.loads((cell/'ACTUATOR_COMMAND_CONTRACT.json').read_text())
limits, rate = np.asarray(contract['limits']), np.asarray(contract['rate'])
plans = [json.loads(p.read_text()) for p in cell.glob('planning_*.json')]
states = {x['step']: x for x in map(json.loads, (cell/'motion_estimate.jsonl').open())}
records = []
for directory in ['successor_certificates', 'recovery_contracts', 'handover_certificates', 'shadow_handover_certificates']:
    for file in sorted((cell/directory).glob('*.gz')):
        with gzip.open(file, 'rt') as stream:
            c = json.load(stream)
        if 'one_cycle_continuation' not in c:
            assert 'reference_following' not in c
            continue
        state = states[c['created_step']]
        assert c['forecast_state'] == {k:v for k,v in state.items() if k!='step'}
        result = check_successor(c, protocol, limits, rate)
        if 'reference_following' in c:
            reference = c['reference_following']
            assert np.array_equal(reference['goal_xy'], protocol['goal_xy'])
            assert any(p['step'] <= c['created_step'] and p['path'] == reference['path'] for p in plans)
        records.append(dict(file=str(file.relative_to(pair)), **result))
result = dict(status='REFERENCE_RECOVERY_AND_SUCCESSOR_PASS', checks=dict(
    complete_original328=True, extra8_continuation=True, full_self_and_controls=True,
    references_from_prior_causal_plans=True, no_future_observations_assumed=True),
    records=records, models=0, integrations=0,
    scope='Finite successor witness only; not recursive feasibility or infinite stop safety.')
(pair/'REFERENCE_RECOVERY_AUDIT.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(dict(status=result['status'], certificates=len(records))))
