"""Independent dense geometry audit: no online collision/search routines imported."""
import itertools
import math

import numpy as np

HALF = np.array([.44, .375])
SIGNS = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
NORMALS = np.column_stack((np.cos(np.arange(16)*math.pi/8),
                           np.sin(np.arange(16)*math.pi/8)))


def polygon_distance(first, second):
    """Convex SAT for overlap and edge-to-vertex distances for disjoint polygons."""
    edges = np.concatenate((np.roll(first, -1, axis=0)-first,
                            np.roll(second, -1, axis=0)-second))
    axes = np.column_stack((-edges[:, 1], edges[:, 0]))
    a, b = first @ axes.T, second @ axes.T
    disjoint = np.any((a.max(axis=0) < b.min(axis=0)) |
                      (b.max(axis=0) < a.min(axis=0)))
    if not disjoint:
        return 0.
    minima = []
    for points, polygon in [(first, second), (second, first)]:
        start = polygon
        delta = np.roll(polygon, -1, axis=0)-polygon
        relative = points[:, None, :]-start
        fraction = np.clip((relative*delta).sum(axis=2)/(delta*delta).sum(axis=1), 0., 1.)
        minima.append(float(np.linalg.norm(relative-fraction[..., None]*delta, axis=2).min()))
    return min(minima)


def enclosure(prior):
    upper = []
    lower = []
    for vertices in prior['vertices']:
        p = np.asarray(vertices)
        radius = np.sqrt(p[:, 1]**2+p[:, 2]**2)
        upper.append(float(np.max(p[:, 0]+radius))+2e-7+1e-6)
        lower.append(float(np.max(-p[:, 0]+radius))+2e-7+1e-6)
    bounds = np.array(upper+lower)
    points = []
    for i, j in itertools.combinations(range(16), 2):
        a = NORMALS[[i, j]]
        if abs(np.linalg.det(a)) < 1e-10:
            continue
        p = np.linalg.solve(a, bounds[[i, j]])
        if np.max(NORMALS @ p-bounds) <= 1e-8:
            points.append(p)
    points = np.unique(np.round(points, 10), axis=0)
    assert len(points) >= 3
    center = points.mean(axis=0)
    return points[np.argsort(np.arctan2(*(points-center)[:, ::-1].T))]


def audit(path, known, prior):
    rectangles = [np.array([x, y])+SIGNS*np.array([hx, hy])
                  for x, y, hx, hy in known['known_rectangles']]
    obstacle = enclosure(prior)
    poses = [np.asarray(path[0])]
    max_curvature = 0.
    for aa, bb in zip(path, path[1:]):
        a, b = np.asarray(aa), np.asarray(bb)
        direction = np.sign((b[:2]-a[:2]) @ [math.cos(a[2]), math.sin(a[2])])
        turn = math.atan2(math.sin(b[2]-a[2]), math.cos(b[2]-a[2]))
        curvature = turn/(direction*.1)
        max_curvature = max(max_curvature, abs(curvature))
        distances = np.arange(1, 201)*(.1/200)*direction
        angle = a[2]+curvature*distances
        if abs(curvature) < 1e-10:
            x = a[0]+distances*math.cos(a[2])
            y = a[1]+distances*math.sin(a[2])
        else:
            x = a[0]+(np.sin(angle)-math.sin(a[2]))/curvature
            y = a[1]-(np.cos(angle)-math.cos(a[2]))/curvature
        dense = np.column_stack((x, y, angle))
        assert np.max(abs(dense[-1]-b)) < 1e-8
        poses.extend(dense)
    min_static, min_dynamic = math.inf, math.inf
    for x, y, angle in poses:
        c, s = math.cos(angle), math.sin(angle)
        rotation = np.array([[c, -s], [s, c]])
        body = SIGNS*HALF @ rotation.T+np.array([x, y])
        static = float(np.min(5.-abs(body)))
        for rectangle in rectangles:
            static = min(static, polygon_distance(body, rectangle))
        for cx, cy, radius in known['known_circles']:
            local = (np.array([cx-x, cy-y]) @ rotation)
            offset = np.abs(local)-HALF
            static = min(static, float(np.linalg.norm(np.maximum(offset, 0)))-radius)
        min_static = min(min_static, static)
        min_dynamic = min(min_dynamic, polygon_distance(body, obstacle)-.1-2e-6)
    rho = math.sqrt(.44**2+.375**2)
    original_reserve = .04+rho*.035+.1*(.13+rho*.16)+.02*(.13+rho*.16+.08)
    interpolation = .5*(.1/200)*(1.+rho*.758770385)
    static_lower = min_static-original_reserve-interpolation
    dynamic_lower = min_dynamic-original_reserve-interpolation
    return dict(passed=min(static_lower, dynamic_lower) >= .155 and max_curvature <= .758770385+1e-8,
                samples=len(poses), static_lower_m=static_lower,
                dynamic_cycle_lower_m=dynamic_lower, maximum_curvature=max_curvature,
                interpolation_reserve_m=interpolation,
                models=0, integrations=0,
                scope='Independent geometric reference audit, not actual tracking or arrival.')
