"""Recorded coordinates only: no dynamics, model imports or sensor invention.

The formulas and 1e-8 bound are those in frozen V1497 saved_input.capture.
This module does not create a model state or resolve V1159 method memory.
"""
import math


def compare(fullstate, packet, setup):
    checks = {}
    values = {}

    def check(name, fn):
        try:
            checks[name] = bool(fn())
        except (KeyError, TypeError, ValueError, IndexError, OverflowError):
            checks[name] = False

    def vector(value, size):
        return (isinstance(value, list) and len(value) == size
                and all(type(x) in (int, float) and math.isfinite(x) for x in value))

    check('canonical_state_shapes', lambda: all(
        vector(fullstate[k], n) for k, n in [('qpos', 20), ('qvel', 19), ('ctrl', 11)]))
    check('canonical_address_binding', lambda:
          setup['dt'] == .01 and setup['steering_qpos_addresses'] == [7, 9]
          and setup['steering_qvel_addresses'] == [6, 8]
          and setup['actuator_ids'] == [0, 1, 2, 3])
    check('same_origin_clock', lambda: type(packet['native_tick']) is int
          and math.isfinite(fullstate['time'])
          and fullstate['time'] == packet['sim_time']
          and abs(fullstate['time'] - .01 * packet['native_tick']) <= 1e-8)
    if checks['canonical_state_shapes'] and checks['canonical_address_binding']:
        q, v = fullstate['qpos'], fullstate['qvel']
        yaw = math.atan2(2 * (q[3] * q[6] + q[4] * q[5]),
                         1 - 2 * (q[5] ** 2 + q[6] ** 2))
        values = dict(
            body=[q[0], q[1], yaw, v[0] * math.cos(yaw) + v[1] * math.sin(yaw), v[5]],
            body_lateral=-v[0] * math.sin(yaw) + v[1] * math.cos(yaw),
            steering_position=[q[i] for i in setup['steering_qpos_addresses']],
            steering_velocity=[v[i] for i in setup['steering_qvel_addresses']],
            last_ctrl=[fullstate['ctrl'][i] for i in setup['actuator_ids']])
    errors = {}

    def coordinates(name, actual, expected, size):
        if not vector(actual, size) or not vector(expected, size):
            return False
        errors[name] = max(abs(a - b) for a, b in zip(actual, expected))
        return errors[name] <= 1e-8

    check('body_coordinates', lambda: coordinates('body', values['body'], packet['body'], 5))
    check('lateral_coordinate', lambda: coordinates(
        'lateral', [values['body_lateral']], [packet['body_lateral']], 1))
    check('wheel_positions', lambda: coordinates(
        'wheel_position', values['steering_position'], packet['steering']['position'], 2))
    check('wheel_velocities', lambda: coordinates(
        'wheel_velocity', values['steering_velocity'], packet['steering']['velocity'], 2))
    check('applied_control_memory', lambda: coordinates(
        'last_ctrl', values['last_ctrl'], packet['controller_memory']['last_ctrl'], 4))
    return dict(passed=all(checks.values()), checks=checks, max_errors=errors,
                projected_coordinates=values, tolerance=1e-8,
                scope='RECORDED_FULLSTATE_COORDINATES_NOT_RESPONSE_MODEL',
                integral_recomputed=False, model_origin_conversion_qualified=False,
                steering_load_epoch_qualified=False, actual_capture_qualified=False,
                models_authorized=False, physical_permission=False)
