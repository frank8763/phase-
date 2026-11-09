"""Candidate decision seam: publish measured pose and causal tracker state atomically.

No model/ROS initialization on import. This candidate is not attached to a running
navigation and does not retrospectively repair V907's failed evidence.
"""
import copy,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'experiments/v907_recovery_corridor_memory'))
from motion_publisher import MotionPublisher

class CoherentMotionPublisher(MotionPublisher):
    def observe(self,packet):
        with self.lock:
            # The parent also uses this RLock. Publishing the decision packet
            # belongs to the SAME transaction as updating its measurement set.
            super().observe(packet)
            assert self.tracker.latest['native_tick']<=packet['native_tick'],'FUTURE_OBSERVATION_IN_PACKET'
            self._decision_packet=copy.deepcopy(packet)

    def decision_snapshot(self):
        with self.lock:
            packet=copy.deepcopy(getattr(self,'_decision_packet',None))
            if packet is None:raise RuntimeError('NO_COHERENT_OBSERVATION')
            now=time.monotonic()
            if self.running and (now-packet['sent_at']>.2 or now-self.scan_monotonic>.2):
                raise RuntimeError('STALE_COHERENT_OBSERVATION')
            tracker=self.tracker
            assert tracker.latest['native_tick']<=packet['native_tick'],'FUTURE_DECISION_SOURCE'
            source=dict(source_native_tick=tracker.latest['native_tick'],source_scan_sim_time=tracker.when,
                        source_age_s=max(0.,now-self.scan_monotonic)if self.running else 0.,
                        support_bounds=None if tracker.support is None else tracker.support.tolist(),
                        last_hit_time=tracker.last_hit,body_native_tick=packet['native_tick'])
            return packet,source
