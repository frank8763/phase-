"""Saved failure, real signed allocator, and adversarial interlock schedules.

Pure controller algebra over recorded or explicitly synthetic feedback. This
does not claim physical braking response or use a constructed vehicle model.
"""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from gear_handoff import GearHandoff

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R / 'runs' / C.name
RAW = R / 'runs/v858_nav2_verified/v1345'


def main():
    sys.path.insert(0, str(R / 'experiments/v993_steering_transient_diagnosis'))
    from fixture import make
    spec = importlib.util.spec_from_file_location('gear_actual_signed', R / 'experiments/v1035_signed_timed_input_source/signed_control.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    out = RAW / 'rpp_async_default_dynamic_main'
    rows = json.loads((out / 'APPLIED_JOURNAL.json').read_text())
    failed = rows[-1]; setup = json.loads((out / 'physics/SETUP.json').read_text())
    owner = make(module.Adapter, setup); owner.last = np.asarray(failed['last_ctrl']); owner.integral = failed['integral']
    gate = GearHandoff(); checks = {}; controls = []
    for tick in range(250):
        previous = owner.last.copy()
        v, w, proof = gate.select(*failed['request'][:2], native_tick=16255+tick,
                                  body=failed['body'], last_ctrl=owner.last, encoders=failed['encoders'])
        assert v == w == 0. and proof['mode'] == 'GEAR_BRAKE_HOLD'
        u = owner.compute(v, w, *failed['body'][3:], False)
        assert owner.commands.legal(u) and np.max(abs(u-previous)-owner.commands.rate*.01/.08) <= 1e-10
        assert np.array_equal(u[:2], np.asarray(failed['last_ctrl'])[:2])
        controls.append(u.tolist())
    checks['exact_failed_request_brakes_in_unchanged_allocator'] = True
    checks['no_release_merely_after_200_if_actual_feedback_moving'] = True
    assert max(abs(owner.last[2:])) <= 1e-10
    body = failed['body'][:]; body[3:] = [0., 0.]
    encoders = failed['encoders'][:]
    v, w, proof = gate.select(.04, 0., native_tick=16505, body=body, last_ctrl=owner.last, encoders=encoders)
    assert v == w == 0. and not proof['released']
    checks['body_rest_but_steering_encoder_motion_denied'] = True
    encoders[2:] = [0., 0.]
    body[4] = .004
    assert gate.select(.04, 0., native_tick=16506, body=body, last_ctrl=owner.last, encoders=encoders)[:2] == (0., 0.)
    checks['actual_yaw_motion_denied'] = True
    body[4] = 0.
    v, w, proof = gate.select(.04, 0., native_tick=16507, body=body, last_ctrl=owner.last, encoders=encoders)
    assert (v, w) == (.04, 0.) and proof['released'] and proof['braking_native'] >= 200
    owner.compute(v, w, 0., 0., False)
    checks['release_uses_fresh_request_not_old_failed_request'] = True
    # Legacy assertion itself must remain active on the original state.
    owner.last = np.asarray(failed['last_ctrl']); owner.integral = failed['integral']
    try:
        owner.compute(*failed['request'][:2], *failed['body'][3:], False)
    except AssertionError as error:
        assert str(error) == 'FORWARD_BEFORE_COMPLETE_REVERSE_STOP'
    else:
        raise AssertionError('ORIGINAL_GUARD_WAS_REMOVED')
    checks['original_allocator_guard_still_rejects_direct_bypass'] = True
    # Both directions, exact boundary, rapid alternating commands, no queued
    # command replay, and no early release at 199 native steps.
    for initial, desired in [(1, -1), (-1, 1)]:
        g = GearHandoff(); stationary = [0.]*5; ctrl = [0., 0., initial*.5, initial*.5]
        for tick in range(200):
            vr = desired*.05 if tick % 2 == 0 else initial*.05
            chosen = g.select(vr, 0., native_tick=tick, body=stationary,
                              last_ctrl=ctrl if tick == 0 else [0.]*4, encoders=[0.]*4)
            assert chosen[:2] == (0., 0.)
        v, w, p = g.select(desired*.03, 0., native_tick=200, body=stationary, last_ctrl=[0.]*4, encoders=[0.]*4)
        assert v == desired*.03 and p['released'] and p['braking_native'] == 200
    checks['both_signs_200_native_and_rapid_reversals'] = True
    for corrupt in ['nan', 'clock', 'mixed_drive']:
        g = GearHandoff(); args = dict(native_tick=0, body=[0.]*5, last_ctrl=[0.]*4, encoders=[0.]*4)
        if corrupt == 'nan': args['body'][3] = float('nan')
        if corrupt == 'mixed_drive': args['last_ctrl'][2:] = [-.1, .1]
        if corrupt == 'clock':
            g.select(.05, 0., **args)
        try:
            g.select(.05, 0., **args)
        except AssertionError:
            pass
        else:
            raise AssertionError('INVALID_FEEDBACK_ACCEPTED ' + corrupt)
    checks['nonfinite_repeated_clock_and_mixed_sign_drive_rejected'] = True
    # All recorded static commands must be untouched; no need to rebuild a
    # model or run the plugin again to verify this pure command filter seam.
    static_count = 0
    for name in ['rpp_async_default_static_main', 'rpp_async_default_static_repeat']:
        g = GearHandoff()
        for row in json.loads((RAW / name / 'APPLIED_JOURNAL.json').read_text()):
            v, w, proof = g.select(*row['request'][:2], native_tick=row['before_native'], body=row['body'], last_ctrl=row['last_ctrl'], encoders=row['encoders'])
            assert [v, w, False] == row['request'] and proof['mode'] == 'UNCHANGED'
            static_count += 1
    checks['all_18390_actual_static_commands_unchanged'] = static_count == 18390
    summary = dict(passed=all(checks.values()), checks=checks,
                   original_failure_native_tick=16255, analytical_braking_commands=len(controls),
                   actual_static_journal_rows=static_count, models=0, integrations=0,
                   synthetic_rest_feedback_explicit=True, physical_transition_qualified=False)
    (O / 'GEAR_HANDOFF_QUALIFICATION.json').write_text(json.dumps(summary, indent=2)+'\n')
    (O / 'ANALYTICAL_BRAKING_CONTROLS.json').write_text(json.dumps(controls)+'\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
