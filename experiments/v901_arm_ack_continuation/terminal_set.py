"""Policy-visible finite refuge region; original navigation goal stays unchanged."""
import numpy as np
from refuge_logic import wait_ok

MIN_RETREAT_M = .75  # Original minimum refuge displacement, not a new arrival tolerance.

def membership(body, start, selected_goal, support, age):
    b, s, g = (np.asarray(x[:3], dtype=float) for x in (body, start, selected_goal))
    if not (np.isfinite(b).all() and np.isfinite(s).all() and np.isfinite(g).all()):
        return dict(passed=False, reason='NONFINITE_POSE')
    direction = g[:2] - s[:2]
    length = float(np.linalg.norm(direction))
    if support is None or not np.isfinite(age) or age < 0 or age > .2 or length < MIN_RETREAT_M:
        return dict(passed=False, reason='NO_FRESH_CAUSAL_REFUGE')
    progress = float((b[:2] - s[:2]) @ (direction / length))
    hold = wait_ok(b, support, age, hold=6.)
    return dict(passed=progress >= MIN_RETREAT_M and hold,
                projected_retreat_m=progress, minimum_retreat_m=MIN_RETREAT_M,
                current_six_second_hold_admitted=hold,
                reason='REGION_ENTRY' if progress >= MIN_RETREAT_M and hold else 'OUTSIDE_REGION')
