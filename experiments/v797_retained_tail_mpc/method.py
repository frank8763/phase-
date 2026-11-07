"""Finite CEM proposals and known-map observation utility, never a safety oracle."""
import numpy as np
from types import SimpleNamespace

LOW = np.array([-.42, 0., -6., -.42, 0., -6.])
HIGH = np.array([.42, 6., 6., .42, 6., 6.])
ANCHORS = np.array([[0, 0, 0, 0, 0, 0], [0, 3, 0, 0, 3, 0],
                    [.42, 0, 6, 0, 3, 0], [-.42, 0, -6, 0, 3, 0]], float)


def schedule(parameters, last, command_map):
    p = np.asarray(parameters, float)
    assert p.shape == (6,) and np.all(p >= LOW) and np.all(p <= HIGH)
    a = np.array([p[0], p[0], p[1]-p[2], p[1]+p[2]])
    b = np.array([p[3], p[3], p[4]-p[5], p[4]+p[5]])
    brake = b.copy(); brake[2:] = 0.
    commands = []; command = np.asarray(last, float).copy()
    for tick in range(0, 328, 8):
        target = a if tick < 64 else b if tick < 160 else brake
        command = command_map.step(target, command)
        command_map.assert_first(command, last if tick == 0 else commands[-1])
        commands.extend([command.copy() for _ in range(8)])
    return np.asarray(commands)


def samples(standard, mean, std, incumbent, iteration):
    values = np.clip(mean + standard * std, LOW, HIGH)
    values[0] = mean
    if iteration == 0:
        values[:4] = ANCHORS
    elif incumbent is not None:
        values[1] = incumbent
    return values


def update(values, scores, mean, std):
    elite = np.argsort(-np.asarray(scores), kind='stable')[:8]
    mean = .25*mean + .75*values[elite].mean(axis=0)
    std = np.maximum(.25*std + .75*values[elite].std(axis=0), .04*(HIGH-LOW))
    return mean, std, elite


def opportunity(poses, protocol, domain, initial_xy):
    """Possible useful ray coverage using ONLY static prior; utility, not evidence.

    No hypothetical packet is admitted to the causal domain. Max-range rays are
    discarded, as in the actual free-space certificate. This is an optimistic
    visibility heuristic; future unknown occlusion/dropout is not guaranteed.
    """
    from phase14_sensor_utils import ray_cast_distance
    delta = np.asarray(protocol['goal_xy']) - initial_xy
    forward = delta / np.linalg.norm(delta); lateral = np.array([-forward[1], forward[0]])
    points = np.asarray([initial_xy + u*forward + v*lateral
                         for u in np.arange(.5, 2.51, .10)
                         for v in np.arange(-.6, .61, .10)])
    ids = np.rint((points+6.)/.01).astype(int)
    possible = domain.possible[ids[:, 0], ids[:, 1]]
    if not possible.any():
        return 0.
    points = points[possible]; covered = np.zeros(len(points), bool)
    env = SimpleNamespace(map_min=-5., map_max=5.,
                          rect_obstacles=np.asarray(protocol['known_rectangles'], np.float32),
                          circle_obstacles=np.asarray(protocol['known_circles'], np.float32))
    for pose in np.asarray(poses)[[63, 159]]:
        env.robot_xy = pose[:2].astype(np.float32); env.robot_yaw = float(pose[2])
        for angles, bound in [(np.arange(32)*2*np.pi/32, .06),
                              (np.linspace(-np.deg2rad(35), np.deg2rad(35), 15), .09)]:
            for angle in angles+pose[2]:
                z = float(ray_cast_distance(env, float(angle), 3., .08))
                if z >= 3. or z <= bound+.05:
                    continue
                direction = np.array([np.cos(angle), np.sin(angle)])
                offsets = points-pose[:2]; along = offsets@direction
                cross = abs(offsets[:, 0]*direction[1]-offsets[:, 1]*direction[0])
                covered |= (along >= 0) & (along < z-bound-.08) & (cross < .07)
    return float(covered.mean())


def merit(progress, heading, opportunity_value, clearance, self_margin, speed, angular):
    violation = (100.*max(0., .155-clearance) + 100.*max(0., .002-self_margin)
                 + 10.*max(0., speed-.025) + 10.*max(0., angular-.025))
    return float(progress - .05*heading + .025*opportunity_value - violation)
