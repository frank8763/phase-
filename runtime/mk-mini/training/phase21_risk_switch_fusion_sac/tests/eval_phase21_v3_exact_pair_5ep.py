#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import random
import zlib
from pathlib import Path
from typing import Any

import numpy as np
import torch
from stable_baselines3 import SAC

from training.phase21_risk_switch_fusion_sac.envs.mkmini_phase21_risk_switch_fusion_sac_env import (
    MkMiniPhase21RiskSwitchFusionSACEnv,
)


ROOT = Path.home() / "catkin_ws/src/mk-mini"

MODEL_PATH = (
    ROOT
    / "training/phase20_unknown_obstacle_adaptation"
    / "checkpoints/stage_b_randomized"
    / "phase20_stage_b_325000_steps.zip"
)

OUTPUT_PATH = (
    ROOT
    / "training/phase21_risk_switch_fusion_sac"
    / "results/exact_pair_5ep"
    / "phase21_v3_exact_pair_5ep.json"
)

SEEDS = list(range(22100, 22105))
MAX_STEPS = 600


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def walk_objects(root):
    queue = [("root", root)]
    seen = set()

    while queue:
        path, obj = queue.pop(0)

        if obj is None or id(obj) in seen:
            continue

        seen.add(id(obj))
        yield path, obj

        for name in (
            "inner",
            "env",
            "base_env",
            "unwrapped",
        ):
            try:
                child = getattr(obj, name, None)
            except Exception:
                child = None

            if (
                child is not None
                and child is not obj
            ):
                queue.append(
                    (f"{path}.{name}", child)
                )


def synchronize_rngs(
    env,
    seed: int,
) -> None:
    """
    将两组环境中所有已存在的随机数生成器设置为相同状态。
    """

    for object_path, obj in walk_objects(env):
        try:
            attributes = list(
                obj.__dict__.items()
            )
        except Exception:
            continue

        for name, value in attributes:
            if "rng" not in name.lower():
                continue

            token = (
                f"{object_path}.{name}"
            ).encode("utf-8")

            offset = zlib.crc32(token)

            local_seed = int(
                (
                    int(seed) * 1009
                    + int(offset)
                )
                % (2**32 - 1)
            )

            try:
                if isinstance(
                    value,
                    np.random.Generator,
                ):
                    setattr(
                        obj,
                        name,
                        np.random.default_rng(
                            local_seed
                        ),
                    )

                elif isinstance(
                    value,
                    np.random.RandomState,
                ):
                    setattr(
                        obj,
                        name,
                        np.random.RandomState(
                            local_seed
                        ),
                    )
            except Exception:
                pass


def array_hash(value) -> str:
    try:
        array = np.asarray(
            value,
            dtype=np.float32,
        )
    except Exception:
        return "UNAVAILABLE"

    array = np.ascontiguousarray(array)

    return hashlib.sha256(
        array.tobytes()
    ).hexdigest()


def rounded_vector(value) -> list[float]:
    try:
        array = np.asarray(
            value,
            dtype=np.float64,
        ).reshape(-1)

        return [
            round(float(item), 7)
            for item in array
        ]
    except Exception:
        return []


def make_env(
    seed: int,
    enable_detour: bool,
):
    seed_all(seed)

    env = MkMiniPhase21RiskSwitchFusionSACEnv(
        randomized=True,
        random_seed=seed,
        terminate_on_collision=True,
        penetration_margin=0.02,
        safe_clearance=0.35,
        phase21_v3_enable_detour=enable_detour,
    )

    # 控制参数保持固定，只随机化场景和未知障碍。
    if hasattr(
        env,
        "phase17_enable_domain_randomization",
    ):
        env.phase17_enable_domain_randomization = False

    synchronize_rngs(
        env,
        seed,
    )

    return env


def reset_env(
    env,
    seed: int,
):
    seed_all(seed)
    synchronize_rngs(env, seed)

    output = env.reset(seed=seed)

    if (
        isinstance(output, tuple)
        and len(output) == 2
    ):
        observation, info = output
    else:
        observation = output
        info = {}

    observation = np.asarray(
        observation,
        dtype=np.float32,
    )

    if observation.shape != (186,):
        raise RuntimeError(
            f"观察维度异常：{observation.shape}"
        )

    return observation, dict(info or {})


def scenario_signature(env) -> dict[str, Any]:
    config = dict(
        getattr(
            env,
            "phase20_last_config",
            {},
        )
    )

    original_path = getattr(
        env,
        "phase21_v3_original_path",
        None,
    )

    return {
        "unknown_radius": round(
            float(
                config.get(
                    "unknown_radius",
                    float("nan"),
                )
            ),
            7,
        ),
        "unknown_lateral_offset": round(
            float(
                config.get(
                    "unknown_lateral_offset",
                    float("nan"),
                )
            ),
            7,
        ),
        "unknown_path_fraction": round(
            float(
                config.get(
                    "unknown_path_fraction",
                    float("nan"),
                )
            ),
            7,
        ),
        "endpoint_clearance": round(
            float(
                config.get(
                    "endpoint_clearance",
                    float("nan"),
                )
            ),
            7,
        ),
        "robot_xy": rounded_vector(
            getattr(
                env,
                "robot_xy",
                [],
            )
        ),
        "goal_xy": rounded_vector(
            getattr(
                env,
                "goal_xy",
                [],
            )
        ),
        "rect_hash": array_hash(
            getattr(
                env,
                "rect_obstacles",
                [],
            )
        ),
        "circle_hash": array_hash(
            getattr(
                env,
                "circle_obstacles",
                [],
            )
        ),
        "unknown_hash": array_hash(
            getattr(
                env,
                "phase19_unknown_circles",
                [],
            )
        ),
        "original_path_hash": array_hash(
            original_path
        ),
    }


def flag(
    info: dict[str, Any],
    names: tuple[str, ...],
) -> bool:
    for name in names:
        if name not in info:
            continue

        try:
            values = np.asarray(
                info[name]
            ).reshape(-1)

            if any(bool(value) for value in values):
                return True
        except Exception:
            continue

    return False


def rollout(
    env,
    observation: np.ndarray,
    reset_info: dict[str, Any],
    model: SAC,
) -> dict[str, Any]:
    total_reward = 0.0
    minimum_clearance = float("inf")
    success = False
    collision = False
    done = False
    final_info = dict(reset_info)

    for step in range(1, MAX_STEPS + 1):
        action, _ = model.predict(
            observation,
            deterministic=True,
        )

        output = env.step(action)

        if len(output) == 5:
            (
                observation,
                reward,
                terminated,
                truncated,
                info,
            ) = output

            done = bool(
                terminated or truncated
            )
        else:
            (
                observation,
                reward,
                done,
                info,
            ) = output

            done = bool(done)

        observation = np.asarray(
            observation,
            dtype=np.float32,
        )

        final_info = dict(info or {})
        total_reward += float(reward)

        try:
            clearance = float(
                final_info.get(
                    "phase20_unknown_clearance",
                    float("inf"),
                )
            )

            if math.isfinite(clearance):
                minimum_clearance = min(
                    minimum_clearance,
                    clearance,
                )
        except Exception:
            pass

        success = (
            success
            or flag(
                final_info,
                (
                    "reach_goal",
                    "success",
                    "is_success",
                    "goal_reached",
                ),
            )
        )

        collision = (
            collision
            or flag(
                final_info,
                (
                    "phase20_collision",
                    "collision",
                ),
            )
        )

        if done:
            break

    return {
        "steps": int(step),
        "done": bool(done),
        "success": bool(success),
        "collision": bool(collision),
        "timeout": bool(
            not success
            and not collision
            and step >= MAX_STEPS
        ),
        "total_reward": float(total_reward),
        "min_unknown_clearance": float(
            minimum_clearance
        ),
        "detour_enabled": bool(
            final_info.get(
                "phase21_v3_enable_detour",
                False,
            )
        ),
        "detour_applied": bool(
            final_info.get(
                "phase21_v3_detour_applied",
                False,
            )
        ),
        "chosen_side": str(
            final_info.get(
                "phase21_v3_chosen_side",
                "NONE",
            )
        ),
        "trigger_risk": float(
            final_info.get(
                "phase21_v3_trigger_risk",
                0.0,
            )
        ),
        "failure_reason": str(
            final_info.get(
                "phase21_v3_failure_reason",
                "none",
            )
        ),
        "ground_truth_used_for_control": bool(
            final_info.get(
                "phase21_ground_truth_used_for_control",
                False,
            )
        ),
    }


def main() -> None:
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(MODEL_PATH)

    model = SAC.load(
        str(MODEL_PATH),
        device="cpu",
    )

    pairs = []

    for index, seed in enumerate(
        SEEDS,
        start=1,
    ):
        print(
            f"\n[{index}/{len(SEEDS)}] seed={seed}",
            flush=True,
        )

        baseline_env = make_env(
            seed,
            enable_detour=False,
        )

        method_env = make_env(
            seed,
            enable_detour=True,
        )

        try:
            (
                baseline_obs,
                baseline_reset_info,
            ) = reset_env(
                baseline_env,
                seed,
            )

            baseline_signature = (
                scenario_signature(
                    baseline_env
                )
            )

            (
                method_obs,
                method_reset_info,
            ) = reset_env(
                method_env,
                seed,
            )

            method_signature = (
                scenario_signature(
                    method_env
                )
            )

            same_scenario = bool(
                baseline_signature
                == method_signature
            )

            if not same_scenario:
                mismatch = {
                    key: {
                        "baseline":
                            baseline_signature.get(
                                key
                            ),
                        "method":
                            method_signature.get(
                                key
                            ),
                    }
                    for key in baseline_signature
                    if (
                        baseline_signature.get(key)
                        != method_signature.get(key)
                    )
                }

                raise RuntimeError(
                    "严格配对失败："
                    f"seed={seed}\n"
                    + json.dumps(
                        mismatch,
                        ensure_ascii=False,
                        indent=2,
                    )
                )

            baseline_result = rollout(
                baseline_env,
                baseline_obs,
                baseline_reset_info,
                model,
            )

            method_result = rollout(
                method_env,
                method_obs,
                method_reset_info,
                model,
            )

        finally:
            baseline_env.close()
            method_env.close()

        pair = {
            "seed": seed,
            "same_scenario": True,
            "scenario_signature":
                baseline_signature,
            "baseline": baseline_result,
            "method": method_result,
            "collision_avoided": bool(
                baseline_result["collision"]
                and not method_result["collision"]
            ),
            "new_collision": bool(
                not baseline_result["collision"]
                and method_result["collision"]
            ),
            "success_improved": bool(
                not baseline_result["success"]
                and method_result["success"]
            ),
            "success_regressed": bool(
                baseline_result["success"]
                and not method_result["success"]
            ),
        }

        pairs.append(pair)

        print(
            "  OFF:",
            f"success={baseline_result['success']}",
            f"collision={baseline_result['collision']}",
            f"steps={baseline_result['steps']}",
            flush=True,
        )

        print(
            "  ON :",
            f"success={method_result['success']}",
            f"collision={method_result['collision']}",
            f"steps={method_result['steps']}",
            f"detour={method_result['detour_applied']}",
            f"side={method_result['chosen_side']}",
            flush=True,
        )

    summary = {
        "episodes": len(pairs),
        "same_scenario_count": sum(
            int(pair["same_scenario"])
            for pair in pairs
        ),
        "baseline_success_count": sum(
            int(pair["baseline"]["success"])
            for pair in pairs
        ),
        "baseline_collision_count": sum(
            int(pair["baseline"]["collision"])
            for pair in pairs
        ),
        "method_success_count": sum(
            int(pair["method"]["success"])
            for pair in pairs
        ),
        "method_collision_count": sum(
            int(pair["method"]["collision"])
            for pair in pairs
        ),
        "collision_avoided_count": sum(
            int(pair["collision_avoided"])
            for pair in pairs
        ),
        "new_collision_count": sum(
            int(pair["new_collision"])
            for pair in pairs
        ),
        "success_improved_count": sum(
            int(pair["success_improved"])
            for pair in pairs
        ),
        "success_regressed_count": sum(
            int(pair["success_regressed"])
            for pair in pairs
        ),
    }

    payload = {
        "seeds": SEEDS,
        "comparison": {
            "baseline":
                "same_phase21_stack_detour_off",
            "method":
                "same_phase21_stack_detour_on",
        },
        "summary": summary,
        "pairs": pairs,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 80)
    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    print(
        "PHASE21_V3_EXACT_PAIR_5EP_DONE"
    )

    print(
        "OUTPUT =",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()
