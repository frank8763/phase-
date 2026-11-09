"""Separate observation liveness from fresh installation/command admission.

This supervisor creates no actuator permission. Original bridge/native guards
alone decide whether an immutable old certificate is still executable.
"""
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    'frozen_v938_transaction', ROOT/'experiments/v938_rpccr_recovery_segments/transaction.py')
_old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_old)
fingerprint = _old.fingerprint


class RecoveryTransaction(_old.RecoveryTransaction):
    # request/install/finish_segment and fresh are inherited unchanged (50ms).
    @staticmethod
    def live(packet, source, now):
        assert np.isfinite([now, *packet['body'], packet['body_measured_at'],
                            source['source_age_s']]).all(), 'NONFINITE_SOURCE'
        assert 0 <= now-packet['body_measured_at'] <= .2, 'STALE_BODY_LIVENESS'
        age = source['source_age_s']+max(0., now-source.get('decision_at', now))
        assert 0 <= age <= .2, 'STALE_SCAN'
        assert source['source_native_tick'] <= packet['native_tick'], 'FUTURE_SOURCE'
        prior = source['periodic']
        assert prior['source_tick'] <= source['source_native_tick'], 'FUTURE_PERIODIC_SOURCE'
        assert prior['omega'] == .32 and prior['amplitude'] == .25, 'CHANGED_PRIOR'

    @_old.guarded
    def monitor(self, packet, source, now):
        self.live(packet, source, now)
        if self.mode in {'CANCEL_PENDING', 'FOLLOW_ACCEPT_PENDING'}:
            anchor = self.started_at if self.mode == 'CANCEL_PENDING' else self.installed_at
            assert now-anchor <= 2., 'ACTION_HANDSHAKE_TIMEOUT'
        if self.mode in {'FOLLOW_RECOVERY', 'STOPPED_REPLAN'}:
            assert now-self.installed_at <= 35., 'RECOVERY_SEGMENT_TIMEOUT'
            assert fingerprint(self.path) == self.path_sha256, 'COMMITTED_REFERENCE_MUTATED'
        return self._record('COMMAND_AND_NATIVE_GUARDS_REMAIN_REQUIRED',
                            checked_at=now, body_age_s=now-packet['body_measured_at'],
                            actuator_permission_created=False)
