"""Offline robot-only articulation audit; geometry calculation from frozen B69. Never imported by online navigation."""
import math
import numpy as np

def extract_self_envelope(env, mj):
    """Only robot descendants are read; no world/obstacle pose or size access."""
    model, data = env.model, env.data
    root = mj.mj_name2id(model, mj.mjtObj.mjOBJ_BODY, 'mkmini_base')
    if root < 0:
        raise RuntimeError('Robot base absent')
    descendants = set()
    for bid in range(1, model.nbody):
        parent = bid
        while parent and parent != root:
            parent = int(model.body_parentid[parent])
        if parent == root:
            descendants.add(bid)
    q = data.qpos
    yaw = math.atan2(2*(q[3]*q[6]+q[4]*q[5]), 1-2*(q[5]**2+q[6]**2))
    c, s = math.cos(yaw), math.sin(yaw)
    inv = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    origin = np.asarray(data.xpos[root])
    entries = []
    for gid in range(model.ngeom):
        if int(model.geom_bodyid[gid]) not in descendants:
            continue
        if int(model.geom_contype[gid]) == 0 and int(model.geom_conaffinity[gid]) == 0:
            continue
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, gid) or f'unnamed_geom_{gid}'
        kind = int(model.geom_type[gid])
        size = np.asarray(model.geom_size[gid], dtype=float)
        rotation = inv@np.asarray(data.geom_xmat[gid]).reshape(3, 3)
        center = inv@(np.asarray(data.geom_xpos[gid])-origin)
        if kind == int(mj.mjtGeom.mjGEOM_BOX):
            extents = np.abs(rotation)@size
        elif kind == int(mj.mjtGeom.mjGEOM_SPHERE):
            extents = np.full(3, size[0])
        elif kind == int(mj.mjtGeom.mjGEOM_CAPSULE):
            extents = size[0]+size[1]*np.abs(rotation[:, 2])
        elif kind == int(mj.mjtGeom.mjGEOM_CYLINDER):
            # Rotation invariant circumsphere also covers the spinning/steering wheels.
            extents = np.full(3, math.hypot(size[0], size[1]))
        else:
            raise RuntimeError(f'Unaccounted active self geom {name}: {kind}')
        entries.append({'geom_id': gid, 'name': name, 'type': kind,
            'body_id': int(model.geom_bodyid[gid]), 'size': size.tolist(),
            'lower_xy': (center-extents)[:2].tolist(), 'upper_xy': (center+extents)[:2].tolist()})
    low = np.min([e['lower_xy'] for e in entries], axis=0)
    high = np.max([e['upper_xy'] for e in entries], axis=0)
    joints = []
    for jid in range(model.njnt):
        name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_JOINT, jid) or ''
        if 'steer' in name:
            joints.append({'name': name, 'range_rad': model.jnt_range[jid].tolist(),
                           'limited': bool(model.jnt_limited[jid])})
    return {'bounds_xy': np.r_[low, high].tolist(), 'active_robot_geoms': entries,
            'steering_joints': joints, 'max_steer_command_rad': float(env.inner.max_steer),
            'max_wheel_delta_per_public_step': float(env.inner.max_wheel_delta),
            'scope': 'current articulated configuration; cylinders rotation-enclosed; no obstacle truth'}
