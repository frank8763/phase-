"""Fixed pose-feedback proposal; actuator allocation stays in the old adapter."""
import math

CAP = .42722137342572125


def request(state, reference, target, speed):
    if speed == 0.:
        return 0., 0., {'along': 0., 'cross': 0., 'heading': 0.}
    assert speed == .12
    dx, dy = reference[0]-state[0], reference[1]-state[1]
    c, s = math.cos(state[2]), math.sin(state[2])
    along, cross = c*dx+s*dy, -s*dx+c*dy
    heading = math.atan2(math.sin(reference[2]-state[2]),
                         math.cos(reference[2]-state[2]))
    curvature = math.tan(target)/.6 + 8.*cross + 5.*heading
    curvature = max(-math.tan(CAP)/.6, min(math.tan(CAP)/.6, curvature))
    v = max(.0, min(.12, speed+.5*along))
    return v, v*curvature, {'along': along, 'cross': cross, 'heading': heading}
