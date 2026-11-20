"""Explicit mode history from canonical t0; never infer missing history as False."""
import math


class ModeMemory:
    def __init__(self, *, canonical_native, coupled_episode, steering_motion_active):
        assert canonical_native == 0, 'MODE_HISTORY_REQUIRES_CANONICAL_T0'
        assert coupled_episode is False and steering_motion_active is False, 'NONCANONICAL_MODE_INITIAL_STATE'
        self.covered_native = 0
        self.coupled_episode = False
        self.steering_motion_active = False
        self.parked_target = None

    def applied(self, *, before_native, v, w, parked_target, steering_motion_active_after):
        assert type(before_native) is int and before_native == self.covered_native, 'MODE_HISTORY_GAP_OR_DUPLICATE'
        assert all(type(x) in (int,float) and math.isfinite(x) for x in (v,w)), 'MODE_COMMAND_NONFINITE'
        assert type(steering_motion_active_after) is bool, 'MODE_ACTIVE_NOT_BOOLEAN'
        assert parked_target is None or (type(parked_target) in (int,float) and math.isfinite(parked_target)), 'MODE_TARGET_NONFINITE'
        episode = self.coupled_episode
        if parked_target is not None:
            assert v == w == 0., 'PARKED_MODE_CANNOT_DRIVE'
            episode = True
        if abs(v) >= .005:
            episode = False
        assert steering_motion_active_after == (parked_target is not None), 'MODE_ADAPTER_EPISODE_MISMATCH'
        assert not steering_motion_active_after or episode, 'ACTIVE_MODE_WITHOUT_EPISODE'
        self.coupled_episode = episode
        self.steering_motion_active = steering_motion_active_after
        self.parked_target = parked_target
        self.covered_native += 1

    def snapshot(self, native_tick):
        assert type(native_tick) is int and native_tick == self.covered_native, 'MODE_CURRENT_STATE_NOT_COVERED'
        return dict(canonical_origin_native=0, covered_native=self.covered_native,
                    coupled_episode=self.coupled_episode, steering_motion_active=self.steering_motion_active,
                    parked_target=self.parked_target)
