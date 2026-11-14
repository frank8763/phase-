"""Offline-qualified, packet-causal certificate transaction. No vehicle factory.

This module does not publish controls. The caller must bind/recertify against
the current measured packet again before any physical application.
"""
import copy
import hashlib
import json
import math

KEYS = ('native_tick', 'time', 'xy', 'yaw', 'ranges')
REQUIRED = .24353421020226934
CHECKS = {'finite','full_states','full_raw_geometry','full_200_stop','goal_upper',
          'speed_yaw','legal_ctrl','legal_slew','coupled_mode_envelopes',
          'parked_ready','full2200tail','terminal_full_cycle_hold',
          'safe_terminal_position','safe_terminal_heading'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(',', ':')).encode()).hexdigest()


def causal_packets(rows, packet):
    """Reject future input; collapse only identical, adjacent packet duplicates."""
    tick, clock = packet['native_tick'], packet['sim_time']
    assert type(tick) is int and tick >= 0 and math.isfinite(clock)
    clean, duplicates = [], 0
    for row in rows:
        sample = {key: copy.deepcopy(row[key]) for key in KEYS}
        digest(sample)  # strict finite JSON, including every range
        assert type(sample['native_tick']) is int
        assert 0 <= sample['native_tick'] <= tick, 'FUTURE_NATIVE'
        assert 0 <= sample['time'] <= clock + 1e-9, 'FUTURE_TIME'
        if clean:
            prev = clean[-1]
            if sample['time'] == prev['time'] or sample['native_tick'] == prev['native_tick']:
                assert sample == prev, 'CONTRADICTORY_DUPLICATE'
                duplicates += 1
                continue
            assert sample['time'] > prev['time'] and sample['native_tick'] > prev['native_tick'], 'BACKWARDS_PACKET'
        clean.append(sample)
    assert clean and 0 <= clock - clean[-1]['time'] <= .051, 'STALE_MEASUREMENT'
    return clean, duplicates


def try_commit(previous, packet, build, certify, now, deadline):
    """Copy-on-write: failure retains the complete previous certificate bundle."""
    old_hash = digest(previous)
    try:
        assert now() < deadline, 'REFRESH_TIMEOUT'
        packet_hash = digest(packet)
        candidate = build(copy.deepcopy(packet))
        assert candidate['packet_sha256'] == packet_hash, 'WRONG_PACKET_BINDING'
        assert candidate['nested_domain'] is True, 'DOMAIN_NOT_NESTED'
        assert candidate['duals_verified'] is True, 'UNCERTIFIED_SUPPORT'
        assert candidate['source_native_tick'] <= packet['native_tick'], 'FUTURE_SOURCE'
        assert 0 <= candidate['source_age_s'] <= .051, 'STALE_SOURCE'
        proofs = certify(copy.deepcopy(packet), candidate)
        assert set(proofs) == {'current', 'prospective'}, 'INCOMPLETE_BACKUPS'
        for key, proof in proofs.items():
            assert CHECKS <= set(proof['checks']), 'MISSING_SAFETY_CHECKS'
            assert proof['passed'] is True and all(v is True for v in proof['checks'].values()), 'BACKUP_REFUSED'
            assert all(math.isfinite(proof[field]) and proof[field] >= REQUIRED
                       for field in ('minimum_raw_m','terminal_full_cycle_raw_m')), 'RAW_MARGIN_REFUSED'
            assert proof['native'] >= 2200, 'INCOMPLETE_STOP'
            assert all(len(proof[field]) == 64 and all(c in '0123456789abcdef' for c in proof[field])
                       for field in ('states_sha256','controls_sha256')), 'MISSING_PROFILE_HASH'
        assert now() < deadline, 'REFRESH_TIMEOUT'
        assert digest(packet) == packet_hash and digest(previous) == old_hash, 'TRANSACTION_INPUT_CHANGED'
        return dict(candidate, proofs=proofs), {'committed': True, 'previous_sha256': old_hash}
    except Exception as error:
        assert digest(previous) == old_hash, 'OLD_CERTIFICATE_MUTATED'
        return previous, {'committed': False, 'reason': str(error), 'previous_sha256': old_hash}
