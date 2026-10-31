
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(os.environ["MKMINI_PROJECT"]).resolve()
BASE_SCRIPT = (
    ROOT
    / "experiments/phase_paper_stageG2A_randomized_unknown_generalization_80_v1/"
      "run_g2a.py"
)
HERE = ROOT / "experiments/phase_paper_stageG2B_LH40_v1"
OUT = HERE / "results"
WORK = OUT / "workers"
ISO = OUT / "method_runs"
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
ISO.mkdir(parents=True, exist_ok=True)

WORKER = HERE / "lh_method_worker.py"

PROTOCOL = "G2B_LH40_V1_20260915"
TARGET_N = 40
CANDIDATE_START = 23400
CANDIDATE_END = 23999
MIN_ASTAR_M = 3.0
MIN_EUCLID_M = 2.5
MAX_STEPS = 600
METHOD_WALL = 120
POST_READY_WATCHDOG = 135
STARTUP_TIMEOUT = 180
BOOT_N = 20000

SELECTION_PATH = OUT / "selection_manifest.json"
PREREG_PATH = OUT / "preregistration.json"
FINAL_REPORT = OUT / "g2b_lh40_final_report.json"

def load_base():
    spec = importlib.util.spec_from_file_location("g2a_lh_parent_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("FAILED_TO_LOAD_G2A_BASE")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["g2a_lh_parent_base"] = mod
    spec.loader.exec_module(mod)
    return mod

G = load_base()

PREREG = {
    "protocol_version": PROTOCOL,
    "purpose": "fresh long-horizon randomized unknown-obstacle stress test",
    "primary_endpoint": "collision-free task success",
    "baseline": G.BASE_CLS,
    "proposed": G.PROP_CLS,
    "model_sha256": G.MODEL_SHA,
    "candidate_seed_pool": [CANDIDATE_START, CANDIDATE_END],
    "selection_order": "ascending_seed_first_eligible",
    "selection_uses_outcomes": False,
    "selection_rollout_performed": False,
    "target_pairs": TARGET_N,
    "long_horizon_rule": {
        "astar_path_length_m_min": MIN_ASTAR_M,
        "euclidean_start_goal_m_min": MIN_EUCLID_M,
    },
    "randomized": True,
    "terminate_on_collision": True,
    "penetration_margin": 0.02,
    "safe_clearance": 0.35,
    "max_steps": MAX_STEPS,
    "success_dist_m": 0.90,
    "method_wall_timeout_s": METHOD_WALL,
    "external_post_ready_watchdog_s": POST_READY_WATCHDOG,
    "control_domain_randomization": False,
    "paper_runtime_accelerators": False,
    "final_holdout_22800_23099_reused": False,
    "g2a_23100_23179_reused": False,
    "method_tuning_after_open": False,
    "statistics": ["Wilson95", "paired bootstrap20k", "exact McNemar"],
    "secondary_metrics": [
        "collision",
        "wall_timeout",
        "env_timeout",
        "astar_path_length_m",
        "euclidean_start_goal_m",
        "steps",
        "minimum_unknown_clearance",
        "phase22_attempted",
        "phase22_corridor_success",
        "method_wall_seconds",
    ],
}

def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def close_env(env):
    try:
        env.close()
    except Exception:
        pass

def path_length(path) -> float:
    a = np.asarray(path, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] < 2 or a.shape[1] < 2:
        return float("nan")
    a = a[:, :2]
    return float(np.linalg.norm(np.diff(a, axis=0), axis=1).sum())

def scenario_geometry_from_baseline(env, sig):
    p = getattr(env, "phase19_planned_path", None)
    if p is None:
        p = getattr(env, "phase21_v3_original_path", None)
    if p is None:
        p = getattr(env, "raw_astar_path", None)
    astar = path_length(p)

    s = np.asarray(sig["robot_xy"], dtype=np.float64)
    g = np.asarray(sig["goal_xy"], dtype=np.float64)
    euclid = float(np.linalg.norm(g - s))

    unchanged = bool(getattr(env, "phase19_path_unchanged", True))
    unknown_count = int(getattr(env, "phase19_unknown_count", 1))
    return astar, euclid, unchanged, unknown_count

def preflight():
    if G.sha256(G.MODEL) != G.MODEL_SHA:
        raise SystemExit("MODEL_SHA_MISMATCH")
    if int(G.MAX_STEPS) != MAX_STEPS:
        raise SystemExit(f"MAX_STEPS_CHANGED={G.MAX_STEPS}")
    if int(G.METHOD_WALL) != METHOD_WALL:
        raise SystemExit(f"METHOD_WALL_CHANGED={G.METHOD_WALL}")
    if not WORKER.is_file():
        raise SystemExit(f"WORKER_MISSING={WORKER}")

    # Prevent accidental reuse of already-opened evaluation ranges.
    old = set(range(22800, 23180))
    cand = set(range(CANDIDATE_START, CANDIDATE_END + 1))
    if old & cand:
        raise SystemExit("CANDIDATE_POOL_OVERLAPS_PRIOR_FORMAL_SEEDS")

    print("MODEL_SHA_MATCH=True")
    print("MAX_STEPS_600=True")
    print("METHOD_WALL_120=True")
    print(f"CANDIDATE_POOL={CANDIDATE_START}..{CANDIDATE_END}")
    print(f"TARGET_PAIRS={TARGET_N}")
    print(f"MIN_ASTAR_M={MIN_ASTAR_M}")
    print(f"MIN_EUCLID_M={MIN_EUCLID_M}")
    print("FINAL_HOLDOUT_REUSED=FALSE")
    print("G2A_SEEDS_REUSED=FALSE")
    print("PAPER_RUNTIME_ACCELERATORS=FALSE")

def screen():
    """
    Reset-only deterministic selection. No policy/model rollout is run.
    Selection is based ONLY on path geometry and protocol integrity.
    """
    preflight()
    dump(PREREG_PATH, PREREG)

    if SELECTION_PATH.is_file():
        old = read_json(SELECTION_PATH)
        if old.get("protocol_version") == PROTOCOL and len(old.get("selected", [])) == TARGET_N:
            print("SELECTION_ALREADY_FROZEN=TRUE")
            print("SELECTED_SEEDS=" + ",".join(str(x["seed"]) for x in old["selected"]))
            return old

    E, _ = G.load_eval()
    BC = G.env_class(G.BASE_MOD, G.BASE_CLS)
    PC = G.env_class(G.PROP_MOD, G.PROP_CLS)

    selected = []
    scanned = 0
    reject_short = 0
    reject_integrity = 0

    print("=" * 96)
    print("G2B-LH40 RESET-ONLY SCREEN — NO OUTCOME ROLLOUT")
    print("=" * 96)

    for seed in range(CANDIDATE_START, CANDIDATE_END + 1):
        if len(selected) >= TARGET_N:
            break
        scanned += 1

        be = None
        try:
            be, _, _, bs = G.prepare(E, BC, seed)
            astar, euclid, unchanged, unknown_count = scenario_geometry_from_baseline(be, bs)

            eligible = (
                math.isfinite(astar)
                and astar >= MIN_ASTAR_M
                and euclid >= MIN_EUCLID_M
                and unchanged
                and unknown_count >= 1
            )
            if not eligible:
                reject_short += 1
                continue
        except Exception as e:
            reject_integrity += 1
            print(f"SCREEN_REJECT seed={seed} reason={type(e).__name__}:{e}", flush=True)
            continue
        finally:
            if be is not None:
                close_env(be)

        # For eligible seeds only, reset the proposed environment and verify
        # exact scenario identity. Still NO rollout and no outcome inspection.
        pe = None
        try:
            pe, _, _, ps = G.prepare(E, PC, seed)
            if bs != ps:
                reject_integrity += 1
                print(f"SCREEN_REJECT seed={seed} reason=SCENARIO_MISMATCH", flush=True)
                continue
        finally:
            if pe is not None:
                close_env(pe)

        item = {
            "seed": int(seed),
            "astar_path_length_m": float(astar),
            "euclidean_start_goal_m": float(euclid),
            "scenario_signature": bs,
        }
        selected.append(item)
        print(
            f"SELECT {len(selected):02d}/{TARGET_N} seed={seed} "
            f"astar_m={astar:.3f} euclid_m={euclid:.3f}",
            flush=True,
        )

    if len(selected) != TARGET_N:
        raise SystemExit(
            f"INSUFFICIENT_LONG_HORIZON_SCENARIOS selected={len(selected)} "
            f"scanned={scanned} pool={CANDIDATE_START}..{CANDIDATE_END}"
        )

    manifest = {
        "protocol_version": PROTOCOL,
        "selection_frozen": True,
        "selection_uses_outcomes": False,
        "rollout_performed_during_selection": False,
        "candidate_seed_pool": [CANDIDATE_START, CANDIDATE_END],
        "scanned_candidates": scanned,
        "rejected_short_or_geometry": reject_short,
        "rejected_integrity": reject_integrity,
        "selected": selected,
    }
    dump(SELECTION_PATH, manifest)

    arr = np.asarray([x["astar_path_length_m"] for x in selected])
    eu = np.asarray([x["euclidean_start_goal_m"] for x in selected])
    print("")
    print(f"SELECTION_FROZEN=True")
    print(f"SELECTED_N={len(selected)}")
    print(f"ASTAR_MIN_MEAN_MAX={arr.min():.3f},{arr.mean():.3f},{arr.max():.3f}")
    print(f"EUCLID_MIN_MEAN_MAX={eu.min():.3f},{eu.mean():.3f},{eu.max():.3f}")
    print("OUTCOME_ROLLOUTS_PERFORMED=FALSE")
    print("G2B_LH40_SCREEN=PASS")
    return manifest

def timeout_row(method: str, elapsed: float):
    row = {
        "success": False,
        "collision": False,
        "env_timeout": False,
        "wall_timeout": True,
        "safe_success": False,
        "wall_seconds": float(METHOD_WALL),
        "final_class": "WALL_TIMEOUT",
        "external_watchdog_enforced": True,
        "external_watchdog_observed_elapsed_s": float(elapsed),
        "wall_timeout_protocol_s": METHOD_WALL,
    }
    if method == "proposed":
        row.update({
            "phase22_attempted": None,
            "phase22_corridor_success": None,
            "phase22_candidate_count": None,
            "phase22_failure_reason": "TELEMETRY_UNAVAILABLE_EXTERNAL_WATCHDOG",
            "phase22_telemetry_unavailable": True,
        })
    return row

def kill_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    try:
        proc.wait(timeout=10)
    except Exception:
        pass

def run_one(seed: int, method: str):
    ready = ISO / f"ready_{seed}_{method}.json"
    result = ISO / f"result_{seed}_{method}.json"
    log = ISO / f"log_{seed}_{method}.txt"
    for p in (ready, result):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    cmd = [
        sys.executable, "-u", str(WORKER),
        "--seed", str(seed),
        "--method", method,
        "--ready", str(ready),
        "--result", str(result),
    ]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["CUDA_VISIBLE_DEVICES"] = ""

    print(f"METHOD_START seed={seed} method={method}", flush=True)
    with log.open("w", encoding="utf-8") as lf:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=lf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )

        launch_t = time.monotonic()
        ready_seen = None

        while True:
            rc = proc.poll()
            if ready_seen is None and ready.is_file():
                ready_seen = time.monotonic()
                print(f"METHOD_READY seed={seed} method={method}", flush=True)

            if rc is not None:
                break

            now = time.monotonic()
            if ready_seen is None:
                if now - launch_t > STARTUP_TIMEOUT:
                    kill_group(proc)
                    return None, {
                        "seed": seed,
                        "method": method,
                        "type": "STARTUP_TIMEOUT",
                    }
            else:
                elapsed = now - ready_seen
                if elapsed > POST_READY_WATCHDOG:
                    kill_group(proc)
                    meta = read_json(ready)
                    print(
                        f"METHOD_EXTERNAL_WALL_TIMEOUT seed={seed} "
                        f"method={method} elapsed={elapsed:.3f}",
                        flush=True,
                    )
                    return {
                        "signature": meta["scenario_signature"],
                        "protocol_info": meta["protocol_info"],
                        "row": timeout_row(method, elapsed),
                    }, None
            time.sleep(0.25)

        if not ready.is_file():
            tail = log.read_text(encoding="utf-8", errors="replace")[-4000:]
            return None, {
                "seed": seed, "method": method,
                "type": "EXIT_BEFORE_READY",
                "rc": proc.returncode,
                "tail": tail,
            }

        meta = read_json(ready)

        # Accept a persisted scientific result even if cleanup exits nonzero.
        if result.is_file():
            x = read_json(result)
            if x["scenario_signature"] != meta["scenario_signature"]:
                return None, {
                    "seed": seed, "method": method,
                    "type": "RESULT_SIGNATURE_MISMATCH",
                }
            print(
                f"METHOD_DONE seed={seed} method={method} "
                f"class={x['row'].get('final_class')} rc={proc.returncode}",
                flush=True,
            )
            return {
                "signature": x["scenario_signature"],
                "protocol_info": x["protocol_info"],
                "row": x["row"],
            }, None

        tail = log.read_text(encoding="utf-8", errors="replace")[-4000:]
        return None, {
            "seed": seed, "method": method,
            "type": "PROCESS_FAILURE_AFTER_READY",
            "rc": proc.returncode,
            "tail": tail,
        }

def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [max(0.0, c-h), min(1.0, c+h)]

def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(
        1.0,
        2.0 * sum(math.comb(n, i) for i in range(k+1)) / (2**n)
    )

def bootstrap(base, prop):
    base = np.asarray(base, dtype=float)
    prop = np.asarray(prop, dtype=float)
    d = prop - base
    n = len(d)
    rng = np.random.default_rng(20260915)
    vals = np.empty(BOOT_N)
    for i in range(BOOT_N):
        vals[i] = np.mean(d[rng.integers(0, n, n)])
    return [
        float(np.quantile(vals, 0.025)),
        float(np.quantile(vals, 0.975)),
    ]

def summarize(rows, selection):
    n = len(rows)
    bs = np.array([bool(r["baseline"].get("safe_success", False)) for r in rows])
    ps = np.array([bool(r["proposed"].get("safe_success", False)) for r in rows])
    bc = np.array([bool(r["baseline"].get("collision", False)) for r in rows])
    pc = np.array([bool(r["proposed"].get("collision", False)) for r in rows])
    bw = np.array([bool(r["baseline"].get("wall_timeout", False)) for r in rows])
    pw = np.array([bool(r["proposed"].get("wall_timeout", False)) for r in rows])

    po = int(np.sum(ps & ~bs))
    bo = int(np.sum(bs & ~ps))
    pco = int(np.sum(pc & ~bc))
    bco = int(np.sum(bc & ~pc))

    def binstat(x):
        k = int(np.sum(x))
        return {"count": k, "n": n, "rate": k/n if n else None, "wilson95": wilson(k,n)}

    ast = np.asarray([selection[r["seed"]]["astar_path_length_m"] for r in rows], dtype=float)
    euc = np.asarray([selection[r["seed"]]["euclidean_start_goal_m"] for r in rows], dtype=float)

    def mean_field(method, field):
        vals = []
        for r in rows:
            v = r[method].get(field)
            try:
                v = float(v)
            except Exception:
                continue
            if math.isfinite(v):
                vals.append(v)
        return float(np.mean(vals)) if vals else None

    return {
        "n_pairs": n,
        "baseline": {
            "safe_success": binstat(bs),
            "collision": binstat(bc),
            "wall_timeout": binstat(bw),
            "mean_wall_s": mean_field("baseline", "wall_seconds"),
            "mean_steps": mean_field("baseline", "steps"),
            "mean_min_unknown_clearance": mean_field("baseline", "min_unknown_clearance"),
        },
        "proposed": {
            "safe_success": binstat(ps),
            "collision": binstat(pc),
            "wall_timeout": binstat(pw),
            "mean_wall_s": mean_field("proposed", "wall_seconds"),
            "mean_steps": mean_field("proposed", "steps"),
            "mean_min_unknown_clearance": mean_field("proposed", "min_unknown_clearance"),
            "phase22_attempted": int(sum(bool(r["proposed"].get("phase22_attempted")) for r in rows)),
            "phase22_corridor_success": int(sum(bool(r["proposed"].get("phase22_corridor_success")) for r in rows)),
        },
        "paired_safe_success": {
            "proposed_only": po,
            "baseline_only": bo,
            "both": int(np.sum(ps & bs)),
            "neither": int(np.sum(~ps & ~bs)),
            "difference": float(np.mean(ps) - np.mean(bs)) if n else None,
            "bootstrap95": bootstrap(bs, ps) if n else [None, None],
            "mcnemar_p": exact_mcnemar(po, bo),
        },
        "paired_collision": {
            "proposed_only": pco,
            "baseline_only": bco,
            "difference": float(np.mean(pc) - np.mean(bc)) if n else None,
            "mcnemar_p": exact_mcnemar(pco, bco),
        },
        "long_horizon_coverage": {
            "astar_path_length_m": {
                "min": float(ast.min()) if n else None,
                "mean": float(ast.mean()) if n else None,
                "max": float(ast.max()) if n else None,
            },
            "euclidean_start_goal_m": {
                "min": float(euc.min()) if n else None,
                "mean": float(euc.mean()) if n else None,
                "max": float(euc.max()) if n else None,
            },
        },
    }

def formal():
    preflight()

    if not SELECTION_PATH.is_file():
        raise SystemExit("RUN_SCREEN_FIRST")
    manifest = read_json(SELECTION_PATH)
    selected_items = manifest.get("selected", [])
    if len(selected_items) != TARGET_N or not manifest.get("selection_frozen", False):
        raise SystemExit("INVALID_SELECTION_MANIFEST")
    selected = {int(x["seed"]): x for x in selected_items}

    dump(PREREG_PATH, PREREG)

    rows = []
    failures = []

    print("=" * 96)
    print("G2B-LH40 FORMAL LONG-HORIZON PAIRED EXPERIMENT")
    print("=" * 96)
    print("FORMAL_ALGORITHM=ORIGINAL_PHASE22_V1")
    print("PAPER_RUNTIME_ACCELERATORS=FALSE")
    print("METHOD_WALL_SECONDS=120")
    print("POST_READY_EXTERNAL_WATCHDOG_SECONDS=135")
    print("NO_TUNING_AFTER_OPEN=TRUE")

    for i, item in enumerate(selected_items, 1):
        seed = int(item["seed"])
        pair_path = WORK / f"pair_{seed}.json"

        if pair_path.is_file():
            try:
                old = read_json(pair_path)
                if (
                    old.get("protocol_version") == PROTOCOL
                    and old.get("same_scenario") is True
                    and "baseline" in old
                    and "proposed" in old
                ):
                    rows.append(old)
                    print(f"RESUME {i}/{TARGET_N} seed={seed}", flush=True)
                    continue
            except Exception:
                pass

        print(
            f"\nPAIR_START {i}/{TARGET_N} seed={seed} "
            f"astar_m={item['astar_path_length_m']:.3f} "
            f"euclid_m={item['euclidean_start_goal_m']:.3f}",
            flush=True,
        )

        b, bf = run_one(seed, "baseline")
        if bf is not None:
            failures.append(bf)
            print(f"PAIR_PROTOCOL_FAILURE seed={seed} method=baseline type={bf['type']}", flush=True)
            continue

        p, pf = run_one(seed, "proposed")
        if pf is not None:
            failures.append(pf)
            print(f"PAIR_PROTOCOL_FAILURE seed={seed} method=proposed type={pf['type']}", flush=True)
            continue

        if b["signature"] != p["signature"]:
            failures.append({
                "seed": seed, "type": "SCENARIO_MISMATCH"
            })
            print(f"PAIR_PROTOCOL_FAILURE seed={seed} type=SCENARIO_MISMATCH", flush=True)
            continue

        if b["signature"] != item["scenario_signature"]:
            failures.append({
                "seed": seed, "type": "SIGNATURE_CHANGED_FROM_FROZEN_SELECTION"
            })
            print(
                f"PAIR_PROTOCOL_FAILURE seed={seed} "
                "type=SIGNATURE_CHANGED_FROM_FROZEN_SELECTION",
                flush=True,
            )
            continue

        row = {
            "protocol_version": PROTOCOL,
            "seed": seed,
            "same_scenario": True,
            "scenario_signature": b["signature"],
            "astar_path_length_m": item["astar_path_length_m"],
            "euclidean_start_goal_m": item["euclidean_start_goal_m"],
            "baseline": b["row"],
            "proposed": p["row"],
            "protocol_info": b["protocol_info"],
        }
        dump(pair_path, row)
        rows.append(row)

        sm = summarize(rows, selected)
        dump(OUT / "progress.json", {
            "completed": len(rows),
            "target": TARGET_N,
            "protocol_failures": failures,
            "summary": sm,
        })
        print(
            f"PAIR_DONE seed={seed} "
            f"base={b['row'].get('final_class')} "
            f"prop={p['row'].get('final_class')} "
            f"completed={len(rows)}/{TARGET_N}",
            flush=True,
        )

    rows = sorted(rows, key=lambda x: x["seed"])
    sm = summarize(rows, selected) if rows else {}
    complete = (len(rows) == TARGET_N and not failures)

    report = {
        "protocol_version": PROTOCOL,
        "preregistration": PREREG,
        "selection_manifest": str(SELECTION_PATH),
        "formal_complete": complete,
        "completed_pairs": len(rows),
        "target_pairs": TARGET_N,
        "protocol_failures": failures,
        "summary": sm,
        "rows": rows,
    }
    dump(FINAL_REPORT, report)

    print("\n" + "=" * 96)
    print("G2B-LH40 FINAL SUMMARY")
    print("=" * 96)
    print(f"FORMAL_COMPLETE={complete}")
    print(f"COMPLETED_PAIRS={len(rows)}/{TARGET_N}")
    print(f"PROTOCOL_FAILURES={len(failures)}")
    if rows:
        print(f"BASELINE_SAFE_SUCCESS={sm['baseline']['safe_success']}")
        print(f"PROPOSED_SAFE_SUCCESS={sm['proposed']['safe_success']}")
        print(f"SAFE_SUCCESS_DIFF={sm['paired_safe_success']['difference']}")
        print(f"SAFE_SUCCESS_BOOTSTRAP95={sm['paired_safe_success']['bootstrap95']}")
        print(f"SAFE_SUCCESS_MCNEMAR_P={sm['paired_safe_success']['mcnemar_p']}")
        print(f"BASELINE_COLLISION={sm['baseline']['collision']}")
        print(f"PROPOSED_COLLISION={sm['proposed']['collision']}")
        print(f"COLLISION_DIFF={sm['paired_collision']['difference']}")
        print(f"COLLISION_MCNEMAR_P={sm['paired_collision']['mcnemar_p']}")
        print(f"BASELINE_WALL_TIMEOUT={sm['baseline']['wall_timeout']}")
        print(f"PROPOSED_WALL_TIMEOUT={sm['proposed']['wall_timeout']}")
        print(f"PHASE22_ATTEMPTED={sm['proposed']['phase22_attempted']}")
        print(f"PHASE22_CORRIDOR_SUCCESS={sm['proposed']['phase22_corridor_success']}")
        print(f"LONG_HORIZON_COVERAGE={sm['long_horizon_coverage']}")
    print("G2B_LH40=" + ("PASS" if complete else "INCOMPLETE"))
    return 0 if complete else 7

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--formal", action="store_true")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()

    if args.screen:
        screen()
        return 0
    if args.formal:
        return formal()
    if args.full:
        screen()
        return formal()
    raise SystemExit("USE --screen, --formal, OR --full")

if __name__ == "__main__":
    raise SystemExit(main())
