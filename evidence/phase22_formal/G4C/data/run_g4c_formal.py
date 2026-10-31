from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()
G4 = ROOT / "experiments/phase_paper_stageG4_external_baseline_v1"
B1 = G4 / "g4b1_ackermann_dwa_devscreen"
B2 = G4 / "g4b2_ackermann_dwa_top2_validation"
OUT = G4 / "g4c_threeway_formal_100"
RESULTS = OUT / "results"
WORK = OUT / "workers"
RECORDS = OUT / "records"
CHILD = OUT / "run_g4c_method_child.py"

SEEDS = list(range(26200, 26300))
METHODS = ("dwa", "phase21_v11", "phase22_v1")
METHOD_WALL_S = 120.0
OUTER_KILL_S = 125
BOOT_N = 20000
DEFAULT_WORKERS = 2

FROZEN_DWA_SHA = "ff3e9c3d3fff5d9722bcf4d450e36c22c5b4c57966b488f0ac0a9d716ee0c11e"


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


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(safe(obj), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def verify_frozen_contract():
    b2_summary = B2 / "results" / "g4b2_summary.json"
    b2_text = B2 / "results" / "G4B2_SUMMARY.txt"
    dwa_cfg = B2 / "results" / "DWA_FROZEN_CONFIG.json"
    b1_hashes = B1 / "records" / "source_contract.sha256"
    prereg = RECORDS / "G4C_PREREGISTRATION.json"

    for p in (b2_summary, b2_text, dwa_cfg, b1_hashes, prereg):
        if not p.exists():
            raise RuntimeError(f"MISSING_CONTRACT_FILE={p}")

    b2 = load_json(b2_summary)
    if b2.get("frozen_config_name") != "C3_CLEARANCE_BIASED":
        raise RuntimeError("FROZEN_DWA_NAME_MISMATCH")
    if not bool(b2.get("dwa_config_frozen", False)):
        raise RuntimeError("DWA_NOT_FROZEN")
    if sha256(dwa_cfg) != FROZEN_DWA_SHA:
        raise RuntimeError("FROZEN_DWA_SHA_MISMATCH")

    # All files covered by the pre-B2 source contract must still be unchanged.
    for line in b1_hashes.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        expected, filename = line.split(maxsplit=1)
        p = Path(filename.strip())
        if not p.exists():
            raise RuntimeError(f"SOURCE_MISSING={p}")
        got = sha256(p)
        if got != expected:
            raise RuntimeError(
                f"SOURCE_HASH_CHANGED file={p} expected={expected} got={got}"
            )

    pre = load_json(prereg)
    if pre.get("seeds") != [26200, 26299] or pre.get("n_scenarios") != 100:
        raise RuntimeError("PREREG_SEED_CONTRACT_MISMATCH")
    if pre.get("methods") != list(METHODS):
        raise RuntimeError("PREREG_METHOD_CONTRACT_MISMATCH")
    if pre.get("dwa_frozen_config_sha256") != FROZEN_DWA_SHA:
        raise RuntimeError("PREREG_DWA_SHA_MISMATCH")

    return {
        "b2_summary_sha256": sha256(b2_summary),
        "dwa_frozen_config_sha256": sha256(dwa_cfg),
        "b1_source_contract_sha256": sha256(b1_hashes),
        "preregistration_sha256": sha256(prereg),
    }


def rotated_methods(seed: int):
    k = (seed - SEEDS[0]) % len(METHODS)
    return METHODS[k:] + METHODS[:k]


def method_paths(seed: int, method: str):
    d = WORK / f"seed_{seed}" / method
    return {
        "dir": d,
        "started": d / "started.json",
        "result": d / "result.json",
        "log": d / "stdout_stderr.log",
    }


def valid_existing(row, seed: int, method: str):
    if not isinstance(row, dict):
        return False
    return (
        int(row.get("seed", -1)) == seed
        and row.get("method") == method
        and row.get("final_class")
        in {
            "SAFE_SUCCESS",
            "COLLISION",
            "ENV_TIMEOUT",
            "WALL_TIMEOUT",
            "OTHER_FAILURE",
        }
        and row.get("scenario_signature") is not None
    )


def outer_timeout_row(started_path: Path, elapsed: float, seed: int, method: str):
    sig = None
    if started_path.exists():
        try:
            sig = load_json(started_path).get("scenario_signature")
        except Exception:
            pass
    return {
        "seed": seed,
        "method": method,
        "scenario_signature": sig,
        "success": False,
        "collision": False,
        "safe_success": False,
        "env_timeout": False,
        "wall_timeout": True,
        "wall_seconds": max(METHOD_WALL_S, float(elapsed)),
        "final_class": "WALL_TIMEOUT",
        "method_metrics": {},
        "outer_os_timeout": True,
    }


def run_method(seed: int, method: str, frozen_cfg: Path):
    p = method_paths(seed, method)
    p["dir"].mkdir(parents=True, exist_ok=True)

    if p["result"].exists():
        try:
            row = load_json(p["result"])
            if valid_existing(row, seed, method):
                return row, True
        except Exception:
            pass

    for x in (p["started"], p["result"], p["log"]):
        try:
            x.unlink()
        except FileNotFoundError:
            pass

    env = os.environ.copy()
    env["MKMINI_PROJECT"] = str(ROOT)
    env["PYTHONPATH"] = str(ROOT) + (
        ":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MUJOCO_GL"] = "egl"
    env["CUDA_VISIBLE_DEVICES"] = ""

    cmd = [
        "timeout",
        "--signal=TERM",
        "--kill-after=5s",
        f"{OUTER_KILL_S}s",
        sys.executable,
        "-u",
        str(CHILD),
        "--seed",
        str(seed),
        "--method",
        method,
        "--frozen-dwa-config",
        str(frozen_cfg),
        "--started-json",
        str(p["started"]),
        "--result-json",
        str(p["result"]),
    ]

    t0 = time.perf_counter()
    with p["log"].open("w", encoding="utf-8") as f:
        cp = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT,
        )
    elapsed = float(time.perf_counter() - t0)

    if cp.returncode == 0 and p["result"].exists():
        row = load_json(p["result"])
        if not valid_existing(row, seed, method):
            raise RuntimeError(
                f"INVALID_CHILD_RESULT seed={seed} method={method}"
            )
    elif cp.returncode in (124, 137, 143):
        row = outer_timeout_row(
            p["started"], elapsed, seed, method
        )
        if row["scenario_signature"] is None:
            raise RuntimeError(
                f"OUTER_TIMEOUT_BEFORE_SIGNATURE seed={seed} method={method}"
            )
        atomic_json(p["result"], row)
    else:
        raise RuntimeError(
            f"CHILD_FAILURE seed={seed} method={method} "
            f"rc={cp.returncode} log={p['log']}"
        )

    # Enforce the formal 120 s threshold even if the child returned after it.
    if (
        not bool(row.get("wall_timeout", False))
        and float(row.get("wall_seconds", 0.0)) >= METHOD_WALL_S
    ):
        row.update(
            {
                "success": False,
                "collision": False,
                "safe_success": False,
                "env_timeout": False,
                "wall_timeout": True,
                "final_class": "WALL_TIMEOUT",
            }
        )
        atomic_json(p["result"], row)

    return row, False


def run_seed(seed: int, frozen_cfg: Path):
    rows = {}
    resumed = {}
    for method in rotated_methods(seed):
        print(
            f"G4C START seed={seed} method={method}",
            flush=True,
        )
        row, was_resumed = run_method(seed, method, frozen_cfg)
        rows[method] = row
        resumed[method] = was_resumed
        print(
            f"G4C RESULT seed={seed} method={method} "
            f"class={row['final_class']} "
            f"wall={float(row.get('wall_seconds',0.0)):.3f} "
            f"resumed={was_resumed}",
            flush=True,
        )

    sigs = [rows[m].get("scenario_signature") for m in METHODS]
    same = (
        all(s is not None for s in sigs)
        and sigs[0] == sigs[1] == sigs[2]
    )
    pair = {
        "seed": seed,
        "same_scenario": same,
        "scenario_signature": sigs[0] if same else None,
        "method_order": list(rotated_methods(seed)),
        "resumed": resumed,
        "methods": rows,
    }
    atomic_json(WORK / f"seed_{seed}" / "threeway.json", pair)
    if not same:
        raise RuntimeError(f"SCENARIO_MISMATCH seed={seed}")
    return pair


def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = (
        z
        * math.sqrt(
            p * (1.0 - p) / n + z * z / (4.0 * n * n)
        )
        / d
    )
    return [max(0.0, c - h), min(1.0, c + h)]


def exact_mcnemar(b: int, c: int):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(
        1.0,
        2.0
        * sum(math.comb(n, i) for i in range(k + 1))
        / (2 ** n),
    )


def paired_bootstrap(a, b, seed=20260916):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = b - a
    n = len(d)
    rng = np.random.default_rng(seed)
    vals = np.empty(BOOT_N, dtype=float)
    for i in range(BOOT_N):
        idx = rng.integers(0, n, n)
        vals[i] = float(np.mean(d[idx]))
    return {
        "diff": float(np.mean(d)),
        "ci95": [
            float(np.quantile(vals, 0.025)),
            float(np.quantile(vals, 0.975)),
        ],
        "n_boot": BOOT_N,
    }


def method_summary(pairs, method: str):
    rows = [x["methods"][method] for x in pairs]
    n = len(rows)
    safe = sum(bool(r.get("safe_success")) for r in rows)
    col = sum(bool(r.get("collision")) for r in rows)
    wall = sum(bool(r.get("wall_timeout")) for r in rows)
    envto = sum(bool(r.get("env_timeout")) for r in rows)
    other = sum(r.get("final_class") == "OTHER_FAILURE" for r in rows)
    wall_vals = np.asarray(
        [float(r.get("wall_seconds", 0.0)) for r in rows],
        dtype=float,
    )
    steps = [
        float(r["steps"])
        for r in rows
        if r.get("steps") is not None
        and isinstance(r.get("steps"), (int, float))
    ]
    out = {
        "n": n,
        "safe_success": {
            "n": safe,
            "rate": safe / n,
            "wilson95": wilson(safe, n),
        },
        "collision": {
            "n": col,
            "rate": col / n,
            "wilson95": wilson(col, n),
        },
        "wall_timeout_n": wall,
        "env_timeout_n": envto,
        "other_failure_n": other,
        "wall_mean_s": float(wall_vals.mean()),
        "wall_median_s": float(np.median(wall_vals)),
        "wall_p95_s": float(np.quantile(wall_vals, 0.95)),
        "mean_steps_when_recorded": (
            float(np.mean(steps)) if steps else None
        ),
    }

    if method == "dwa":
        metrics = [r.get("method_metrics", {}) for r in rows]
        attempts = sum(
            int(m.get("g4_dwa_attempt_count", 0) or 0)
            for m in metrics
        )
        successes = sum(
            int(m.get("g4_dwa_success_count", 0) or 0)
            for m in metrics
        )
        failures = sum(
            int(m.get("g4_dwa_failure_count", 0) or 0)
            for m in metrics
        )
        total_plan = sum(
            float(m.get("g4_dwa_plan_time_total_s", 0.0) or 0.0)
            for m in metrics
        )
        max_plan = max(
            [
                float(m.get("g4_dwa_plan_time_max_s", 0.0) or 0.0)
                for m in metrics
            ]
            or [0.0]
        )
        out["planner"] = {
            "attempts": attempts,
            "successes": successes,
            "failures": failures,
            "success_rate_per_attempt": (
                successes / attempts if attempts else None
            ),
            "mean_time_s_per_attempt": (
                total_plan / attempts if attempts else None
            ),
            "max_single_plan_time_s": max_plan,
        }
    elif method == "phase22_v1":
        metrics = [r.get("method_metrics", {}) for r in rows]
        attempted = sum(
            bool(m.get("phase22_v1_attempted", False))
            for m in metrics
        )
        success = sum(
            bool(m.get("phase22_v1_success", False))
            for m in metrics
        )
        out["phase22_activation"] = {
            "attempted_episodes": attempted,
            "successful_corridor_episodes": success,
        }
    return out


def pairwise(pairs, a: str, b: str):
    a_safe = np.asarray(
        [bool(x["methods"][a].get("safe_success")) for x in pairs],
        dtype=bool,
    )
    b_safe = np.asarray(
        [bool(x["methods"][b].get("safe_success")) for x in pairs],
        dtype=bool,
    )
    a_col = np.asarray(
        [bool(x["methods"][a].get("collision")) for x in pairs],
        dtype=bool,
    )
    b_col = np.asarray(
        [bool(x["methods"][b].get("collision")) for x in pairs],
        dtype=bool,
    )

    b_only_safe = int(np.sum((~a_safe) & b_safe))
    a_only_safe = int(np.sum(a_safe & (~b_safe)))
    b_only_col = int(np.sum((~a_col) & b_col))
    a_only_col = int(np.sum(a_col & (~b_col)))

    safe_boot = paired_bootstrap(a_safe, b_safe)
    col_boot = paired_bootstrap(a_col, b_col, seed=20260917)

    return {
        "a": a,
        "b": b,
        "safe_success": {
            "b_minus_a_pp": 100.0 * safe_boot["diff"],
            "bootstrap95_pp": [
                100.0 * safe_boot["ci95"][0],
                100.0 * safe_boot["ci95"][1],
            ],
            "b_only": b_only_safe,
            "a_only": a_only_safe,
            "mcnemar_p": exact_mcnemar(
                b_only_safe, a_only_safe
            ),
        },
        "collision": {
            "b_minus_a_pp": 100.0 * col_boot["diff"],
            "bootstrap95_pp": [
                100.0 * col_boot["ci95"][0],
                100.0 * col_boot["ci95"][1],
            ],
            "b_only": b_only_col,
            "a_only": a_only_col,
            "mcnemar_p": exact_mcnemar(
                b_only_col, a_only_col
            ),
        },
    }


def aggregate():
    pairs = []
    missing = []
    for seed in SEEDS:
        p = WORK / f"seed_{seed}" / "threeway.json"
        if not p.exists():
            missing.append(seed)
            continue
        row = load_json(p)
        if not bool(row.get("same_scenario", False)):
            raise RuntimeError(f"INVALID_SCENARIO_PAIR seed={seed}")
        pairs.append(row)
    if missing:
        raise RuntimeError("MISSING_SEEDS=" + repr(missing))
    if len(pairs) != 100:
        raise RuntimeError(f"PAIR_COUNT={len(pairs)}")

    summary = {
        "protocol": "G4C_THREEWAY_FORMAL_100_V1",
        "formal_complete": True,
        "n_scenarios": len(pairs),
        "seed_range": [SEEDS[0], SEEDS[-1]],
        "methods": {
            m: method_summary(pairs, m)
            for m in METHODS
        },
        "pairwise": {
            "phase22_vs_dwa": pairwise(
                pairs, "dwa", "phase22_v1"
            ),
            "phase22_vs_phase21": pairwise(
                pairs, "phase21_v11", "phase22_v1"
            ),
            "dwa_vs_phase21": pairwise(
                pairs, "phase21_v11", "dwa"
            ),
        },
        "primary_external_comparison": "phase22_v1 vs dwa",
        "primary_endpoint": "collision-free task success",
        "formal_dwa_config": "C3_CLEARANCE_BIASED",
        "formal_dwa_config_sha256": FROZEN_DWA_SHA,
        "method_wall_timeout_s": METHOD_WALL_S,
        "max_steps": 600,
        "scenario_mismatch_n": 0,
        "post_open_tuning": False,
    }
    atomic_json(RESULTS / "g4c_summary.json", summary)

    lines = [
        "G4C THREE-WAY FORMAL EXTERNAL-BASELINE EVALUATION — 100 FRESH SCENARIOS",
        "=" * 110,
        f"SEEDS={SEEDS[0]}-{SEEDS[-1]} N=100",
        "METHODS=DWA_FROZEN_C3,PHASE21_V11,PHASE22_V1",
        "PRIMARY_EXTERNAL_COMPARISON=PHASE22_V1_VS_DWA",
        "PRIMARY_ENDPOINT=COLLISION_FREE_TASK_SUCCESS",
        "SCENARIO_MISMATCH_N=0",
        "POST_OPEN_TUNING=FALSE",
        "",
    ]
    for m in METHODS:
        s = summary["methods"][m]
        lines.append(
            f"{m}: safe={s['safe_success']['n']}/100 "
            f"({100*s['safe_success']['rate']:.2f}%) "
            f"collision={s['collision']['n']}/100 "
            f"({100*s['collision']['rate']:.2f}%) "
            f"wall_timeout={s['wall_timeout_n']} "
            f"env_timeout={s['env_timeout_n']} "
            f"other={s['other_failure_n']} "
            f"wall_mean={s['wall_mean_s']:.3f}s "
            f"wall_p95={s['wall_p95_s']:.3f}s"
        )
    lines.append("")
    for key in (
        "phase22_vs_dwa",
        "phase22_vs_phase21",
        "dwa_vs_phase21",
    ):
        x = summary["pairwise"][key]
        ss = x["safe_success"]
        cc = x["collision"]
        lines.append(
            f"{key}: SAFE b-a={ss['b_minus_a_pp']:.2f}pp "
            f"CI95=[{ss['bootstrap95_pp'][0]:.2f},{ss['bootstrap95_pp'][1]:.2f}] "
            f"b_only={ss['b_only']} a_only={ss['a_only']} "
            f"McNemar_p={ss['mcnemar_p']:.8g}; "
            f"COLLISION b-a={cc['b_minus_a_pp']:.2f}pp "
            f"CI95=[{cc['bootstrap95_pp'][0]:.2f},{cc['bootstrap95_pp'][1]:.2f}] "
            f"McNemar_p={cc['mcnemar_p']:.8g}"
        )
    lines += [
        "",
        "G4C_FORMAL_COMPLETE=TRUE",
        "NEXT=LOCK_SIMULATION_RESULTS_AND_WRITE_PAPER",
    ]
    text = "\n".join(lines) + "\n"
    (RESULTS / "G4C_SUMMARY.txt").write_text(
        text, encoding="utf-8"
    )
    print(text)


def formal(workers: int):
    contract = verify_frozen_contract()
    frozen_cfg = B2 / "results" / "DWA_FROZEN_CONFIG.json"

    print("=" * 110)
    print("G4C THREE-WAY FORMAL 100 — START")
    print("=" * 110)
    print(f"SEEDS={SEEDS[0]}-{SEEDS[-1]} N=100")
    print("METHODS=dwa,phase21_v11,phase22_v1")
    print(f"WORKERS={workers}")
    print(f"METHOD_WALL_S={METHOD_WALL_S}")
    print(f"OUTER_KILL_S={OUTER_KILL_S}")
    print(f"DWA_FROZEN_SHA={FROZEN_DWA_SHA}")
    print("POST_OPEN_TUNING=FALSE")
    print("FROZEN_CONTRACT=PASS")
    print(
        "METHOD_ORDER=ROTATED_BY_SEED_TO_DISTRIBUTE_SYSTEM_ORDER_EFFECTS"
    )

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers
    ) as ex:
        futures = {
            ex.submit(run_seed, seed, frozen_cfg): seed
            for seed in SEEDS
        }
        for fut in concurrent.futures.as_completed(futures):
            seed = futures[fut]
            try:
                fut.result()
            except Exception as e:
                print(
                    f"G4C SEED FAILURE seed={seed} error={e!r}",
                    flush=True,
                )
                raise

    aggregate()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
    )
    ap.add_argument(
        "--aggregate-only",
        action="store_true",
    )
    args = ap.parse_args()

    if args.aggregate_only:
        aggregate()
        return 0
    if args.workers < 1 or args.workers > 4:
        raise SystemExit("WORKERS_MUST_BE_1_TO_4")
    return formal(args.workers)


if __name__ == "__main__":
    raise SystemExit(main())
