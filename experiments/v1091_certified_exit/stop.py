"""Certified actual braking after a rejected proposal; never navigation success."""
import math
from pathlib import Path
import sys
import numpy as np

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'experiments/v1090_active_corridor'))
import corridor
from kernel import virtual
from physical_ops import dump

STOP_NATIVE = 2200
REJECTION = 'ACTIVE_CORRIDOR_RECEDING_CERTIFICATE_REJECTED'

def plan(setup, packet, source):
    requests = np.zeros((STOP_NATIVE, 3))
    proof, states, controls = corridor.proof(setup, packet, source, requests)
    assert proof['passed'], 'NO_CERTIFIED_ACTUAL_EXIT'
    return proof, states, controls, requests

def execute(v, setup, packet, source, out, reason, scan=None):
    """No state writes or model imports. The normal native vehicle owns safety."""
    assert reason == REJECTION, 'UNREGISTERED_CONTROLLED_EXIT'
    assert packet['native_tick'] == v.count
    proof, states, controls, requests = plan(setup, packet, source)
    out = Path(out)
    assert not (out / 'CERTIFIED_EXIT.json').exists(), 'EXIT_ALREADY_ATTEMPTED'
    record = dict(scope='COMPONENT_CERTIFIED_STOP_NOT_GOAL', reason=reason,
                  packet=packet, source=source, proof=proof, start_native=v.count,
                  executed_native=0, completed=False, navigation_passed=False)
    dump(out / 'CERTIFIED_EXIT.json', record)
    np.savez_compressed(out / 'CERTIFIED_EXIT_PLAN.npz', states=states,
                        controls=controls, requests=requests)
    maximum = np.zeros(3)
    try:
        for i, request in enumerate(requests):
            v.step(*request)
            record['executed_native'] = v.count - record['start_native']
            body = np.asarray(v.body())
            angle = body[2] - states[i + 1, 2]
            error = [np.linalg.norm(body[:2] - states[i + 1, :2]),
                     abs(math.atan2(math.sin(angle), math.cos(angle))),
                     abs(virtual(v.steering_sample()[:2]) - states[i + 1, 6])]
            maximum = np.maximum(maximum, error)
            assert np.all(maximum <= [.04, .035, .015]), 'EXIT_TRACKING'
            assert abs(body[3]) <= .13 and abs(body[4]) <= .16, 'EXIT_BODY_CAP'
            if scan is not None and v.count % 5 == 0:
                scan(v.scan())
        assert record['executed_native'] == STOP_NATIVE
        assert np.linalg.norm(v.d.qvel[:2]) <= .03 and abs(v.body()[4]) <= .03, 'EXIT_ACTUAL_STOP'
        record.update(completed=True, maximum_tracking=maximum.tolist(),
                      final_translation_speed_m_s=float(np.linalg.norm(v.d.qvel[:2])),
                      final_body=list(v.body()))
        return record
    finally:
        dump(out / 'CERTIFIED_EXIT.json', record)

def after_rejection(operation, v, setup, packet_fn, source, out, scan=None):
    """Only a forecast rejection is intercepted, never a physical anomaly."""
    try:
        return operation()
    except AssertionError as error:
        if str(error) != REJECTION:
            raise
        packet = packet_fn(v, True)
        packet['speed_episode'] = False
        result = execute(v, setup, packet, source, out, REJECTION, scan)
        raise ControlledStop(result) from error

class ControlledStop(RuntimeError):
    def __init__(self, record):
        self.record = record
        super().__init__('PROPOSAL_REJECTED_ACTUAL_CERTIFIED_STOP_COMPLETED')
