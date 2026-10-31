#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import math
import os
import statistics
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path.cwd().resolve()
OUT_ROOT = (
    ROOT
    / "training/phase21_risk_switch_fusion_sac/results/"
      "phase_final_holdout_300_v1_1"
)
PROTECTED_MANIFEST = OUT_ROOT / "protected_before.sha256"

MODEL_PATH = (
    ROOT
    / "training/phase20_unknown_obstacle_adaptation/checkpoints/"
      "stage_b_randomized/phase20_stage_b_325000_steps.zip"
)

METHODS = {
    "phase21_v11": (
        "envs.phase21.mkmini_phase21_v11_candidate_recovery_env",
        "MkMiniPhase21V11CandidateRecoveryEnv",
    ),
    "phase22_v1": (
        "envs.phase22.mkmini_phase22_v1_continuous_corridor_env",
        "MkMiniPhase22V1ContinuousCorridorEnv",
    ),
}

PREFLIGHT_SEEDS = [22751]
FORMAL_SEEDS = list(range(22800, 23100))
PER_ROLLOUT_TIMEOUT_S = 120.0

def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT))
    except Exception:
        return str(p)

def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        out[name.strip()] = digest.strip()
    return out

def verify_protected() -> None:
    if not PROTECTED_MANIFEST.exists():
        raise RuntimeError("PROTECTED_MANIFEST_MISSING")
    for name, expected in parse_manifest(PROTECTED_MANIFEST).items():
        p = ROOT / name
        if not p.exists():
            raise RuntimeError(f"PROTECTED_FILE_MISSING:{name}")
        actual = file_sha256(p)
        if actual != expected:
            raise RuntimeError(
                f"PROTECTED_HASH_MISMATCH:{name}:{expected}:{actual}"
            )

def as_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, dict):
        for key in (
            "penetration", "collision", "collision_any",
            "map_penetration", "contact",
        ):
            if key in value:
                return as_bool(value[key])
        return False
    if isinstance(value, (tuple, list)):
        if not value:
            return False
        # Existing helpers place the main penetration flag first.
        return as_bool(value[0])
    if isinstance(value, np.ndarray):
        if value.size == 1:
            return bool(value.reshape(-1)[0])
        return False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return bool(value)
    return False

def safe_float(value: Any) -> float | None:
    try:
        x = float(value)
    except Exception:
        return None
    return x if math.isfinite(x) else None

class StrictTracker:
    def __init__(self):
        self.steps = 0
        self.strict_collision = False
        self.strict_collision_step = None
        self.robot_contact_any = False
        self.map_penetration_any = False
        self.info_collision_any = False
        self.unknown_penetration_any = False
        self.known_penetration_any = False
        self.sample_points_min_count = None
        self.sample_points_max_count = None
        self.minimum_clearance = float("inf")
        self.replan_info_max = 0
        self.rejoin_info_max = 0

    def update_info(self, info: dict[str, Any]):
        for key in (
            "collision", "collision_any", "contact_collision",
            "penetration", "map_penetration",
        ):
            if as_bool(info.get(key, False)):
                self.info_collision_any = True

        for key in (
            "phase20_unknown_penetration",
            "unknown_penetration",
            "phase19_unknown_contact",
            "unknown_contact",
        ):
            if as_bool(info.get(key, False)):
                self.unknown_penetration_any = True

        for key in (
            "phase20_known_penetration",
            "known_penetration",
        ):
            if as_bool(info.get(key, False)):
                self.known_penetration_any = True

        for key in (
            "minimum_clearance", "phase21_minimum_clearance",
            "min_clearance",
        ):
            x = safe_float(info.get(key))
            if x is not None:
                self.minimum_clearance = min(self.minimum_clearance, x)

        for key, value in info.items():
            lk = str(key).lower()
            if "replan" in lk and isinstance(value, (int, np.integer)):
                self.replan_info_max = max(self.replan_info_max, int(value))
            if "rejoin" in lk and isinstance(value, (int, np.integer)):
                self.rejoin_info_max = max(self.rejoin_info_max, int(value))

def install_strict_step(env, tracker: StrictTracker):
    from training.phase18_ablation.scripts.eval_phase18_A_full_fixed_seed import (
        robot_obstacle_contact,
        robot_sample_points,
        check_map_penetration,
    )

    original_step = env.step

    def strict_step(action):
        out = original_step(action)
        tracker.steps += 1

        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            info = dict(info or {})
        elif len(out) == 4:
            obs, reward, done, info = out
            terminated = bool(done)
            truncated = False
            info = dict(info or {})
        else:
            raise RuntimeError(f"UNSUPPORTED_STEP_TUPLE_LEN:{len(out)}")

        # Explicitly call all three formal collision components.
        pts = np.asarray(robot_sample_points(env))
        n_pts = int(len(pts)) if pts.ndim >= 1 else int(pts.size)
        if tracker.sample_points_min_count is None:
            tracker.sample_points_min_count = n_pts
            tracker.sample_points_max_count = n_pts
        else:
            tracker.sample_points_min_count = min(tracker.sample_points_min_count, n_pts)
            tracker.sample_points_max_count = max(tracker.sample_points_max_count, n_pts)

        contact = as_bool(robot_obstacle_contact(env))
        try:
            penetration_raw = check_map_penetration(env, margin=0.02)
        except TypeError:
            penetration_raw = check_map_penetration(env)
        penetration = as_bool(penetration_raw)

        tracker.robot_contact_any |= contact
        tracker.map_penetration_any |= penetration
        tracker.update_info(info)

        strict_collision_now = bool(
            contact
            or penetration
            or tracker.info_collision_any
        )

        if strict_collision_now:
            tracker.strict_collision = True
            if tracker.strict_collision_step is None:
                tracker.strict_collision_step = tracker.steps

        info["robot_obstacle_contact"] = bool(
            as_bool(info.get("robot_obstacle_contact", False))
            or contact
        )
        info["map_penetration"] = bool(
            as_bool(info.get("map_penetration", False))
            or penetration
        )
        info["collision"] = bool(
            as_bool(info.get("collision", False))
            or strict_collision_now
        )
        info["collision_any"] = bool(
            as_bool(info.get("collision_any", False))
            or strict_collision_now
        )

        if strict_collision_now:
            terminated = True

        if len(out) == 5:
            return obs, reward, bool(terminated), bool(truncated), info
        return obs, reward, bool(terminated or truncated), info

    env.step = strict_step

def install_planner_timing(env):
    times: list[float] = []
    hook_name = None
    for name in (
        "_phase21_v3_build_detour",
        "_phase21_v8_replan",
    ):
        fn = getattr(env, name, None)
        if callable(fn):
            hook_name = name
            original = fn

            def timed(*args, __orig=original, **kwargs):
                t0 = time.perf_counter()
                try:
                    return __orig(*args, **kwargs)
                finally:
                    times.append(float(time.perf_counter() - t0))

            setattr(env, name, timed)
            break
    return hook_name, times

def scalar_runtime_attrs(env) -> dict[str, Any]:
    wanted = (
        "replan", "rejoin", "detour", "corridor",
        "candidate", "recovery", "attempt", "success_count",
        "failure_count",
    )
    out = {}
    for name in dir(env):
        if name.startswith("__"):
            continue
        low = name.lower()
        if not any(token in low for token in wanted):
            continue
        try:
            value = getattr(env, name)
        except Exception:
            continue
        if isinstance(value, (bool, str, int, float, np.integer, np.floating)):
            if isinstance(value, (np.integer, np.floating)):
                value = value.item()
            if isinstance(value, float) and not math.isfinite(value):
                value = None
            out[name] = value
    return out

def instantiate(method: str):
    module_name, class_name = METHODS[method]
    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name)

    import training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep as evaluator
    max_steps = int(getattr(evaluator, "MAX_STEPS", 300))

    errors = []
    for kwargs in ({"max_steps": max_steps}, {}):
        try:
            return cls(**kwargs)
        except TypeError as exc:
            errors.append(f"{kwargs}:{exc}")
    raise RuntimeError("ENV_INIT_FAILED:" + " | ".join(errors))


def smoke_worker(method: str, seed: int, out_path: Path, smoke_steps: int = 5) -> int:
    """
    Harness-only preflight.
    It intentionally DOES NOT run a complete episode and DOES NOT judge navigation
    performance. It only verifies that the frozen method can be instantiated/reset,
    produces the same paired scenario signature, can execute a few policy steps,
    and that the strict collision helpers are callable.
    """
    from stable_baselines3 import SAC
    import training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep as evaluator

    env = None
    row: dict[str, Any] = {
        "method": method,
        "seed": int(seed),
        "model_sha256": file_sha256(MODEL_PATH),
        "smoke_steps_requested": int(smoke_steps),
        "preflight_semantics": "HARNESS_ONLY_SHORT_ROLLOUT_NOT_PERFORMANCE_GATE",
    }
    try:
        env = instantiate(method)
        tracker = StrictTracker()
        hook_name, planner_times = install_planner_timing(env)
        install_strict_step(env, tracker)

        model = SAC.load(str(MODEL_PATH), device="cpu")
        observation, reset_info = evaluator.reset_env(env, int(seed))
        signature = evaluator.scenario_signature(env)

        total_reward = 0.0
        t0 = time.perf_counter()
        terminated_early = False

        for _ in range(max(1, int(smoke_steps))):
            action, _ = model.predict(observation, deterministic=True)
            output = env.step(action)

            if len(output) == 5:
                observation, reward, terminated, truncated, info = output
                done = bool(terminated or truncated)
            elif len(output) == 4:
                observation, reward, done, info = output
                done = bool(done)
            else:
                raise RuntimeError(f"UNSUPPORTED_STEP_TUPLE_LEN:{len(output)}")

            observation = np.asarray(observation, dtype=np.float32)
            total_reward += float(reward)

            if done:
                terminated_early = True
                break

        elapsed = float(time.perf_counter() - t0)

        arr = np.asarray(planner_times, dtype=np.float64)
        row.update({
            "scenario_signature": signature,
            "smoke_steps_executed": int(tracker.steps),
            "terminated_early": bool(terminated_early),
            "strict_collision_seen": bool(tracker.strict_collision),
            "sample_points_min_count": tracker.sample_points_min_count,
            "sample_points_max_count": tracker.sample_points_max_count,
            "planner_hook": hook_name,
            "planner_call_count": len(planner_times),
            "planner_p95_seconds": (
                float(np.percentile(arr, 95.0)) if arr.size else None
            ),
            "smoke_elapsed_seconds": elapsed,
            "total_reward": total_reward,
        })

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["traceback"] = traceback.format_exc()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return 2
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass

def worker(method: str, seed: int, out_path: Path) -> int:
    from stable_baselines3 import SAC
    import training.phase21_risk_switch_fusion_sac.tests.eval_phase21_v3_exact_pair_5ep as evaluator

    env = None
    row: dict[str, Any] = {
        "method": method,
        "seed": int(seed),
        "model_sha256": file_sha256(MODEL_PATH),
    }
    try:
        env = instantiate(method)
        tracker = StrictTracker()
        hook_name, planner_times = install_planner_timing(env)
        install_strict_step(env, tracker)

        model = SAC.load(str(MODEL_PATH), device="cpu")
        observation, reset_info = evaluator.reset_env(env, int(seed))
        signature = evaluator.scenario_signature(env)

        t0 = time.perf_counter()
        result = evaluator.rollout(
            env,
            observation,
            reset_info,
            model,
        )
        elapsed = float(time.perf_counter() - t0)

        collision = bool(
            as_bool(result.get("collision", False))
            or tracker.strict_collision
        )
        success_raw = bool(result.get("success", False))
        safe_success = bool(success_raw and not collision)

        arr = np.asarray(planner_times, dtype=np.float64)
        if arr.size:
            planner_mean = float(np.mean(arr))
            planner_p95 = float(np.percentile(arr, 95.0))
            planner_max = float(np.max(arr))
        else:
            planner_mean = planner_p95 = planner_max = float("nan")

        row.update({
            "scenario_signature": signature,
            "success_raw": success_raw,
            "safe_success": safe_success,
            "collision": collision,
            "env_timeout": bool(result.get("timeout", False)),
            "steps": int(result.get("steps", tracker.steps) or tracker.steps),
            "total_reward": safe_float(result.get("total_reward")),
            "minimum_clearance": (
                tracker.minimum_clearance
                if math.isfinite(tracker.minimum_clearance)
                else safe_float(result.get("minimum_clearance"))
            ),
            "strict_collision_step": tracker.strict_collision_step,
            "robot_obstacle_contact": tracker.robot_contact_any,
            "map_penetration": tracker.map_penetration_any,
            "unknown_penetration": tracker.unknown_penetration_any,
            "known_penetration": tracker.known_penetration_any,
            "sample_points_min_count": tracker.sample_points_min_count,
            "sample_points_max_count": tracker.sample_points_max_count,
            "planner_hook": hook_name,
            "planner_call_count": len(planner_times),
            "planner_times_seconds": planner_times,
            "planner_mean_seconds": planner_mean,
            "planner_p95_seconds": planner_p95,
            "planner_max_seconds": planner_max,
            "rollout_elapsed_seconds": elapsed,
            "replan_info_max": tracker.replan_info_max,
            "rejoin_info_max": tracker.rejoin_info_max,
            "runtime_attrs": scalar_runtime_attrs(env),
        })

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["traceback"] = traceback.format_exc()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return 2
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass


def run_smoke_isolated(method: str, seed: int, out_path: Path, smoke_steps: int = 5) -> dict[str, Any]:
    cmd = [
        sys.executable, "-u", "-m",
        "training.phase21_risk_switch_fusion_sac.tests.phase_final_holdout_300_v1_1",
        "--mode", "smoke_worker",
        "--method", method,
        "--seed", str(seed),
        "--out", str(out_path),
        "--smoke-steps", str(int(smoke_steps)),
    ]

    t0 = time.perf_counter()
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60.0,
        )
        wall = float(time.perf_counter() - t0)
        if out_path.exists():
            row = json.loads(out_path.read_text(encoding="utf-8"))
        else:
            row = {
                "method": method,
                "seed": int(seed),
                "model_sha256": file_sha256(MODEL_PATH),
                "error": f"NO_SMOKE_RESULT_FILE_RC_{cp.returncode}",
            }
        row["worker_rc"] = int(cp.returncode)
        row["wall_seconds"] = wall
        row["worker_tail"] = (cp.stdout or "").splitlines()[-8:]
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return row
    except subprocess.TimeoutExpired as exc:
        wall = float(time.perf_counter() - t0)
        row = {
            "method": method,
            "seed": int(seed),
            "model_sha256": file_sha256(MODEL_PATH),
            "wall_timeout": True,
            "error": "SMOKE_HARD_WALL_TIMEOUT",
            "wall_seconds": wall,
            "worker_tail": (
                (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            ).splitlines()[-8:],
        }
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return row

def row_valid(path: Path, method: str, seed: int) -> bool:
    if not path.exists():
        return False
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    identity_ok = (
        row.get("method") == method
        and int(row.get("seed", -1)) == int(seed)
        and row.get("model_sha256") == file_sha256(MODEL_PATH)
    )
    if not identity_ok:
        return False

    # Normal completed row.
    if "error" not in row and not row.get("wall_timeout", False):
        return True

    # Resume-only fix: a first-observed formal 120 s hard wall timeout is itself
    # a valid confirmatory failure and must NOT be rerun after interruption.
    if (
        row.get("wall_timeout", False)
        and row.get("error") == "HARD_WALL_TIMEOUT"
        and isinstance(row.get("wall_seconds"), (int, float))
        and float(row.get("wall_seconds")) >= 119.0
    ):
        return True

    return False

def run_isolated(method: str, seed: int, out_path: Path) -> dict[str, Any]:
    if row_valid(out_path, method, seed):
        row = json.loads(out_path.read_text(encoding="utf-8"))
        row["resumed"] = True
        return row

    cmd = [
        sys.executable, "-u", "-m",
        "training.phase21_risk_switch_fusion_sac.tests.phase_final_holdout_300_v1_1",
        "--mode", "worker",
        "--method", method,
        "--seed", str(seed),
        "--out", str(out_path),
    ]

    t0 = time.perf_counter()
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=os.environ.copy(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=PER_ROLLOUT_TIMEOUT_S,
        )
        wall = float(time.perf_counter() - t0)
        if out_path.exists():
            row = json.loads(out_path.read_text(encoding="utf-8"))
        else:
            row = {
                "method": method,
                "seed": int(seed),
                "model_sha256": file_sha256(MODEL_PATH),
                "error": f"NO_WORKER_RESULT_FILE_RC_{cp.returncode}",
            }
        row["worker_rc"] = int(cp.returncode)
        row["wall_seconds"] = wall
        row["worker_tail"] = (cp.stdout or "").splitlines()[-8:]
        row["resumed"] = False
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2, allow_nan=True),
            encoding="utf-8",
        )
        return row
    except subprocess.TimeoutExpired as exc:
        wall = float(time.perf_counter() - t0)
        row = {
            "method": method,
            "seed": int(seed),
            "model_sha256": file_sha256(MODEL_PATH),
            "wall_timeout": True,
            "error": "HARD_WALL_TIMEOUT",
            "wall_seconds": wall,
            "worker_tail": (
                (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            ).splitlines()[-8:],
            "resumed": False,
        }
        out_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return row

def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n <= 0:
        return [None, None]
    p = k / n
    den = 1.0 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return [max(0.0, center-half), min(1.0, center+half)]

def exact_mcnemar_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    prob = sum(
        math.comb(n, i) * (0.5 ** n)
        for i in range(0, m + 1)
    )
    return min(1.0, 2.0 * prob)

def bootstrap_paired_diff(a: list[int], b: list[int], reps: int = 20000):
    # Returns b-a success-rate difference CI.
    if len(a) != len(b) or not a:
        return [None, None]
    rng = np.random.default_rng(20260914)
    aa = np.asarray(a, dtype=np.float64)
    bb = np.asarray(b, dtype=np.float64)
    d = bb - aa
    idx = rng.integers(0, len(d), size=(reps, len(d)))
    samples = d[idx].mean(axis=1)
    return [
        float(np.percentile(samples, 2.5)),
        float(np.percentile(samples, 97.5)),
    ]

def summarize_method(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    safe = sum(bool(r.get("safe_success", False)) for r in rows)
    collision = sum(bool(r.get("collision", False)) for r in rows)
    env_timeout = sum(bool(r.get("env_timeout", False)) for r in rows)
    wall_timeout = sum(bool(r.get("wall_timeout", False)) for r in rows)
    errors = sum("error" in r and not r.get("wall_timeout", False) for r in rows)
    unknown = sum(bool(r.get("unknown_penetration", False)) for r in rows)
    known = sum(bool(r.get("known_penetration", False)) for r in rows)
    contact = sum(bool(r.get("robot_obstacle_contact", False)) for r in rows)
    penetration = sum(bool(r.get("map_penetration", False)) for r in rows)

    steps = [int(r.get("steps", 0)) for r in rows if "steps" in r]
    walls = [
        float(r["wall_seconds"])
        for r in rows
        if isinstance(r.get("wall_seconds"), (int, float))
    ]
    planner_calls = []
    planner_times = []
    for r in rows:
        planner_calls.append(int(r.get("planner_call_count", 0) or 0))
        for x in r.get("planner_times_seconds", []) or []:
            try:
                x = float(x)
            except Exception:
                continue
            if math.isfinite(x):
                planner_times.append(x)

    def p95(xs):
        return float(np.percentile(np.asarray(xs, dtype=np.float64), 95.0)) if xs else None

    return {
        "n": n,
        "safe_success_count": safe,
        "safe_success_rate": safe/n if n else None,
        "safe_success_95ci_wilson": wilson(safe, n),
        "collision_count": collision,
        "collision_rate": collision/n if n else None,
        "collision_95ci_wilson": wilson(collision, n),
        "env_timeout_count": env_timeout,
        "wall_timeout_count": wall_timeout,
        "worker_error_count": errors,
        "unknown_penetration_count": unknown,
        "known_penetration_count": known,
        "robot_obstacle_contact_count": contact,
        "map_penetration_count": penetration,
        "mean_steps": float(statistics.fmean(steps)) if steps else None,
        "mean_wall_seconds": float(statistics.fmean(walls)) if walls else None,
        "p95_wall_seconds": p95(walls),
        "planner_call_count_total": sum(planner_calls),
        "planner_call_latency_mean_seconds": (
            float(statistics.fmean(planner_times)) if planner_times else None
        ),
        "planner_call_latency_p95_seconds": p95(planner_times),
        "planner_call_latency_max_seconds": max(planner_times) if planner_times else None,
        "planner_deadline_exceed_count": wall_timeout,
        "real_time_1p5s_gate_pass": bool(
            planner_times
            and p95(planner_times) is not None
            and p95(planner_times) <= 1.5
            and wall_timeout == 0
        ),
    }

def write_progress(done: int, total: int, seed: int | None, method: str | None, stage: str):
    data = {
        "stage": stage,
        "done": done,
        "total": total,
        "fraction": done / total if total else 0.0,
        "last_seed": seed,
        "last_method": method,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (OUT_ROOT / "progress.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def preflight() -> int:
    verify_protected()
    run_dir = OUT_ROOT / "preflight_22751"
    worker_dir = run_dir / "workers"
    worker_dir.mkdir(parents=True, exist_ok=True)

    rows = {}
    for method in METHODS:
        out_path = worker_dir / f"{method}_seed_22751.json"
        print(f"PREFLIGHT START method={method} seed=22751", flush=True)
        row = run_smoke_isolated(method, 22751, out_path, smoke_steps=5)
        rows[method] = row
        print(
            "PREFLIGHT RESULT",
            method,
            "error=", row.get("error"),
            "smoke_steps=", row.get("smoke_steps_executed"),
            "strict_collision_seen=", row.get("strict_collision_seen"),
            "wall=", row.get("wall_seconds"),
            flush=True,
        )
        if "error" in row:
            raise RuntimeError(
                f"PREFLIGHT_HARNESS_FAILED:{method}:{row.get('error')}"
            )

    sig_a = rows["phase21_v11"].get("scenario_signature")
    sig_b = rows["phase22_v1"].get("scenario_signature")
    if sig_a != sig_b:
        raise RuntimeError("PREFLIGHT_SCENARIO_MISMATCH")

    for method, row in rows.items():
        if row.get("sample_points_min_count") in (None, 0):
            raise RuntimeError(f"PREFLIGHT_STRICT_COLLISION_HELPER_FAILED:{method}")

    (run_dir / "preflight.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    print("PREFLIGHT_SCENARIO_MATCH=TRUE")
    print("PREFLIGHT_STRICT_COLLISION=PASS")
    print("PREFLIGHT_FINAL_HOLDOUT_TOUCHED=FALSE")
    return 0

def formal() -> int:
    verify_protected()
    run_dir = OUT_ROOT / "formal_22800_23099"
    worker_dir = run_dir / "workers"
    worker_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "policy": rel(MODEL_PATH),
        "policy_sha256": file_sha256(MODEL_PATH),
        "baseline": {
            "label": "phase21_v11",
            "module": METHODS["phase21_v11"][0],
            "class": METHODS["phase21_v11"][1],
        },
        "proposed": {
            "label": "phase22_v1",
            "module": METHODS["phase22_v1"][0],
            "class": METHODS["phase22_v1"][1],
        },
        "seeds": [22800, 23099],
        "seed_count": 300,
        "paired": True,
        "per_rollout_hard_wall_seconds": PER_ROLLOUT_TIMEOUT_S,
        "strict_collision": [
            "robot_sample_points(env)",
            "check_map_penetration(env, margin=0.02)",
            "robot_obstacle_contact(env)",
        ],
        "training": False,
        "post_holdout_tuning_allowed": False,
    }
    protocol_path = run_dir / "FROZEN_PROTOCOL.json"
    if protocol_path.exists():
        existing = json.loads(protocol_path.read_text(encoding="utf-8"))
        # Ignore timestamp only.
        existing_cmp = dict(existing)
        protocol_cmp = dict(protocol)
        existing_cmp.pop("frozen_at", None)
        protocol_cmp.pop("frozen_at", None)
        if existing_cmp != protocol_cmp:
            raise RuntimeError("FROZEN_PROTOCOL_MISMATCH_ON_RESUME")
    else:
        protocol_path.write_text(
            json.dumps(protocol, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    total = len(FORMAL_SEEDS) * len(METHODS)
    done = 0
    all_rows: list[dict[str, Any]] = []

    # Pair by seed so scenario consistency is checked immediately.
    for seed_idx, seed in enumerate(FORMAL_SEEDS, 1):
        pair_rows = {}
        for method in ("phase21_v11", "phase22_v1"):
            out_path = worker_dir / f"{method}_seed_{seed}.json"

            print(
                f"FORMAL [{done+1}/{total}] "
                f"pair={seed_idx}/300 seed={seed} method={method} START",
                flush=True,
            )

            row = run_isolated(method, seed, out_path)
            pair_rows[method] = row
            all_rows.append(row)
            done += 1
            write_progress(done, total, seed, method, "FORMAL_300_PAIRED")

            print(
                "FORMAL RESULT",
                f"seed={seed}",
                f"method={method}",
                f"safe={row.get('safe_success', False)}",
                f"collision={row.get('collision', False)}",
                f"env_timeout={row.get('env_timeout', False)}",
                f"wall_timeout={row.get('wall_timeout', False)}",
                f"steps={row.get('steps')}",
                f"wall={row.get('wall_seconds')}",
                f"resumed={row.get('resumed', False)}",
                flush=True,
            )

        a = pair_rows["phase21_v11"]
        b = pair_rows["phase22_v1"]

        # A wall timeout is still a valid failure row, but an arbitrary worker
        # exception is not acceptable for confirmatory statistics.
        for method, row in pair_rows.items():
            if "error" in row and not row.get("wall_timeout", False):
                raise RuntimeError(
                    f"FORMAL_WORKER_ERROR seed={seed} method={method} "
                    f"error={row.get('error')}"
                )

        if (
            "scenario_signature" in a
            and "scenario_signature" in b
            and a["scenario_signature"] != b["scenario_signature"]
        ):
            raise RuntimeError(f"FORMAL_SCENARIO_MISMATCH seed={seed}")

    # Reload from disk to make resume/final aggregation deterministic.
    all_rows = []
    for seed in FORMAL_SEEDS:
        for method in ("phase21_v11", "phase22_v1"):
            path = worker_dir / f"{method}_seed_{seed}.json"
            if not path.exists():
                raise RuntimeError(f"MISSING_FORMAL_ROW:{method}:{seed}")
            all_rows.append(json.loads(path.read_text(encoding="utf-8")))

    by_method = {
        method: [r for r in all_rows if r["method"] == method]
        for method in METHODS
    }

    summary = {
        method: summarize_method(rows)
        for method, rows in by_method.items()
    }

    paired_rows = []
    mismatch = 0
    a_success = []
    b_success = []
    b_only = 0
    a_only = 0
    both_success = 0
    neither_success = 0
    b_collision_only = 0
    a_collision_only = 0

    a_by_seed = {int(r["seed"]): r for r in by_method["phase21_v11"]}
    b_by_seed = {int(r["seed"]): r for r in by_method["phase22_v1"]}

    for seed in FORMAL_SEEDS:
        a = a_by_seed[seed]
        b = b_by_seed[seed]

        if (
            "scenario_signature" in a
            and "scenario_signature" in b
            and a["scenario_signature"] != b["scenario_signature"]
        ):
            mismatch += 1

        sa = int(bool(a.get("safe_success", False)))
        sb = int(bool(b.get("safe_success", False)))
        ca = int(bool(a.get("collision", False)))
        cb = int(bool(b.get("collision", False)))
        a_success.append(sa)
        b_success.append(sb)

        if sa and sb:
            both_success += 1
        elif (not sa) and sb:
            b_only += 1
        elif sa and (not sb):
            a_only += 1
        else:
            neither_success += 1

        if (not ca) and cb:
            b_collision_only += 1
        elif ca and (not cb):
            a_collision_only += 1

        paired_rows.append({
            "seed": seed,
            "phase21_v11_safe": sa,
            "phase22_v1_safe": sb,
            "phase21_v11_collision": ca,
            "phase22_v1_collision": cb,
            "phase21_v11_wall_timeout": bool(a.get("wall_timeout", False)),
            "phase22_v1_wall_timeout": bool(b.get("wall_timeout", False)),
        })

    success_diff = (
        summary["phase22_v1"]["safe_success_rate"]
        - summary["phase21_v11"]["safe_success_rate"]
    )
    collision_diff = (
        summary["phase22_v1"]["collision_rate"]
        - summary["phase21_v11"]["collision_rate"]
    )

    paired_stats = {
        "n_pairs": 300,
        "scenario_mismatch_count": mismatch,
        "both_success": both_success,
        "phase22_only_success": b_only,
        "phase21_only_success": a_only,
        "neither_success": neither_success,
        "safe_success_rate_difference_phase22_minus_phase21": success_diff,
        "safe_success_rate_difference_95ci_paired_bootstrap": bootstrap_paired_diff(
            a_success, b_success
        ),
        "safe_success_mcnemar_exact_p": exact_mcnemar_p(b_only, a_only),
        "phase22_only_collision": b_collision_only,
        "phase21_only_collision": a_collision_only,
        "collision_rate_difference_phase22_minus_phase21": collision_diff,
        "collision_mcnemar_exact_p": exact_mcnemar_p(
            b_collision_only, a_collision_only
        ),
    }

    confirmatory_pass = bool(
        mismatch == 0
        and success_diff > 0.0
        and paired_stats["safe_success_mcnemar_exact_p"] < 0.05
        and collision_diff < 0.0
    )

    conclusion = {
        "confirmatory_accuracy_safety_gate_pass": confirmatory_pass,
        "real_time_gate_phase22_v1_pass": summary["phase22_v1"]["real_time_1p5s_gate_pass"],
        "post_holdout_tuning_allowed": False,
        "interpretation": (
            "CONFIRMED_PHASE22_V1_ACCURACY_SAFETY_GAIN"
            if confirmatory_pass
            else "FINAL_HOLDOUT_DID_NOT_CONFIRM_PRE_REGISTERED_GAIN"
        ),
    }

    final = {
        "protocol": protocol,
        "summary": summary,
        "paired_statistics": paired_stats,
        "conclusion": conclusion,
    }

    # JSON
    (run_dir / "episodes.json").write_text(
        json.dumps(all_rows, ensure_ascii=False, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps(final, ensure_ascii=False, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    (run_dir / "paired_statistics.json").write_text(
        json.dumps(paired_stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Episode CSV
    fields = [
        "seed", "method", "safe_success", "collision",
        "env_timeout", "wall_timeout", "steps",
        "unknown_penetration", "known_penetration",
        "robot_obstacle_contact", "map_penetration",
        "minimum_clearance", "planner_call_count",
        "planner_mean_seconds", "planner_p95_seconds",
        "planner_max_seconds", "rollout_elapsed_seconds",
        "wall_seconds",
    ]
    with (run_dir / "episodes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k) for k in fields})

    # Paper table CSV
    paper_fields = [
        "method", "n", "safe_success_count", "safe_success_rate",
        "safe_success_95ci_wilson", "collision_count", "collision_rate",
        "collision_95ci_wilson", "env_timeout_count", "wall_timeout_count",
        "unknown_penetration_count", "known_penetration_count",
        "mean_steps", "planner_call_latency_mean_seconds",
        "planner_call_latency_p95_seconds", "planner_call_latency_max_seconds",
        "real_time_1p5s_gate_pass",
    ]
    with (run_dir / "paper_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=paper_fields)
        w.writeheader()
        for method in ("phase21_v11", "phase22_v1"):
            row = dict(summary[method])
            row["method"] = method
            row["safe_success_95ci_wilson"] = json.dumps(
                row["safe_success_95ci_wilson"]
            )
            row["collision_95ci_wilson"] = json.dumps(
                row["collision_95ci_wilson"]
            )
            w.writerow({k: row.get(k) for k in paper_fields})

    # Paired CSV
    with (run_dir / "paired_rows.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(paired_rows[0].keys()))
        w.writeheader()
        w.writerows(paired_rows)

    def pct(x):
        return "NA" if x is None else f"{100.0*x:.2f}%"

    s21 = summary["phase21_v11"]
    s22 = summary["phase22_v1"]
    report = f"""# MK-MINI Phase Final Holdout 300

## Frozen protocol

- Policy: `{protocol['policy']}`
- Baseline: Phase21 v11
- Proposed method: Phase22 v1 continuous corridor
- Seeds: 22800–23099
- Paired episodes: 300
- Training: false
- Post-holdout tuning: forbidden
- Strict collision: robot sample points + map penetration (0.02 m) + physical obstacle contact

## Main result

| Method | Safe success | Collision | Env timeout | Wall timeout | Planner P95 |
|---|---:|---:|---:|---:|---:|
| Phase21 v11 | {s21['safe_success_count']}/300 ({pct(s21['safe_success_rate'])}) | {s21['collision_count']}/300 ({pct(s21['collision_rate'])}) | {s21['env_timeout_count']} | {s21['wall_timeout_count']} | {s21['planner_call_latency_p95_seconds']} s |
| Phase22 v1 | {s22['safe_success_count']}/300 ({pct(s22['safe_success_rate'])}) | {s22['collision_count']}/300 ({pct(s22['collision_rate'])}) | {s22['env_timeout_count']} | {s22['wall_timeout_count']} | {s22['planner_call_latency_p95_seconds']} s |

## Paired statistics

- Scenario mismatch: {mismatch}
- Phase22-only success: {b_only}
- Phase21-only success: {a_only}
- McNemar exact p (safe success): {paired_stats['safe_success_mcnemar_exact_p']}
- Safe-success difference (Phase22 - Phase21): {success_diff}
- Paired bootstrap 95% CI: {paired_stats['safe_success_rate_difference_95ci_paired_bootstrap']}
- Collision difference (Phase22 - Phase21): {collision_diff}
- McNemar exact p (collision): {paired_stats['collision_mcnemar_exact_p']}

## Confirmatory decision

- Accuracy/safety confirmatory gate: {confirmatory_pass}
- Phase22 v1 real-time 1.5 s P95 gate: {s22['real_time_1p5s_gate_pass']}
- Interpretation: {conclusion['interpretation']}
- Post-holdout tuning allowed: false
"""
    (run_dir / "final_report.md").write_text(report, encoding="utf-8")

    write_progress(total, total, FORMAL_SEEDS[-1], "phase22_v1", "FORMAL_COMPLETE")

    print("=" * 92)
    print("PHASE FINAL HOLDOUT 300 COMPLETE")
    print("=" * 92)
    print(
        "PHASE21_V11",
        "SAFE=", f"{s21['safe_success_count']}/300",
        "COLLISION=", f"{s21['collision_count']}/300",
        "WALL_TIMEOUT=", s21["wall_timeout_count"],
        "PLANNER_P95=", s21["planner_call_latency_p95_seconds"],
    )
    print(
        "PHASE22_V1",
        "SAFE=", f"{s22['safe_success_count']}/300",
        "COLLISION=", f"{s22['collision_count']}/300",
        "WALL_TIMEOUT=", s22["wall_timeout_count"],
        "PLANNER_P95=", s22["planner_call_latency_p95_seconds"],
    )
    print("SCENARIO_MISMATCH_COUNT =", mismatch)
    print("PHASE22_ONLY_SUCCESS =", b_only)
    print("PHASE21_ONLY_SUCCESS =", a_only)
    print("MCNEMAR_SAFE_P =", paired_stats["safe_success_mcnemar_exact_p"])
    print("SAFE_DIFF_PHASE22_MINUS_PHASE21 =", success_diff)
    print(
        "SAFE_DIFF_95CI =",
        paired_stats["safe_success_rate_difference_95ci_paired_bootstrap"],
    )
    print("CONFIRMATORY_ACCURACY_SAFETY_GATE_PASS =", confirmatory_pass)
    print("PHASE22_REAL_TIME_1P5S_GATE_PASS =", s22["real_time_1p5s_gate_pass"])
    print("POST_HOLDOUT_TUNING_ALLOWED = FALSE")
    print("FINAL_REPORT =", rel(run_dir / "final_report.md"))
    print("PHASE_FINAL_HOLDOUT_300_DONE = TRUE")
    return 0

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=["preflight", "formal", "worker", "smoke_worker"])
    p.add_argument("--method", choices=list(METHODS))
    p.add_argument("--seed", type=int)
    p.add_argument("--out")
    p.add_argument("--smoke-steps", type=int, default=5)
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.mode == "smoke_worker":
        if args.method is None or args.seed is None or args.out is None:
            raise SystemExit("SMOKE_WORKER_ARGS_MISSING")
        raise SystemExit(
            smoke_worker(
                args.method,
                args.seed,
                Path(args.out),
                smoke_steps=args.smoke_steps,
            )
        )
    if args.mode == "worker":
        if args.method is None or args.seed is None or args.out is None:
            raise SystemExit("WORKER_ARGS_MISSING")
        raise SystemExit(worker(args.method, args.seed, Path(args.out)))
    if args.mode == "preflight":
        raise SystemExit(preflight())
    raise SystemExit(formal())
