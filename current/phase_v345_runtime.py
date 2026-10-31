
import json
import numpy as np

EVENT_NAME = "real_circle_obs_10"
EVENT_XY = np.array(
    [0.5619897334275917, 2.402208204207623],
    dtype=np.float64,
)

STATE = {}

class SensorProxy:
    def __init__(self, real, circles):
        self._real = real

        base = np.asarray(
            getattr(real, "circle_obstacles", []),
            dtype=np.float32
        ).reshape(-1, 3)

        additional = np.asarray(
            circles, dtype=np.float32
        ).reshape(-1, 3)

        self.circle_obstacles = np.concatenate(
            (base, additional), axis=0
        )

    def __getattr__(self, name):
        return getattr(self._real, name)


def objects(env):
    seen = set()
    current = env

    for _ in range(15):
        if current is None or id(current) in seen:
            break

        seen.add(id(current))
        yield current

        try:
            current = object.__getattribute__(
                current, "__dict__"
            ).get("inner")
        except Exception:
            break


def event_circles(env, mujoco):
    model = env.model
    data = env.data

    gid = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        EVENT_NAME
    )

    if gid < 0:
        return np.empty((0, 3), dtype=np.float32)

    if (
        int(model.geom_contype[gid]) == 0
        or int(model.geom_conaffinity[gid]) == 0
        or float(model.geom_pos[gid, 2]) < -1.0
    ):
        return np.empty((0, 3), dtype=np.float32)

    xy = np.asarray(
        data.geom_xpos[gid, :2], dtype=float
    )

    radius = float(model.geom_size[gid, 0])

    return np.asarray(
        [[xy[0], xy[1], radius]],
        dtype=np.float32
    )


def install_sensor_hooks(env, mujoco):
    hooks = []
    visited = set()

    names = (
        "_phase17c_get_lidar",
        "_get_lidar",
        "_phase14_get_lidar",
        "_phase15_get_lidar",
        "_phase16_get_lidar",
    )

    for obj in objects(env):
        for name in names:
            try:
                method = getattr(obj, name, None)
                fn = getattr(method, "__func__", None)
                if fn is None:
                    continue

                module = str(
                    getattr(fn, "__module__", "")
                )

                if not (
                    module.startswith("training.phase")
                    or module.startswith("envs.phase")
                ):
                    continue

                namespace = fn.__globals__
                key = id(namespace)

                if key in visited:
                    continue

                original = namespace.get(
                    "get_lidar_features"
                )

                if not callable(original):
                    continue

                visited.add(key)

                def wrapped(
                    sensor_env,
                    *args,
                    _original=original,
                    **kwargs
                ):
                    extra = event_circles(
                        env, mujoco
                    )

                    if len(extra) == 0:
                        return _original(
                            sensor_env,
                            *args,
                            **kwargs
                        )

                    return _original(
                        SensorProxy(sensor_env, extra),
                        *args,
                        **kwargs
                    )

                namespace["get_lidar_features"] = wrapped

                hooks.append(
                    (namespace, original, module)
                )

            except Exception as error:
                print(
                    "V345_HOOK_DISCOVERY_ERROR",
                    repr(error),
                    flush=True
                )

    return hooks


def map_arrays(env):
    fn = getattr(
        env,
        "_phase21_v4_known_map_obstacles",
        None
    )

    if not callable(fn):
        raise RuntimeError(
            "V345_KNOWN_MAP_API_MISSING"
        )

    result = fn()

    if not isinstance(result, (tuple, list)):
        raise RuntimeError(
            "V345_KNOWN_MAP_FORMAT_INVALID"
        )

    if len(result) < 2:
        raise RuntimeError(
            "V345_KNOWN_MAP_ITEMS_INVALID"
        )

    rectangles = np.asarray(
        result[0], dtype=np.float64
    ).reshape(-1, 4)

    circles = np.asarray(
        result[1], dtype=np.float64
    ).reshape(-1, 3)

    return rectangles.copy(), circles.copy()


def map_equal(a, b):
    return (
        np.array_equal(a[0], b[0])
        and np.array_equal(a[1], b[1])
    )


def distance_to_known(point, radius, arrays):
    rects, circles = arrays
    distances = []

    for x, y, hx, hy in rects:
        dx = max(
            abs(float(point[0]) - x) - hx,
            0.0
        )

        dy = max(
            abs(float(point[1]) - y) - hy,
            0.0
        )

        distances.append(
            float(np.hypot(dx, dy)) - radius
        )

    for x, y, r in circles:
        distances.append(
            float(np.hypot(
                float(point[0]) - x,
                float(point[1]) - y
            )) - radius - r
        )

    return min(distances) if distances else float("inf")


def snapshot(env, obs):
    return {
        "obs": np.asarray(
            obs, dtype=np.float64
        ).reshape(-1).copy(),
        "qpos": env.data.qpos.copy(),
        "qvel": env.data.qvel.copy(),
    }


def activate(env, branch, step, obs, mujoco):
    model = env.model
    data = env.data

    gid = mujoco.mj_name2id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        EVENT_NAME
    )

    if gid < 0:
        raise RuntimeError(
            "V345_EVENT_GEOMETRY_MISSING"
        )

    if branch in STATE:
        raise RuntimeError(
            "V345_EVENT_ALREADY_ACTIVE"
        )

    if int(model.geom_bodyid[gid]) != 0:
        raise RuntimeError(
            "V345_EVENT_NOT_WORLD_FIXED"
        )

    if (
        int(model.geom_contype[gid]) != 0
        or int(model.geom_conaffinity[gid]) != 0
        or float(model.geom_pos[gid, 2]) > -5.0
    ):
        raise RuntimeError(
            "V345_EVENT_NOT_PARKED"
        )


    # V346: select one scene event, replay identically in both arms.
    if branch == "frozen_original":

        import importlib.util

        _v346_nominal = EVENT_XY.copy()
        # V23: scene-generation only; no controller change
        _v23_path = np.asarray(
            getattr(env.inner, 'dense_path', []),
            dtype=np.float64
        )
        if (
            _v23_path.ndim != 2
            or _v23_path.shape[0] < 10
            or _v23_path.shape[1] < 2
            or not np.isfinite(_v23_path[:, :2]).all()
        ):
            raise RuntimeError('V23_PRE_EVENT_PATH_INVALID')
        _v23_xy = _v23_path[:, :2]
        _v23_robot = np.asarray(
            env.robot_xy, dtype=np.float64
        ).reshape(2)
        _v23_goal = np.asarray(
            env.goal_xy, dtype=np.float64
        ).reshape(2)
        _v23_segment = np.linalg.norm(
            np.diff(_v23_xy, axis=0), axis=1
        )
        _v23_arc = np.concatenate((
            np.array([0.0]),
            np.cumsum(_v23_segment)
        ))
        _v23_nearest = int(np.argmin(
            np.linalg.norm(
                _v23_xy - _v23_robot, axis=1
            )
        ))
        _v23_forward = (
            _v23_arc - _v23_arc[_v23_nearest]
        )
        _v23_robot_dist = np.linalg.norm(
            _v23_xy - _v23_robot, axis=1
        )
        _v23_goal_dist = np.linalg.norm(
            _v23_xy - _v23_goal, axis=1
        )
        _v23_eligible = np.flatnonzero(
            (_v23_forward >= 1.15)
            & (_v23_forward <= 2.40)
            & (_v23_robot_dist >= 1.10)
            & (_v23_robot_dist <= 2.50)
            & (_v23_goal_dist >= 1.20)
        )
        if len(_v23_eligible) == 0:
            raise RuntimeError(
                'V23_NO_FORWARD_PATH_SECTION'
            )
        _v23_index = int(
            _v23_eligible[np.argmin(
                np.abs(
                    _v23_forward[_v23_eligible]
                    - 1.60
                )
            )]
        )
        _v346_nominal = (
            _v23_xy[_v23_index].copy()
        )
        print(
            'V23_PATH_CONDITIONED_NOMINAL',
            json.dumps({
                'branch':branch,
                'path_points':int(len(_v23_xy)),
                'nominal_xy':_v346_nominal.tolist(),
                'robot_distance_m':float(
                    _v23_robot_dist[_v23_index]
                ),
                'forward_arc_m':float(
                    _v23_forward[_v23_index]
                ),
                'eligible_points':int(
                    len(_v23_eligible)
                )
            }),
            flush=True
        )

        _v346_robot = np.asarray(
            env.robot_xy, dtype=np.float64
        ).reshape(2)

        _v346_static_map = map_arrays(env)

        _v346_radius = float(
            model.geom_size[gid, 0]
        )

        _v346_direction = (
            _v346_nominal - _v346_robot
        )

        _v346_original_distance = float(
            np.linalg.norm(_v346_direction)
        )

        if _v346_original_distance < 0.5:
            raise RuntimeError(
                "V346_INVALID_NOMINAL_EVENT_DIRECTION"
            )

        _v346_direction /= _v346_original_distance

        _v346_bounds_min = float(
            getattr(env, "map_min", -5.0)
        )

        _v346_bounds_max = float(
            getattr(env, "map_max", 5.0)
        )

        _v346_candidates = []

        # Search near the original event, not over the whole map.
        # The event radius and required clearance remain unchanged.
        for _v346_ix in range(-18, 19):

            for _v346_iy in range(-18, 19):

                _v346_offset = np.array(
                    [
                        0.05 * _v346_ix,
                        0.05 * _v346_iy,
                    ],
                    dtype=np.float64
                )

                _v346_offset_norm = float(
                    np.linalg.norm(_v346_offset)
                )

                if _v346_offset_norm > 0.90:
                    continue

                _v346_point = (
                    _v346_nominal + _v346_offset
                )

                if not (
                    _v346_bounds_min + 0.45
                    < _v346_point[0]
                    < _v346_bounds_max - 0.45
                    and
                    _v346_bounds_min + 0.45
                    < _v346_point[1]
                    < _v346_bounds_max - 0.45
                ):
                    continue

                _v346_relative = (
                    _v346_point - _v346_robot
                )

                _v346_distance = float(
                    np.linalg.norm(_v346_relative)
                )

                if not (
                    1.05 <= _v346_distance <= 2.25
                ):
                    continue

                _v346_direction_dot = float(
                    np.dot(
                        _v346_relative / _v346_distance,
                        _v346_direction
                    )
                )

                if _v346_direction_dot < 0.88:
                    continue

                _v346_clearance = (
                    distance_to_known(
                        _v346_point,
                        _v346_radius,
                        _v346_static_map
                    )
                )

                # Keep the strict original >= 0.30 m gate.
                # The extra 0.02 m is numerical robustness.
                if _v346_clearance < 0.32:
                    continue

                _v346_score = (
                    _v346_offset_norm
                    + 0.20 * abs(
                        _v346_distance - 1.20
                    )
                    + 0.30 * (
                        1.0 - _v346_direction_dot
                    )
                )

                _v346_candidates.append(
                    (
                        _v346_score,
                        _v346_point.copy(),
                        _v346_clearance,
                        _v346_distance
                    )
                )

        _v346_candidates.sort(
            key=lambda item: item[0]
        )

        _v346_spec = importlib.util.spec_from_file_location(
            "phase_v346_original_sensor",
            str(
                __import__("pathlib").Path.home()
                / "catkin_ws/src/mk-mini/"
                "training/phase14_lidar_depth_nav/"
                "envs/phase14_sensor_utils.py"
            )
        )

        if (
            _v346_spec is None
            or _v346_spec.loader is None
        ):
            raise RuntimeError(
                "V346_SENSOR_IMPORT_FAILED"
            )

        _v346_sensor = (
            importlib.util.module_from_spec(
                _v346_spec
            )
        )

        _v346_spec.loader.exec_module(
            _v346_sensor
        )

        _v346_num_rays = int(
            getattr(
                env,
                "phase17c_lidar_num_rays",
                32
            )
        )

        _v346_max_range = float(
            getattr(
                env,
                "phase17c_lidar_max_range",
                3.0
            )
        )

        _v346_base_scan = (
            _v346_sensor.get_lidar_features(
                env,
                num_rays=_v346_num_rays,
                max_range=_v346_max_range
            )
        )

        _v346_selected = None

        # Check actual software-ray visibility for eligible positions.
        for (
            _v346_score,
            _v346_point,
            _v346_clearance,
            _v346_distance
        ) in _v346_candidates:

            _v346_extra = np.asarray(
                [[
                    _v346_point[0],
                    _v346_point[1],
                    _v346_radius
                ]],
                dtype=np.float32
            )

            _v346_probe = SensorProxy(
                env, _v346_extra
            )

            _v346_event_scan = (
                _v346_sensor.get_lidar_features(
                    _v346_probe,
                    num_rays=_v346_num_rays,
                    max_range=_v346_max_range
                )
            )

            _v346_changed = np.flatnonzero(
                _v346_base_scan - _v346_event_scan
                > 0.02
            )

            if len(_v346_changed) == 0:
                continue

            _v346_selected = (
                _v346_point.copy(),
                float(_v346_clearance),
                float(_v346_distance),
                _v346_changed.tolist()
            )

            break

        print(
            "V346_SCENE_SELECTION_AUDIT",
            json.dumps({
                "candidate_count":
                    len(_v346_candidates),
                "visible_safe_candidate_found":
                    _v346_selected is not None,
                "original_event_xy":
                    _v346_nominal.tolist(),
                "original_strict_clearance_m":
                    float(distance_to_known(
                        _v346_nominal,
                        _v346_radius,
                        _v346_static_map
                    )),
                "minimum_required_clearance_m": 0.30,
                "radius_m": _v346_radius
            }),
            flush=True
        )

        if _v346_selected is None:
            raise RuntimeError(
                "V346_NO_SAFE_VISIBLE_EVENT_POSITION"
            )

        (
            _v346_xy,
            _v346_margin,
            _v346_robot_dist,
            _v346_indices
        ) = _v346_selected

        EVENT_XY[:] = _v346_xy

        STATE["v346_event_xy"] = (
            _v346_xy.copy()
        )

        print(
            "V346_EVENT_SELECTED",
            json.dumps({
                "xy": _v346_xy.tolist(),
                "static_clearance_m":
                    _v346_margin,
                "robot_distance_m":
                    _v346_robot_dist,
                "changed_lidar_rays":
                    _v346_indices,
                "radius_m": _v346_radius
            }),
            flush=True
        )

    elif branch == "rpccr_online":

        _v346_replay = STATE.get(
            "v346_event_xy"
        )

        if _v346_replay is None:
            raise RuntimeError(
                "V346_EVENT_REPLAY_MISSING"
            )

        EVENT_XY[:] = _v346_replay

        print(
            "V346_EVENT_REPLAY",
            json.dumps({
                "xy": EVENT_XY.tolist(),
                "same_as_control": True
            }),
            flush=True
        )

    before = snapshot(env, obs)

    if branch == "frozen_original":
        STATE["reference"] = before

    elif branch == "rpccr_online":
        reference = STATE.get("reference")

        if reference is None:
            raise RuntimeError(
                "V345_PAIR_REFERENCE_MISSING"
            )

        diffs = {
            key: float(np.max(
                np.abs(before[key] - reference[key])
            ))
            for key in ("obs", "qpos", "qvel")
        }

        parity = (
            diffs["obs"] <= 1e-5
            and diffs["qpos"] <= 1e-6
            and diffs["qvel"] <= 1e-6
        )

        print(
            "V345_PRE_EVENT_PARITY",
            json.dumps({
                "pass": parity,
                "differences": diffs
            }),
            flush=True
        )

        if not parity:
            raise RuntimeError(
                "V345_PRE_EVENT_PARITY_FAILED"
            )

    distance = float(np.linalg.norm(
        np.asarray(env.robot_xy).reshape(2)
        - EVENT_XY
    ))

    radius = float(model.geom_size[gid, 0])

    known_before = map_arrays(env)

    clearance = distance_to_known(
        EVENT_XY, radius, known_before
    )

    if distance < 0.9:
        raise RuntimeError(
            "V345_UNSAFE_EVENT_DISTANCE"
        )

    if clearance < 0.30:
        raise RuntimeError(
            "V345_INSUFFICIENT_STATIC_CLEARANCE"
        )

    original_geom = {
        "pos": model.geom_pos[gid].copy(),
        "contype": int(model.geom_contype[gid]),
        "conaffinity": int(
            model.geom_conaffinity[gid]
        ),
        "rgba": model.geom_rgba[gid].copy(),
    }

    # Register restoration data before changing physics.
    entry = {
        "gid": gid,
        "original_geom": original_geom,
        "hooks": [],
        "known_before": known_before,
        "active": False,
        "contact_seen": False,
        "policy_lidar_matched": False,
    }

    STATE[branch] = entry

    model.geom_pos[gid] = [
        float(EVENT_XY[0]),
        float(EVENT_XY[1]),
        0.25
    ]

    model.geom_contype[gid] = 1
    model.geom_conaffinity[gid] = 1
    model.geom_rgba[gid, 3] = 1.0

    mujoco.mj_forward(model, data)

    entry["active"] = True

    current = map_arrays(env)
    map_pass = map_equal(
        known_before, current
    )

    print(
        "V345_MAP_GATE",
        json.dumps({
            "branch": branch,
            "map_interface_unchanged": map_pass,
            "known_rectangles": len(current[0]),
            "known_circles": len(current[1])
        }),
        flush=True
    )

    if not map_pass:
        raise RuntimeError(
            "V345_KNOWN_MAP_CHANGED"
        )

    entry["hooks"] = install_sensor_hooks(
        env, mujoco
    )

    print(
        "V345_EVENT_ON",
        json.dumps({
            "branch": branch,
            "step": step,
            "geom_id": gid,
            "xy": EVENT_XY.tolist(),
            "robot_distance_m": distance,
            "static_clearance_m": clearance,
            "sensor_hook_modules": [
                item[2]
                for item in entry["hooks"]
            ],
            "persistent": True
        }),
        flush=True
    )

    if not entry["hooks"]:
        raise RuntimeError(
            "V345_NO_ACTIVE_SENSOR_HOOK"
        )


def audit(env, branch, step, obs, mujoco):
    entry = STATE.get(branch)

    if not entry or not entry["active"]:
        return

    gid = entry["gid"]
    model = env.model
    data = env.data

    contacts = []

    for i in range(int(data.ncon)):
        c = data.contact[i]

        g1 = int(c.geom1)
        g2 = int(c.geom2)

        if gid not in (g1, g2):
            continue

        other = g2 if g1 == gid else g1

        other_name = mujoco.mj_id2name(
            model,
            mujoco.mjtObj.mjOBJ_GEOM,
            other
        )

        contacts.append({
            "other_geom": other_name,
            "penetration_m": float(c.dist)
        })

    if contacts:
        entry["contact_seen"] = True

    obs_array = np.asarray(
        obs, dtype=np.float64
    ).reshape(-1)

    saved = np.asarray(
        getattr(env, "phase17c_last_lidar", []),
        dtype=np.float64
    ).reshape(-1)

    matching_starts = []

    if (
        len(saved) >= 8
        and np.all(np.isfinite(saved))
        and len(obs_array) >= len(saved)
    ):
        for i in range(
            len(obs_array) - len(saved) + 1
        ):
            if np.allclose(
                obs_array[i:i+len(saved)],
                saved,
                atol=1e-5,
                rtol=0
            ):
                matching_starts.append(i)

    if matching_starts:
        entry["policy_lidar_matched"] = True

    distance = float(np.linalg.norm(
        np.asarray(env.robot_xy).reshape(2)
        - EVENT_XY
    ))

    if (
        step in (41, 42, 45, 46, 50, 51, 52)
        or contacts
    ):
        print(
            "V345_RUNTIME_AUDIT",
            json.dumps({
                "branch": branch,
                "step": step,
                "event_active": bool(
                    model.geom_contype[gid]
                ),
                "robot_distance_m": distance,
                "saved_lidar_size": len(saved),
                "policy_obs_size": len(obs_array),
                "lidar_matching_obs_offsets":
                    matching_starts[:8],
                "event_contacts": contacts,
            }),
            flush=True
        )


def restore(env, branch, mujoco):
    entry = STATE.get(branch)

    if not entry:
        return

    model = env.model
    data = env.data
    gid = entry["gid"]

    errors = []

    # Restore original sensor function bindings.
    for namespace, original, module in reversed(
        entry["hooks"]
    ):
        try:
            namespace["get_lidar_features"] = original
        except Exception as error:
            errors.append(
                module + ":" + repr(error)
            )

    original = entry["original_geom"]

    try:
        model.geom_pos[gid] = original["pos"]

        model.geom_contype[gid] = original["contype"]

        model.geom_conaffinity[gid] = (
            original["conaffinity"]
        )

        model.geom_rgba[gid] = original["rgba"]

        mujoco.mj_forward(model, data)

    except Exception as error:
        errors.append(
            "PHYSICS_RESTORE:" + repr(error)
        )

    print(
        "V345_EVENT_OFF",
        json.dumps({
            "branch": branch,
            "restored": not errors,
            "event_contact_seen":
                entry["contact_seen"],
            "policy_lidar_window_matched":
                entry["policy_lidar_matched"],
            "errors": errors
        }),
        flush=True
    )

    STATE.pop(branch, None)
