"""Production transaction timing/immutability gates; no new observations or models."""
import copy
import json
import math
import sys
from pathlib import Path

from reproduce import NoModel  # installs the no-model import guard

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).parent
OUT = ROOT/'runs/v945_rpccr_observation_liveness'
sys.path.insert(0, str(CODE))
from transaction import RecoveryTransaction, fingerprint
from cycle_backup import retained_allowed, stale_proposal_may_defer


def main():
    first = json.loads((ROOT/'runs/v936_rpccr_corridor_search/ENTRY_QUALIFICATION.json').read_text())['first_actual_trigger']
    checks = {}
    cases = []

    def fresh_case(age):
        packet, source = copy.deepcopy(first['packet']), copy.deepcopy(first['source'])
        packet['body_measured_at'] = 0.
        source['decision_at'] = age
        source['source_age_s'] = .01
        m = RecoveryTransaction([4., -2.], [])
        m.mode = 'FOLLOW_RECOVERY'
        m.path = [[0., 0., 0.], [1., 0., 0.]]
        m.path_sha256 = fingerprint(m.path)
        m.installed_at = age-1.
        return m, packet, source

    for age in [.049, .05, .050001, .051, .1, .199, .2, .200001, .201]:
        m, p, s = fresh_case(age)
        original = copy.deepcopy((p, s, m.path, m.path_sha256, m.installed_at))
        try:
            event = m.monitor(p, s, age)
            error = None
        except AssertionError as e:
            error = str(e)
            event = None
        checks[f'live_boundary_{age}'] = (error is None) == (age <= .2)
        checks[f'no_new_permission_or_input_mutation_{age}'] = (
            (p, s, m.path, m.path_sha256, m.installed_at) == original
            and (event is None or event['actuator_permission_created'] is False))
        strict_error = None
        try:
            RecoveryTransaction.fresh(p, s, age)
        except AssertionError as e:
            strict_error = str(e)
        checks[f'new_permission_still_50ms_{age}'] = (strict_error is None) == (age <= .05)
        cases.append(dict(age_s=age, monitor_error=error, new_permission_error=strict_error))

    for name, mutate, expected in [
        ('future_body', lambda m,p,s:p.update(body_measured_at=2.), 'STALE_BODY_LIVENESS'),
        ('stale_scan', lambda m,p,s:s.update(source_age_s=.201), 'STALE_SCAN'),
        ('future_source', lambda m,p,s:s.update(source_native_tick=p['native_tick']+1), 'FUTURE_SOURCE'),
        ('future_prior', lambda m,p,s:s['periodic'].update(source_tick=s['source_native_tick']+1), 'FUTURE_PERIODIC_SOURCE'),
        ('changed_prior', lambda m,p,s:s['periodic'].update(omega=.33), 'CHANGED_PRIOR'),
        ('nonfinite', lambda m,p,s:p['body'].__setitem__(0, math.nan), 'NONFINITE_SOURCE'),
        ('path_mutated', lambda m,p,s:m.path[-1].__setitem__(0, 2.), 'COMMITTED_REFERENCE_MUTATED'),
        ('segment_timeout', lambda m,p,s:setattr(m, 'installed_at', -36.), 'RECOVERY_SEGMENT_TIMEOUT'),
    ]:
        m, p, s = fresh_case(.1)
        mutate(m, p, s)
        try:
            m.monitor(p, s, .1)
        except AssertionError as e:
            checks[name] = str(e) == expected and m.mode == 'FAILED'
        else:
            checks[name] = False

    # Exercise the unchanged production certificate keeper, including finite expiry.
    proof = dict(passed=True, body_age_s=.01, body_native_tick=100,
                 terminal_cycle_qualified=False, terminal_cycle_lower_m=.1)
    m, p, s = fresh_case(.1)
    p['native_tick'] = 110
    s['source_native_tick'] = 110
    s['periodic']['source_tick'] = 110
    frozen = copy.deepcopy(proof)
    checks['old_valid_certificate_may_defer_stale_new_proposal'] = stale_proposal_may_defer(
        AssertionError('STALE_COMMAND_BODY'), proof, p, .1)
    p['native_tick'] = 327
    checks['expired_finite_certificate_cannot_be_extended'] = not stale_proposal_may_defer(
        AssertionError('STALE_COMMAND_BODY'), proof, p, .1)
    checks['finite_expiry_is_unchanged'] = retained_allowed(proof, 2.25) and not retained_allowed(proof, 2.261)
    checks['old_certificate_bytes_unchanged'] = proof == frozen
    checks['other_command_faults_never_defer'] = not stale_proposal_may_defer(
        AssertionError('ACTUATOR_RATE'), proof, p, .1)
    checks['install_fresh_function_is_exact_inherited'] = 'fresh' not in RecoveryTransaction.__dict__
    result = dict(passed=all(checks.values()), checks=checks, cases=cases, models=0, integrations=0,
                  actual_navigation=0, scope='Synthetic timing boundaries through production transaction and unchanged certificate keeper; not counterfactual arrival.')
    (OUT/'LIVENESS_QUALIFICATION.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
