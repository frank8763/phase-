"""Rigid reference-point conversion; original abstract scan is body-centered."""
import math

REAR_OFFSET = .30


def rear_pose(pose):
    x, y, yaw = map(float, pose)
    if not all(math.isfinite(v) for v in [x, y, yaw]): raise ValueError('NONFINITE_POSE')
    return [x - REAR_OFFSET * math.cos(yaw), y - REAR_OFFSET * math.sin(yaw), yaw]


def rear_body(body):
    if len(body) != 5: raise ValueError('BODY_SHAPE')
    if not all(math.isfinite(float(v)) for v in body): raise ValueError('NONFINITE_BODY')
    return rear_pose(body[:3]) + list(body[3:])


def rear_footprint(vertices):
    return [[float(x) + REAR_OFFSET, float(y)] for x, y in vertices]
