"""Preserved real reversal, lossless segment edges and latest-field negatives."""
import json
from pathlib import Path
import numpy as np
from segments import split, validate, direction_allowed

R = Path(__file__).resolve().parents[2]
C = Path(__file__).resolve().parent
O = R/'runs'/C.name


def main():
    raw = R/'runs/v858_nav2_verified/v1346/rpp_async_default_dynamic_main'
    plans = json.loads((raw/'CAUSAL_ROUTE_RECORDS.json').read_text())
    old = json.loads((O/'premature_probe/RESULT.json').read_text())
    assert old['error'] is None
    assert old['cases'][0]['name'] == 'full' and old['cases'][0]['moving_signs'] == [-1]
    assert old['cases'][1]['name'] == 'forward_only' and old['cases'][1]['moving_signs'] == [1]
    checks = dict(actual_plugin_reproduced_premature_reverse_on_mixed_path=True,
                  actual_same_pose_ranges_plugin_forward_on_first_segment=True)
    source = json.loads((C/'SAVED_PREMATURE_REVERSAL.json').read_text())
    known = json.loads((R/'experiments/v855_renewal_worker/KNOWN_FIELD.json').read_text())
    positive = []; total_edges = 0
    for plan in plans:
        if 'rear_path_with_gears' not in plan: continue
        path = plan['rear_path_with_gears']; segments = split(path)
        rebuilt = [segments[0]['poses'][0]]
        for segment in segments:
            assert segment['poses'][0] == rebuilt[-1]
            rebuilt.extend(segment['poses'][1:])
        assert np.array_equal(np.asarray(rebuilt), np.asarray(path)[:, :3])
        total_edges += len(path)-1
        first = segments[0]; ball = (plan['ball'][:2], plan['ball'][2])
        ok, proof = validate(first, plan['body'], known, ball)
        assert ok, proof
        # A next-gear segment at its planned cusp is a synthetic software
        # state, explicitly not a measured physical arrival at that cusp.
        nxt = segments[1]; rear = nxt['poses'][0]
        body = [rear[0]+.3*np.cos(rear[2]), rear[1]+.3*np.sin(rear[2]), rear[2], 0., 0.]
        ok, proof = validate(nxt, body, known, ball); assert ok, proof
        positive.append(dict(plan=plan['index'], segments=len(segments), cusp_validation=proof))
        moved = body[:]; moved[0] += .2
        assert not validate(nxt, moved, known, ball)[0]
        turned = body[:]; turned[2] += .21
        assert not validate(nxt, turned, known, ball)[0]
        assert not validate(nxt, body, known, (ball[0], ball[1]+3.))[0]
    checks['all_original_edges_and_pose_yaws_preserved_in_order'] = total_edges == 288
    checks['all_three_admitted_routes_first_and_next_cusp_geometry'] = len(positive) == 3
    checks['moved_heading_and_new_obstacle_negatives'] = True
    # The actual premature reverse is blocked while the first segment is
    # active. Correct forward motion and a legitimate reverse segment pass.
    assert not direction_allowed(-.05, 1) and direction_allowed(.05, 1)
    assert direction_allowed(-.05, -1) and not direction_allowed(.05, -1)
    assert direction_allowed(0., 1) and direction_allowed(0., -1)
    checks['opposite_direction_never_forwarded_or_sign_flipped'] = True
    bad = [[0.,0.,0.,1.],[.04,0.,0.,0.]]
    try: split(bad)
    except AssertionError: pass
    else: raise AssertionError('INVALID_GEAR_ACCEPTED')
    checks['invalid_gear_negative'] = True
    result = dict(passed=all(checks.values()), checks=checks, actual_plugin_actions=2,
                  route_positives=positive, total_preserved_edges=total_edges,
                  planned_cusp_software_states_synthetic=True, models=0, physical_native=0,
                  physical_segment_tracking_qualified=False)
    (O/'SEGMENT_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result)); assert result['passed']


if __name__ == '__main__': main()
