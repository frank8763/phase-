from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import random
import signal
import time
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import SAC

ROOT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()

MODEL = ROOT / "training/phase20_unknown_obstacle_adaptation/checkpoints/stage_b_randomized/phase20_stage_b_325000_steps.zip"
MODEL_SHA = "4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f"

EVAL_MOD = "training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep"

METHODS = {
    "dwa": (
        "envs.baselines.mkmini_ackermann_dwa_env",
        "MkMiniG4AckermannDWAEnv",
    ),
    "phase21_v11": (
        "envs.phase21.mkmini_phase21_v11_candidate_recovery_env",
        "MkMiniPhase21V11CandidateRecoveryEnv",
    ),
    "phase22_v1": (
        "envs.phase22.mkmini_phase22_v1_continuous_corridor_env",
        "MkMiniPhase22V1ContinuousCorridorEnv",
    ),
}

METHOD_WALL_S = 120.0
MAX_STEPS = 600


class MethodWallTimeout(Exception):
    pass


def alarm_handler(signum, frame):
    raise MethodWallTimeout("METHOD_WALL_TIMEOUT")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def safe(v):
    if isinstance(v, np.ndarray):
        return v.tolist()
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, dict):
        return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    return repr(v)


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed & 0xFFFFFFFF)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def method_metrics(env, method: str):
    attrs = {}
    if method == "dwa":
        names = (
            "g4_dwa_attempt_count",
            "g4_dwa_success_count",
            "g4_dwa_failure_count",
            "g4_dwa_candidate_count",
            "g4_dwa_feasible_count",
            "g4_dwa_plan_time_total_s",
            "g4_dwa_plan_time_max_s",
            "g4_dwa_last_failure_reason",
            "g4_dwa_gt_obstacle_used_for_control",
        )
    elif method == "phase21_v11":
        names = (
            "phase21_v3_apply_count",
            "phase21_v4_attempt_count",
            "phase21_v4_feasible_count",
            "phase21_v4_failed_attempt_count",
            "phase21_v11_recovery_attempt_count",
            "phase21_v11_recovery_success_count",
            "phase21_v11_recovery_candidate_count",
            "phase21_v11_recovery_feasible_count",
        )
    else:
        names = (
            "phase21_v3_apply_count",
            "phase21_v4_attempt_count",
            "phase21_v4_feasible_count",
            "phase21_v4_failed_attempt_count",
            "phase21_v11_recovery_attempt_count",
            "phase21_v11_recovery_success_count",
            "phase22_v1_attempted",
            "phase22_v1_success",
            "phase22_v1_candidate_count",
            "phase22_v1_failure_reason",
            "phase22_v1_selected_known_margin",
            "phase22_v1_selected_sensor_margin",
            "phase22_v1_selected_p95_curvature",
            "phase22_v1_selected_heading_delta",
            "phase22_v1_reverse_count",
        )
    for name in names:
        if hasattr(env, name):
            try:
                attrs[name] = safe(getattr(env, name))
            except Exception:
                pass
    return attrs


def normalize_result(result, wall_s: float):
    r = dict(result or {})
    success = bool(r.get("success", False))
    collision = bool(r.get("collision", False))
    env_timeout = bool(r.get("timeout", False))
    safe_success = bool(success and not collision)
    if collision:
        final_class = "COLLISION"
    elif safe_success:
        final_class = "SAFE_SUCCESS"
    elif env_timeout:
        final_class = "ENV_TIMEOUT"
    else:
        final_class = "OTHER_FAILURE"
    r.update(
        {
            "success": success,
            "collision": collision,
            "safe_success": safe_success,
            "env_timeout": env_timeout,
            "wall_timeout": False,
            "wall_seconds": float(wall_s),
            "final_class": final_class,
        }
    )
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--method", choices=sorted(METHODS), required=True)
    ap.add_argument("--frozen-dwa-config", required=True)
    ap.add_argument("--started-json", required=True)
    ap.add_argument("--result-json", required=True)
    args = ap.parse_args()

    if not (26200 <= args.seed <= 26299):
        raise SystemExit("SEED_OUTSIDE_G4C_FORMAL_RANGE")

    if sha256(MODEL) != MODEL_SHA:
        raise SystemExit("MODEL_SHA_MISMATCH")

    E = importlib.import_module(EVAL_MOD)
    if int(getattr(E, "MAX_STEPS", MAX_STEPS)) != MAX_STEPS:
        raise SystemExit("MAX_STEPS_PROTOCOL_MISMATCH")

    modname, clsname = METHODS[args.method]
    Env = getattr(importlib.import_module(modname), clsname)

    kwargs = dict(
        randomized=True,
        random_seed=args.seed,
        terminate_on_collision=True,
        penetration_margin=0.02,
        safe_clearance=0.35,
    )
    if args.method == "dwa":
        cfg = json.loads(
            Path(args.frozen_dwa_config).read_text(encoding="utf-8")
        )
        kwargs["g4_dwa_config"] = cfg

    seed_all(args.seed)
    env = Env(**kwargs)
    if hasattr(env, "phase17_enable_domain_randomization"):
        env.phase17_enable_domain_randomization = False

    try:
        E.synchronize_rngs(env, args.seed)
        obs, info = E.reset_env(env, args.seed)
        obs = np.asarray(obs, dtype=np.float32)
        if obs.shape != (186,):
            raise RuntimeError(f"OBS_SHAPE={obs.shape}")

        signature = safe(E.scenario_signature(env))
        started = {
            "seed": int(args.seed),
            "method": args.method,
            "scenario_signature": signature,
            "model_sha256": MODEL_SHA,
            "started_wall_time": time.time(),
            "no_rollout_before_signature_write": True,
        }
        Path(args.started_json).write_text(
            json.dumps(started, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        model = SAC.load(str(MODEL), device="cpu")

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(int(METHOD_WALL_S))
        t0 = time.perf_counter()
        try:
            raw = E.rollout(env, obs, dict(info or {}), model)
            wall = float(time.perf_counter() - t0)
            # Enforce the preregistered 120 s wall even if a native call
            # delays Python signal delivery.
            if wall >= METHOD_WALL_S:
                row = {
                    "success": False,
                    "collision": False,
                    "safe_success": False,
                    "env_timeout": False,
                    "wall_timeout": True,
                    "wall_seconds": wall,
                    "final_class": "WALL_TIMEOUT",
                }
            else:
                row = normalize_result(raw, wall)
        except MethodWallTimeout:
            wall = float(time.perf_counter() - t0)
            row = {
                "success": False,
                "collision": False,
                "safe_success": False,
                "env_timeout": False,
                "wall_timeout": True,
                "wall_seconds": wall,
                "final_class": "WALL_TIMEOUT",
            }
        finally:
            signal.alarm(0)

        row.update(
            {
                "seed": int(args.seed),
                "method": args.method,
                "scenario_signature": signature,
                "method_metrics": method_metrics(env, args.method),
            }
        )

        if args.method == "dwa":
            if bool(
                row["method_metrics"].get(
                    "g4_dwa_gt_obstacle_used_for_control",
                    False,
                )
            ):
                raise RuntimeError("DWA_GT_CONTROL_RUNTIME_LEAK")

        Path(args.result_json).write_text(
            json.dumps(safe(row), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(
            f"G4C_METHOD_RESULT seed={args.seed} "
            f"method={args.method} class={row['final_class']} "
            f"wall={row['wall_seconds']:.3f}",
            flush=True,
        )
    finally:
        try:
            env.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
