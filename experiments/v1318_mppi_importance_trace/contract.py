"""Strict shared causal input/output boundary. Pure data; no physical imports."""
import math

SPEED = .1
CURVATURE = 1 / 1.32


def number(x):
    if type(x) not in (int, float) or not math.isfinite(x):
        raise ValueError('NONFINITE_OR_NONNUMERIC')
    return float(x)


def observation(p, *, run_id, now, previous_sequence=-1):
    if type(p) is not dict or set(p) != {'schema', 'run_id', 'sequence', 'sampled_at', 'body', 'ranges_m'}:
        raise ValueError('OBSERVATION_SCHEMA_OR_UNDECLARED_INFORMATION')
    if p['schema'] != 1 or p['run_id'] != run_id:
        raise ValueError('FOREIGN_OBSERVATION')
    if type(p['sequence']) is not int or p['sequence'] <= previous_sequence:
        raise ValueError('REPLAYED_OBSERVATION')
    if not 0 <= number(now) - number(p['sampled_at']) <= .2:
        raise ValueError('STALE_OR_FUTURE_OBSERVATION')
    if type(p['body']) is not list or len(p['body']) != 5:
        raise ValueError('BODY_SHAPE')
    list(map(number, p['body']))
    if type(p['ranges_m']) is not list or len(p['ranges_m']) != 32:
        raise ValueError('SCAN_SHAPE')
    if not all(0 <= number(x) <= 3 for x in p['ranges_m']):
        raise ValueError('SCAN_RANGE')
    return p


def twist(v, w):
    v, w = number(v), number(w)
    if abs(v) > SPEED + 1e-6:
        raise ValueError('COMMAND_SPEED')
    if abs(v) < .005 and abs(w) > 1e-6:
        raise ValueError('ROTATION_WITHOUT_DRIVE')
    if abs(w) > abs(v) * CURVATURE + 1e-6:
        raise ValueError('COMMAND_CURVATURE')
    return v, w


def command(p, *, run_id, now, previous_sequence=-1, stopped=False):
    if type(p) is not dict or set(p) != {'run_id', 'sequence', 'issued_at', 'v', 'w'}:
        raise ValueError('COMMAND_SCHEMA')
    if p['run_id'] != run_id or type(p['sequence']) is not int or p['sequence'] <= previous_sequence:
        raise ValueError('FOREIGN_OR_REPLAYED_COMMAND')
    if not 0 <= number(now) - number(p['issued_at']) <= .2:
        raise ValueError('STALE_OR_FUTURE_COMMAND')
    v, w = twist(p['v'], p['w'])
    if stopped:
        raise ValueError('COMMAND_AFTER_STOP')
    return v, w
