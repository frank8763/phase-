"""Immutable certificate transaction. No vehicle import or control publishing.

The verifier is trusted code supplied by the owner, never a candidate field.
Physical eligibility is separate from nominal software lease bookkeeping.
"""
import copy
import hashlib
import json
import math


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                         allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def replace(previous, candidate, packet, verify, clock, deadline):
    before = digest(previous)
    try:
        assert clock() < deadline, 'DEADLINE'
        new = copy.deepcopy(candidate)
        assert new['packet_sha256'] == digest(packet), 'PACKET_BINDING'
        assert new['domain_parent_sha256'] == previous['domain_sha256'], 'DOMAIN_PARENT'
        assert new['source_tick'] <= packet['native_tick'], 'FUTURE_DOMAIN'
        assert new['absolute_start_time'] == packet['sim_time'], 'CLOCK_REBASE'
        assert new['contract'] == 'RETAINED_RECOVERY_V1', 'WRONG_CONTRACT'
        assert new['remaining_stop_native'] >= 2200, 'INCOMPLETE_STOP'
        verdict = verify(copy.deepcopy(new), copy.deepcopy(packet))
        required = ['source_and_controls_bound', 'domain_subset',
                    'complete_native_coverage', 'full_ctrl_and_memory',
                    'terminal_full_cycle', 'initial_set_membership',
                    'all_successors_covered', 'model_disturbance_verified']
        assert all(verdict.get(k) is True for k in required), 'UNVERIFIED_RECOVERY'
        assert math.isfinite(verdict['minimum_raw_m'])
        assert verdict['minimum_raw_m'] >= .24353421020226934, 'CLEARANCE'
        assert verdict['covered_native'] == new['remaining_native'], 'COVERAGE_LENGTH'
        assert verdict['plan_sha256'] == new['plan_sha256'], 'WRONG_PLAN_PROOF'
        assert clock() < deadline, 'VERIFICATION_TIMEOUT'
        assert digest(previous) == before, 'OLD_PLAN_MUTATED'
        return new, {'committed': True, 'previous_sha256': before}
    except Exception as error:
        assert digest(previous) == before, 'OLD_PLAN_MUTATED'
        return previous, {'committed': False, 'reason': str(error),
                          'previous_sha256': before}


def retained_cursor(plan, native_tick, sim_time, domain_sha256):
    """Cursor bookkeeping only; caller still needs measured tube membership."""
    assert domain_sha256 == plan['domain_sha256'], 'DOMAIN_CHANGED'
    offset = native_tick - plan['start_native_tick']
    assert type(offset) is int and 0 <= offset < plan['remaining_native'], 'PLAN_EXHAUSTED'
    expected = plan['absolute_start_time'] + offset*.01
    assert abs(sim_time-expected) <= 1e-8, 'ABSOLUTE_CLOCK_DRIFT'
    return offset
