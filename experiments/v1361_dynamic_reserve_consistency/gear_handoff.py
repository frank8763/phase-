"""Measured gear transition before the unchanged signed allocator.

No plant/model access, state writes, time warps or actuator-law changes.
Only fresh upstream body commands may pass; a gear transition yields zeros
until 200 native braking steps and measured body/steering-joint rest are complete.
"""
import math

BRAKE_NATIVE = 200
BODY_REST = .003
STEERING_REST = .03
DRIVE_ZERO = 1e-10


def sign(value, threshold):
    return 1 if value > threshold else -1 if value < -threshold else 0


class GearHandoff:
    def __init__(self):
        self.gear = 0
        self.brake_start = None
        self.last_tick = -1

    def select(self, v, w, *, native_tick, body, last_ctrl, encoders):
        assert type(native_tick) is int and native_tick > self.last_tick, 'GEAR_CLOCK_NOT_ADVANCING'
        assert len(body) == 5 and len(last_ctrl) == len(encoders) == 4, 'GEAR_FEEDBACK_SHAPE'
        assert all(math.isfinite(float(x)) for x in [v, w, *body, *last_ctrl, *encoders]), 'GEAR_NONFINITE_FEEDBACK'
        self.last_tick = native_tick
        wanted = 0 if abs(v) < .005 else sign(v, 0.)
        rear = last_ctrl[2:]
        assert min(rear) >= -DRIVE_ZERO or max(rear) <= DRIVE_ZERO, 'GEAR_INCONSISTENT_REAR_TARGETS'
        drive_gear = sign(sum(rear) / 2., DRIVE_ZERO)
        body_gear = sign(body[3], BODY_REST)
        opposing = wanted and any(g and g != wanted for g in [self.gear, drive_gear, body_gear])
        # A same-sign reverse re-entry from zero drive still requires actual
        # rest in the unchanged signed allocator. Short stale holds can reach
        # zero drive before body velocity has settled.
        reverse_reentry=bool(wanted<0 and drive_gear==0 and abs(body[3])>BODY_REST)
        if self.brake_start is None and (opposing or reverse_reentry):
            self.brake_start = native_tick
        resting = (max(abs(x) for x in body[3:]) <= BODY_REST
                   and max(abs(x) for x in rear) <= DRIVE_ZERO
                   and max(abs(x) for x in encoders[2:]) <= STEERING_REST)
        proof = dict(requested_gear=wanted, prior_gear=self.gear,
                     drive_gear=drive_gear, measured_body_gear=body_gear,
                     brake_start=self.brake_start, measured_rest=resting,
                     braking_native=0 if self.brake_start is None else native_tick-self.brake_start)
        if reverse_reentry:proof['reverse_zero_drive_restart_requires_rest']=True
        if self.brake_start is not None:
            if native_tick-self.brake_start < BRAKE_NATIVE or not resting:
                return 0., 0., dict(proof, mode='GEAR_BRAKE_HOLD', released=False)
            # No saved command is replayed: v/w are this step's fresh request.
            self.brake_start = None
            self.gear = wanted
            return float(v), float(w), dict(proof, mode='GEAR_RELEASE_AT_MEASURED_REST', released=True)
        if wanted:
            self.gear = wanted
        return float(v), float(w), dict(proof, mode='UNCHANGED', released=False)
