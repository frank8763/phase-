"""Bind actual range acquisition to the native state, including fast brake steps."""
import math
import time

CORE = ('schema', 'run_id', 'sequence', 'sampled_at', 'body', 'ranges_m')


def validate_frame(scan, tick, sim_time, body):
    assert type(tick) is int and type(scan['native_tick']) is int
    assert scan['native_tick'] == tick, 'SENSOR_NATIVE_TICK_MISMATCH'
    assert len(body) == 5 and len(scan['xy']) == 2
    assert all(math.isfinite(x) for x in [sim_time, scan['time'], scan['yaw'], *scan['xy'], *body])
    assert abs(scan['time'] - sim_time) <= 1e-8, 'SENSOR_PHYSICAL_CLOCK_MISMATCH'
    assert max(abs(x-y) for x, y in zip(scan['xy'], body[:2])) <= 1e-8, 'SENSOR_POSE_MISMATCH'
    angle = math.atan2(math.sin(scan['yaw']-body[2]), math.cos(scan['yaw']-body[2]))
    assert abs(angle) <= 1e-6, 'SENSOR_HEADING_MISMATCH'
    assert len(scan['ranges']) == 32 and all(math.isfinite(x) and 0 <= x <= 3 for x in scan['ranges'])
    return True


class SampleCache:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.scan = None
        self.sampled_at = None

    def sample(self, vehicle):
        now = self.clock()
        if self.scan is None or self.scan['native_tick'] != vehicle.count or now-self.sampled_at >= .04:
            # Conservative acquisition start, never publication time relabeling.
            self.sampled_at = now
            self.scan = vehicle.scan()
        validate_frame(self.scan, vehicle.count, float(vehicle.d.time), list(vehicle.body()))
        assert 0 <= self.clock()-self.sampled_at <= .2, 'SCAN_ACQUISITION_EXPIRED'
        return self.scan, self.sampled_at


def wire_packet(cache, vehicle, run_id, sequence):
    scan, acquired = cache.sample(vehicle)
    return dict(schema=1, run_id=run_id, sequence=sequence, sampled_at=acquired,
                body=list(vehicle.body()), ranges_m=list(scan['ranges']), native_tick=vehicle.count,
                sim_time=float(vehicle.d.time), sensor_frame=dict(native_tick=scan['native_tick'],
                time=scan['time'], xy=list(scan['xy']), yaw=scan['yaw'], sampled_at=acquired))


def validate_wire(wire):
    assert set(wire) == set(CORE) | {'native_tick', 'sim_time', 'sensor_frame'}, 'WIRE_KEYS'
    frame = wire['sensor_frame']
    assert set(frame) == {'native_tick', 'time', 'xy', 'yaw', 'sampled_at'}, 'SENSOR_FRAME_KEYS'
    assert wire['sampled_at'] == frame['sampled_at'] and math.isfinite(frame['sampled_at']), 'ACQUISITION_RELABELED'
    validate_frame(dict(frame, ranges=wire['ranges_m']), wire['native_tick'], wire['sim_time'], wire['body'])
    return True


def validate_binding(command, sent):
    wire = sent[command['observation_sequence']]
    validate_wire(wire)
    assert command['run_id'] == wire['run_id'], 'BINDING_FOREIGN_RUN'
    assert command['observation_native_tick'] == wire['native_tick'], 'BINDING_TICK_CHANGED'
    assert command['observation_sampled_at'] == wire['sampled_at'], 'BINDING_ACQUISITION_CHANGED'
    return True
