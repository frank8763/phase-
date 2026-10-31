import time
import math
import numpy as np

_VIEWER = None
_TRAIL = []
_INIT_DONE = False

def tick(env, branch, step, mj):
    global _VIEWER, _INIT_DONE

    if branch != "rpccr_online":
        if step == 0:
            print(
                "V115_BASELINE_RUNNING=TRUE",
                "GUI_OPENS_WHEN_RPCCR_BRANCH_STARTS",
                flush=True
            )
        return

    import mujoco.viewer

    xy = np.asarray(
        env.robot_xy, dtype=float
    ).reshape(-1)[:2]

    goal = np.asarray(
        env.goal_xy, dtype=float
    ).reshape(-1)[:2]

    if not _INIT_DONE:
        _VIEWER = mujoco.viewer.launch_passive(
            env.model,
            env.data,
            show_left_ui=False,
            show_right_ui=False
        )

        if not _VIEWER.is_running():
            raise RuntimeError(
                "V115_GUI_WINDOW_NOT_RUNNING"
            )

        with _VIEWER.lock():
            center = (xy + goal) / 2.0

            _VIEWER.cam.lookat[:] = [
                float(center[0]),
                float(center[1]),
                0.15
            ]

            _VIEWER.cam.distance = 9.0
            _VIEWER.cam.azimuth = 90
            _VIEWER.cam.elevation = -65

        _INIT_DONE = True

        print(
            "V115_GUI_OPEN=TRUE",
            "MODE=LIVE_MUJOCO",
            "VIDEO_RECORDING=FALSE",
            flush=True
        )

    if not _VIEWER.is_running():
        raise RuntimeError(
            "V115_GUI_CLOSED_BEFORE_RUN_COMPLETE"
        )

    _TRAIL.append(xy.copy())

    path = getattr(
        env.inner, "dense_path", None
    )

    if path is None:
        path = np.empty((0, 2))
    else:
        path = np.asarray(
            path, dtype=float
        )

        if path.ndim != 2 or path.shape[1] < 2:
            path = np.empty((0, 2))
        else:
            path = path[:, :2]

    with _VIEWER.lock():
        scene = _VIEWER.user_scn
        scene.ngeom = 0

        def add_sphere(point, radius, color):
            if scene.ngeom >= scene.maxgeom:
                return

            p = np.asarray(
                [point[0], point[1], 0.25],
                dtype=float
            )

            mj.mjv_initGeom(
                scene.geoms[scene.ngeom],
                mj.mjtGeom.mjGEOM_SPHERE,
                [radius, radius, radius],
                p,
                np.eye(3).flatten(),
                color
            )

            scene.ngeom += 1


        def add_line(a, b, color, z=0.16):
            if scene.ngeom >= scene.maxgeom:
                return

            pa = np.asarray(a, dtype=float).reshape(2)
            pb = np.asarray(b, dtype=float).reshape(2)

            midpoint = (pa + pb) / 2.0

            pos = np.array(
                [midpoint[0], midpoint[1], z],
                dtype=float
            )

            # 蓝色与红色路径使用点列显示。
            radius = 0.037

            mj.mjv_initGeom(
                scene.geoms[scene.ngeom],
                mj.mjtGeom.mjGEOM_SPHERE,
                np.array(
                    [radius, radius, radius],
                    dtype=float
                ),
                pos,
                np.eye(3).reshape(-1),
                np.asarray(color, dtype=float)
            )

            scene.ngeom += 1

        # 蓝色：正在使用的规划路径。
        if len(path) >= 2:
            indices = np.unique(
                np.linspace(
                    0,
                    len(path)-1,
                    min(120, len(path)),
                    dtype=int
                )
            )

            for ia, ib in zip(
                indices[:-1], indices[1:]
            ):
                add_line(
                    path[ia],
                    path[ib],
                    [0.05, 0.30, 1.0, 1.0],
                    z=0.18
                )

        # 红色：机器人真实行驶轨迹。
        for a, b in zip(
            _TRAIL[:-1], _TRAIL[1:]
        ):
            add_line(
                a, b,
                [1.0, 0.05, 0.05, 1.0],
                z=0.23
            )

        # 绿色：真实目标位置。
        add_sphere(
            goal, 0.13,
            [0.0, 0.9, 0.15, 0.95]
        )

        # 第31步接管后，自动切到近距离观察。
        if step >= 31:
            _VIEWER.cam.lookat[:] = [
                float(xy[0]) + 0.6,
                float(xy[1]) + 0.3,
                0.15
            ]

            _VIEWER.cam.distance = 4.5

            print(
                "V115_NEW_PATH_VISIBLE=TRUE",
                "PATH_POINTS=", len(path),
                flush=True
            )

        # 显示MuJoCo原生接触点。
        _VIEWER.opt.flags[
            mj.mjtVisFlag.mjVIS_CONTACTPOINT
        ] = 1

    _VIEWER.sync()

    if (
        step % 10 == 0
        or step in (31, 56, 85, 100, 101, 102)
    ):
        print(
            "V115_LIVE",
            "STEP=", step,
            "GOAL_DISTANCE_M=",
            round(
                float(np.linalg.norm(goal-xy)), 4
            ),
            "PATH_POINTS=", len(path),
            flush=True
        )

    # 降低播放速度，方便用肉眼观察。
    time.sleep(0.12)


def close():
    global _VIEWER

    viewer = _VIEWER

    if viewer is None:
        return

    print(
        "V115_SIMULATION_ENDED=TRUE",
        "FINAL_POSE_VISIBLE=TRUE",
        flush=True
    )

    # 终点姿态停留40秒，供用户旋转、放大观察。
    deadline = time.monotonic() + 40.0

    while (
        viewer.is_running()
        and time.monotonic() < deadline
    ):
        time.sleep(0.1)

    viewer.close()
    _VIEWER = None

    print(
        "V115_GUI_CLOSED_NORMALLY=TRUE",
        flush=True
    )
