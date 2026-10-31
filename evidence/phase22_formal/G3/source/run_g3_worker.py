
from __future__ import annotations

import argparse
import hashlib
import inspect
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

from envs.phase21.mkmini_phase21_v11_candidate_recovery_env import (
    MkMiniPhase21V11CandidateRecoveryEnv,
)
from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import (
    MkMiniPhase22V1ContinuousCorridorEnv,
)
from training.phase21_risk_switch_fusion_sac.tests import (
    eval_phase21_v3_exact_pair_5ep as E,
)

ROOT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()
EXP = ROOT / "experiments/phase_paper_stageG3_multiscene_80_v1"
RESULTS = EXP / "results"
MANIFEST = RESULTS / "g3_manifest.json"

MODEL = ROOT / (
    "training/phase20_unknown_obstacle_adaptation/checkpoints/"
    "stage_b_randomized/phase20_stage_b_325000_steps.zip"
)
MODEL_SHA = "4072c19e02ba5c7c6b218a268c4ff1d987d2352eada01a3de918854d7173fc9f"

METHOD_WALL = 120
MAX_STEPS = 600


class WallTimeout(Exception):
    pass


def alarm_handler(signum, frame):
    raise WallTimeout()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def safe(obj):
    if isinstance(obj, dict):
        return {str(k): safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        x = float(obj)
        return x if math.isfinite(x) else str(x)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed & 0xFFFFFFFF)
    torch.manual_seed(seed)


def prepare(cls, seed):
    seed_all(seed)
    env = cls(
        randomized=True,
        random_seed=seed,
        terminate_on_collision=True,
        penetration_margin=0.02,
        safe_clearance=0.35,
    )
    if hasattr(env, "phase17_enable_domain_randomization"):
        env.phase17_enable_domain_randomization = False
    E.synchronize_rngs(env, seed)
    obs, info = E.reset_env(env, seed)
    obs = np.asarray(obs, dtype=np.float32)
    if obs.shape != (186,):
        raise RuntimeError(f"OBS_SHAPE={obs.shape}")
    sig = safe(E.scenario_signature(env))
    return env, obs, dict(info or {}), sig


def normalize(result, wall):
    r = dict(result or {})
    success = bool(r.get("success", False))
    collision = bool(r.get("collision", False))
    timeout = bool(r.get("timeout", False))
    r = safe(r)
    r.update(
        {
            "success": success,
            "collision": collision,
            "env_timeout": timeout,
            "wall_timeout": False,
            "safe_success": bool(success and not collision),
            "wall_seconds": float(wall),
        }
    )
    if collision:
        cls = "COLLISION"
    elif success:
        cls = "SAFE_SUCCESS"
    elif timeout:
        cls = "ENV_TIMEOUT"
    else:
        cls = "OTHER_FAILURE"
    r["final_class"] = cls
    return r


def run_method(env, obs, info, model):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(METHOD_WALL)
    t0 = time.perf_counter()
    try:
        row = normalize(
            E.rollout(env, obs, info, model),
            time.perf_counter() - t0,
        )
    except WallTimeout:
        row = {
            "success": False,
            "collision": False,
            "env_timeout": False,
            "wall_timeout": True,
            "safe_success": False,
            "wall_seconds": time.perf_counter() - t0,
            "final_class": "WALL_TIMEOUT",
        }
    finally:
        signal.alarm(0)
    return row


def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(safe(obj), ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done(path):
    done = set()
    if not path.exists():
        return done
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            done.add(int(r["seed"]))
        except Exception:
            pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--num-shards", type=int, default=4)
    args = ap.parse_args()

    if args.shard < 0 or args.shard >= args.num_shards:
        raise SystemExit("BAD_SHARD")
    if sha256_file(MODEL) != MODEL_SHA:
        raise SystemExit("MODEL_SHA_MISMATCH")
    if not MANIFEST.exists():
        raise SystemExit("G3_MANIFEST_MISSING")

    # Verify exact rollout still contains collision-adjudication evidence.
    src = inspect.getsource(E.rollout).lower()
    evidence = [
        x
        for x in (
            "collision",
            "robot_obstacle_contact",
            "check_map_penetration",
            "robot_sample_points",
            "map_penetration",
        )
        if x in src
    ]
    if not evidence:
        raise SystemExit("COLLISION_PROTOCOL_EVIDENCE_MISSING")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    selected = manifest["selected"]
    work = [
        r
        for i, r in enumerate(selected)
        if i % args.num_shards == args.shard
    ]

    out = RESULTS / f"worker_{args.shard}.jsonl"
    done = load_done(out)

    model = SAC.load(str(MODEL), device="cpu")

    print(
        f"G3_WORKER_START shard={args.shard} "
        f"pairs={len(work)} resume_done={len(done)}",
        flush=True,
    )

    for ix, item in enumerate(work, 1):
        seed = int(item["seed"])
        if seed in done:
            continue

        b_env = p_env = None
        try:
            b_env, b_obs, b_info, b_sig = prepare(
                MkMiniPhase21V11CandidateRecoveryEnv,
                seed,
            )
            p_env, p_obs, p_info, p_sig = prepare(
                MkMiniPhase22V1ContinuousCorridorEnv,
                seed,
            )

            if b_sig != p_sig:
                raise RuntimeError(
                    f"SCENARIO_MISMATCH seed={seed}"
                )
            if b_sig != item["scenario_signature"]:
                raise RuntimeError(
                    f"MANIFEST_SCENARIO_MISMATCH seed={seed}"
                )

            baseline = run_method(
                b_env, b_obs, b_info, model
            )
            proposed = run_method(
                p_env, p_obs, p_info, model
            )

            # Telemetry for paper analysis only.
            proposed.update(
                {
                    "phase22_attempted": bool(
                        getattr(p_env, "phase22_v1_attempted", False)
                    ),
                    "phase22_corridor_success": bool(
                        getattr(p_env, "phase22_v1_success", False)
                    ),
                    "phase22_candidate_count": int(
                        getattr(p_env, "phase22_v1_candidate_count", 0)
                    ),
                    "phase22_failure_reason": str(
                        getattr(p_env, "phase22_v1_failure_reason", "none")
                    ),
                    "phase22_known_margin": float(
                        getattr(
                            p_env,
                            "phase22_v1_selected_known_margin",
                            float("nan"),
                        )
                    ),
                    "phase22_sensor_margin": float(
                        getattr(
                            p_env,
                            "phase22_v1_selected_sensor_margin",
                            float("nan"),
                        )
                    ),
                }
            )

            row = {
                "seed": seed,
                "family": item["family"],
                "known_map_hash": item["known_map_hash"],
                "geometry_metrics": item["metrics"],
                "scenario_signature": b_sig,
                "same_scenario": True,
                "baseline": baseline,
                "proposed": proposed,
            }

            # No privileged-control contamination is allowed.
            for name, method in (
                ("baseline", baseline),
                ("proposed", proposed),
            ):
                if bool(method.get("ground_truth_used_for_control", False)):
                    raise RuntimeError(
                        f"GROUND_TRUTH_CONTROL_VIOLATION {seed} {name}"
                    )

            append_jsonl(out, row)
            print(
                f"[{args.shard}] {ix}/{len(work)} "
                f"seed={seed} family={item['family']} "
                f"B={baseline['final_class']} "
                f"P={proposed['final_class']} "
                f"wall={baseline['wall_seconds']:.1f}/{proposed['wall_seconds']:.1f}",
                flush=True,
            )
        finally:
            for env in (b_env, p_env):
                if env is not None:
                    try:
                        env.close()
                    except Exception:
                        pass

    print(f"G3_WORKER_{args.shard}=PASS", flush=True)


if __name__ == "__main__":
    main()
