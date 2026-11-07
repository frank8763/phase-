"""Independent array calculation of the stated ideal proposal equations, not physics."""
import numpy as np

from cases import BATCH, HORIZON


def evaluate(case, parameters):
    xy = np.tile(case['pose'][:2], (BATCH, 1))
    yaw = np.full(BATCH, case['pose'][2])
    commands = np.tile(case['last'], (BATCH, 1))
    path = case['path']
    arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(path[:, :2], axis=0), axis=1))]
    poses = np.empty((BATCH, HORIZON, 3))
    controls = np.empty((BATCH, HORIZON, 4))
    for tick in range(HORIZON):
        nearest = np.argmin(np.sum((xy[:, None] - path[None, :, :2]) ** 2, axis=2), axis=1)
        target_index = np.argmin(abs(arc[None] - (arc[nearest] + parameters['lookahead'])[:, None]), axis=1)
        relative = path[target_index, :2] - xy
        lateral = -np.sin(yaw) * relative[:, 0] + np.cos(yaw) * relative[:, 1]
        angle = np.arctan2(1.2 * lateral, np.maximum(np.sum(relative ** 2, axis=1), .02))
        angle = np.clip(np.where(parameters['follow'], angle + parameters['offsets'][:, tick],
                                 parameters['offsets'][:, tick]), -.42722137342572125, .42722137342572125)
        radius = .6 / np.maximum(np.tan(abs(angle)), 1e-12)
        inner, outer = np.arctan2(.6, radius - .27), np.arctan2(.6, radius + .27)
        target = np.empty_like(commands)
        target[:, 0] = np.where(angle >= 0, inner, -outer)
        target[:, 1] = np.where(angle >= 0, outer, -inner)
        wheel = parameters['wheels'][:, tick]
        delta = 8. * wheel * np.tan(angle) * .54 / 1.2
        target[:, 2] = np.where(parameters['follow'], wheel - delta, wheel)
        target[:, 3] = np.where(parameters['follow'], wheel + delta, wheel)
        stop = tick >= parameters['brakes']
        target[stop, :2] = commands[stop, :2]
        target[stop, 2:] = 0.
        commands = np.clip(np.clip(target, case['lower'], case['upper']),
                           commands - case['rate'], commands + case['rate'])
        velocity = .06 * (commands[:, 2] + commands[:, 3])
        omega = velocity * np.tan((commands[:, 0] + commands[:, 1]) / 2.) / .6
        heading = yaw + .04 * omega
        xy[:, 0] += .08 * velocity * np.cos(heading)
        xy[:, 1] += .08 * velocity * np.sin(heading)
        yaw += .08 * omega
        poses[:, tick, :2], poses[:, tick, 2] = xy, yaw
        controls[:, tick] = commands
    flat = poses.reshape(-1, 3)
    c, s = np.cos(flat[:, 2]), np.sin(flat[:, 2])
    hx, hy = case['half']
    ex, ey = abs(c) * hx + abs(s) * hy, abs(s) * hx + abs(c) * hy
    clearance = np.minimum.reduce((flat[:, 0] - ex + 5., 5. - flat[:, 0] - ex,
                                    flat[:, 1] - ey + 5., 5. - flat[:, 1] - ey))
    # Iterate objects rather than the GPU's batched object-axis reductions.
    for x, y, rx, ry in case['rectangles']:
        dx, dy = x - flat[:, 0], y - flat[:, 1]
        separation = np.maximum.reduce((abs(dx) - rx - ex, abs(dy) - ry - ey,
                                         abs(dx * c + dy * s) - hx - rx * abs(c) - ry * abs(s),
                                         abs(-dx * s + dy * c) - hy - rx * abs(s) - ry * abs(c)))
        clearance = np.minimum(clearance, separation)
    for x, y, radius in case['circles']:
        dx, dy = x - flat[:, 0], y - flat[:, 1]
        lx, ly = abs(dx * c + dy * s) - hx, abs(-dx * s + dy * c) - hy
        distance = np.where(np.maximum(lx, ly) <= 0., np.maximum(lx, ly),
                            np.hypot(np.maximum(lx, 0.), np.maximum(ly, 0.))) - radius
        clearance = np.minimum(clearance, distance)
    clearance = clearance.reshape(BATCH, HORIZON)
    route_distance = np.sum((poses[:, :, None, :2] - path[None, None, :, :2]) ** 2, axis=3)
    contour = np.mean(np.sqrt(np.min(route_distance, axis=2)), axis=1)
    start_index = np.argmin(np.sum((case['pose'][:2] - path[:, :2]) ** 2, axis=1))
    progress = arc[np.argmin(route_distance[:, -1], axis=1)] - arc[start_index]
    goal_distance = np.linalg.norm(poses[:, -1, :2] - case['goal'], axis=1)
    penalty = np.mean(np.maximum(.18 - clearance, 0.) ** 2, axis=1)
    effort = np.mean(np.diff(controls, axis=1) ** 2, axis=(1, 2))
    cost = goal_distance + 2. * contour - 2. * progress + 1000. * penalty + .02 * effort + 2. * (.06 * controls[:, -1, 2:].sum(1)) ** 2
    return poses, controls, cost, np.argsort(cost, kind='stable')
