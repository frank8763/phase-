"""One fixed forward-only capture policy, after complete measured stop.

No reverse, no altered global target, no reference-clock reset. The caller
must certify the WHOLE candidate and append a new complete2200 stop.
"""
import math

CAP = .42722137342572125


def request(state, target):
    dx, dy = target[0]-state[0], target[1]-state[1]
    distance = math.hypot(dx,dy)
    if distance <= .012:
        return 0., 0., 'CAPTURED'
    c, s = math.cos(state[2]), math.sin(state[2])
    along, cross = c*dx+s*dy, -s*dx+c*dy
    if along <= .004:
        return 0., 0., 'NO_FORWARD_CAPTURE'
    heading = math.atan2(math.sin(target[2]-state[2]), math.cos(target[2]-state[2]))
    curvature = max(-math.tan(CAP)/.6,
                    min(math.tan(CAP)/.6, 8.*cross+5.*heading))
    speed = min(.03, max(.006, .5*along))
    return speed, speed*curvature, 'CAPTURING'
