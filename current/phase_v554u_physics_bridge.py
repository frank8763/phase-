
import importlib
import json
import runpy
from pathlib import Path

import numpy as np
import mujoco

JOB = Path(__file__).resolve().parent

state = importlib.import_module("v132_recovery_state")

native_step = mujoco.mj_step

stats = {"BACK": 0, "HOLD": 0}
checked = False

def bridge_step(model, data, *args, **kwargs):
    global checked

    snapshot = getattr(state, "STATE", None)

    mode = (
        snapshot.get("mode")
        if isinstance(snapshot, dict)
        else None
    )

    if mode in ("BACK", "HOLD"):

        if model.nu < 4:
            raise RuntimeError(
                "V495_BAD_ACTUATOR_COUNT"
            )

        # V487 已验证的后轮控制目标。
        target = -3.0 if mode == "BACK" else 0.0

        if not checked:
            for aid in range(4):

                lo, hi = [
                    float(t)
                    for t in model.actuator_ctrlrange[aid]
                ]

                name = mujoco.mj_id2name(
                    model,
                    mujoco.mjtObj.mjOBJ_ACTUATOR,
                    aid
                )

                print(
                    "V495_ACTUATOR",
                    aid,
                    name,
                    [lo, hi],
                    flush=True
                )

                desired = (
                    target if aid >= 2 else 0.0
                )

                if not lo <= desired <= hi:
                    raise RuntimeError(
                        "V495_ACTUATOR_RANGE_UNSAFE:"
                        + str(aid)
                    )

            checked = True

        # 只在恢复模式接管前轮转向和后轮驱动。
        # 不修改原始 MuJoCo 模型和物理参数。
        data.ctrl[0:2] = 0.0

        for aid in (2, 3):

            lo, hi = [
                float(t)
                for t in model.actuator_ctrlrange[aid]
            ]

            if not lo <= target <= hi:
                raise RuntimeError(
                    "V495_REVERSE_TARGET_OUT_OF_RANGE"
                )

            data.ctrl[aid] = target

        stats[mode] += 1
        n = stats[mode]

        if n <= 2 or n % 50 == 0:

            print(
                "V495_PHYSICS_OVERRIDE",
                json.dumps({
                    "mode": mode,
                    "physics_calls": n,
                    "rear_ctrl": np.asarray(
                        data.ctrl[2:4],
                        dtype=float
                    ).tolist()
                }),
                flush=True
            )

    return native_step(
        model, data, *args, **kwargs
    )

mujoco.mj_step = bridge_step
