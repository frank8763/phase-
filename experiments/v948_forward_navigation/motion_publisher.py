"""Original causal publisher, with durable exact producer-side stale diagnostics."""
import copy
import importlib.util
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'frozen_v945_motion_publisher',
    ROOT/'experiments/v945_rpccr_observation_liveness/motion_publisher.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


class ObservationFault(RuntimeError):
    def __init__(self, reason, evidence):
        super().__init__(reason)
        self.evidence = evidence


class MotionPublisher(old.MotionPublisher):
    def decision_snapshot(self):
        with self.lock:
            packet = copy.deepcopy(getattr(self, '_decision_packet', None))
            now = time.monotonic()
            if packet is None:
                raise ObservationFault('NO_COHERENT_OBSERVATION',
                                       dict(exact_check_input=True, checked_at=now, packet=None))
            age = max(0., now-self.scan_monotonic) if self.running else 0.
            body_age = now-packet['sent_at']
            evidence = dict(exact_check_input=True, checked_at=now, packet=packet,
                            body_sent_age_s=body_age,
                            body_measured_age_s=now-packet['body_measured_at'],
                            scan_measured_age_s=now-packet['scan_measured_at'],
                            source_age_s=age, running=self.running,
                            scan_monotonic=self.scan_monotonic, threshold_s=.2)
            if not all(math.isfinite(x) for x in
                       [now, body_age, age, evidence['body_measured_age_s'],
                        evidence['scan_measured_age_s']]):
                raise ObservationFault('NONFINITE_COHERENT_OBSERVATION', evidence)
            if self.running and (body_age > .2 or age > .2):
                raise ObservationFault('STALE_COHERENT_OBSERVATION', evidence)
            if self.running and (body_age < -.05 or now-self.scan_monotonic < -.05):
                raise ObservationFault('FUTURE_COHERENT_OBSERVATION', evidence)
            tracker = self.tracker
            assert tracker.latest['native_tick'] <= packet['native_tick'], 'FUTURE_DECISION_SOURCE'
            return packet, dict(source_native_tick=tracker.latest['native_tick'],
                source_scan_sim_time=tracker.when, source_age_s=age,
                support_bounds=None if tracker.support is None else tracker.support.tolist(),
                last_hit_time=tracker.last_hit, body_native_tick=packet['native_tick'],
                decision_at=now, periodic=None if self.periodic.last is None else self.periodic.snapshot())
