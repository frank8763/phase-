"""One immutable response reference per event, with monotonic membership.

This is a response monitor only, never a certificate producer or permission.
Native origins are current event inputs, with no saved-component tick constants.
"""
import math
from route_event import digest, finite_vector


def rear(body):
    return body[0] - .3 * math.cos(body[2]), body[1] - .3 * math.sin(body[2]), body[2]


class ResponseReference:
    def __init__(self, request, states):
        value = dict(request); identity = value.pop('request_sha256')
        assert identity == digest(value), 'REFERENCE_REQUEST_CHANGED'
        assert isinstance(states, (list, tuple)) and len(states) >= 201, 'REFERENCE_COMPLETE_TAIL_LENGTH'
        for state in states:
            finite_vector(state, 8)
        self.states = tuple(tuple(row) for row in states)
        self.origin = request['actual']['wire']['native_tick']
        self.request_sha256 = identity
        self.reference_sha256 = digest(states)
        first = states[0]
        assert max(abs(a-b) for a,b in zip([first[0],first[1],first[2],first[3],first[5]], request['actual']['wire']['body'])) <= 1e-8, 'REFERENCE_WRONG_CURRENT_ORIGIN'
        self.previous_index = 0
        self.previous_native = self.origin - 1

    def assess(self, body, native_tick):
        finite_vector(body, 5)
        assert type(native_tick) is int and native_tick > self.previous_native, 'REFERENCE_NATIVE_NOT_ADVANCING'
        i = native_tick - self.origin
        assert 0 <= i <= len(self.states)-1, 'REFERENCE_TIME_OUTSIDE_FIXED_RESPONSE'
        actual = rear(body); best = None
        for j in range(max(self.previous_index, 0, i-20), min(len(self.states)-1, i+20)+1):
            reference = rear(self.states[j])
            distance = math.dist(actual[:2], reference[:2])
            angle = abs(math.atan2(math.sin(actual[2]-reference[2]), math.cos(actual[2]-reference[2])))
            if distance <= .02+1e-8 and angle <= .1+1e-8:
                candidate = (abs(i-j), j, distance, angle)
                if best is None or candidate < best:
                    best = candidate
        assert best is not None, 'ACTUAL_RESPONSE_OUTSIDE_FIXED_TIME_POSE_TUBE'
        self.previous_index = best[1]; self.previous_native = native_tick
        return dict(reference_index=best[1], rear_error_m=best[2], yaw_error_rad=best[3], time_error_s=best[0]*.01,
                    request_sha256=self.request_sha256, reference_sha256=self.reference_sha256,
                    physical_admission=False)
