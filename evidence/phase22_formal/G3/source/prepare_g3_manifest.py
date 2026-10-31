
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from pathlib import Path

import numpy as np

from envs.phase22.mkmini_phase22_v1_continuous_corridor_env import (
    MkMiniPhase22V1ContinuousCorridorEnv,
)
from training.phase21_risk_switch_fusion_sac.tests import (
    eval_phase21_v3_exact_pair_5ep as E,
)

ROOT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()
OUT = ROOT / "experiments/phase_paper_stageG3_multiscene_80_v1"
RESULTS = OUT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

DEFAULT_START = 24100
DEFAULT_SCAN_N = 96
MAX_SCAN_N = 192
NEEDED_PER_FAMILY = 20

FAMILIES = (
    "LOW_TURN_WIDE",
    "LOW_TURN_CONSTRAINED",
    "HIGH_TURN_WIDE",
    "HIGH_TURN_CONSTRAINED",
)


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
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else str(obj)
    return obj


def dump(path: Path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(safe(obj), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)


def sha256_bytes(payload: bytes):
    return hashlib.sha256(payload).hexdigest()


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed & 0xFFFFFFFF)


def resample_path(path, spacing=0.25):
    p = np.asarray(path, dtype=np.float64).reshape(-1, 2)
    if len(p) < 2:
        return p
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s[-1])
    if total <= 1e-9:
        return p[:1]
    n = max(2, int(math.ceil(total / spacing)) + 1)
    q = np.linspace(0.0, total, n)
    x = np.interp(q, s, p[:, 0])
    y = np.interp(q, s, p[:, 1])
    return np.column_stack([x, y])


def smooth3(path):
    p = np.asarray(path, dtype=np.float64)
    if len(p) < 5:
        return p
    q = p.copy()
    q[1:-1] = (p[:-2] + 2.0 * p[1:-1] + p[2:]) / 4.0
    return q


def route_metrics(path):
    p = resample_path(path, 0.25)
    p = smooth3(p)
    if len(p) < 3:
        return None

    d = np.diff(p, axis=0)
    seg = np.linalg.norm(d, axis=1)
    good = seg > 1e-6
    d = d[good]
    seg = seg[good]
    if len(seg) < 2:
        return None

    length = float(seg.sum())
    euclid = float(np.linalg.norm(p[-1] - p[0]))
    heading = np.arctan2(d[:, 1], d[:, 0])
    dh = np.arctan2(
        np.sin(np.diff(heading)),
        np.cos(np.diff(heading)),
    )
    total_turn = float(np.abs(dh).sum())
    turn_density = total_turn / max(length, 1e-9)
    tort = length / max(euclid, 1e-9)

    return {
        "astar_length_m": length,
        "endpoint_euclid_m": euclid,
        "tortuosity": tort,
        "total_abs_turn_deg": math.degrees(total_turn),
        "turn_density_rad_per_m": turn_density,
        "resampled_points": int(len(p)),
    }, p


def known_obstacle_arrays(env):
    rects = np.asarray(
        getattr(env, "rect_obstacles", np.zeros((0, 4))),
        dtype=np.float64,
    ).reshape(-1, 4)
    circles = np.asarray(
        getattr(env, "circle_obstacles", np.zeros((0, 3))),
        dtype=np.float64,
    ).reshape(-1, 3)

    unknown = np.asarray(
        getattr(env, "phase19_unknown_circles", np.zeros((0, 3))),
        dtype=np.float64,
    ).reshape(-1, 3)

    if len(unknown) and len(circles):
        keep = np.ones(len(circles), dtype=bool)
        for u in unknown:
            err = np.linalg.norm(circles[:, :2] - u[:2], axis=1) + np.abs(
                circles[:, 2] - u[2]
            )
            i = int(np.argmin(err))
            if float(err[i]) < 2e-3:
                keep[i] = False
        circles = circles[keep]

    return rects, circles


def point_clearance(points, rects, circles, map_min, map_max):
    p = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    all_c = []

    if len(rects):
        vals = []
        for cx, cy, hx, hy in rects:
            dx = np.maximum(np.abs(p[:, 0] - cx) - hx, 0.0)
            dy = np.maximum(np.abs(p[:, 1] - cy) - hy, 0.0)
            vals.append(np.hypot(dx, dy))
        all_c.append(np.min(np.stack(vals, axis=1), axis=1))

    if len(circles):
        vals = []
        for ox, oy, r in circles:
            vals.append(
                np.maximum(
                    np.hypot(p[:, 0] - ox, p[:, 1] - oy) - r,
                    0.0,
                )
            )
        all_c.append(np.min(np.stack(vals, axis=1), axis=1))

    if map_min is not None and map_max is not None:
        b = np.column_stack(
            [
                p[:, 0] - map_min,
                map_max - p[:, 0],
                p[:, 1] - map_min,
                map_max - p[:, 1],
            ]
        )
        all_c.append(np.min(b, axis=1))

    if not all_c:
        return np.full(len(p), np.nan)

    return np.min(np.stack(all_c, axis=1), axis=1)


def known_map_hash(rects, circles):
    payload = {
        "rects": np.round(rects, 6).tolist(),
        "circles": np.round(circles, 6).tolist(),
    }
    return sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )


def original_path(env):
    for name in (
        "phase21_v3_original_path",
        "phase19_planned_path",
        "raw_astar_path",
        "global_path",
        "path_world",
    ):
        try:
            p = np.asarray(getattr(env, name), dtype=np.float64).reshape(-1, 2)
        except Exception:
            continue
        if len(p) >= 3 and np.all(np.isfinite(p)):
            return name, p
    return None, None


def scan_seed(seed):
    seed_all(seed)
    env = MkMiniPhase22V1ContinuousCorridorEnv(
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
    sig = safe(E.scenario_signature(env))

    pname, path = original_path(env)
    rm = route_metrics(path) if path is not None else None
    if rm is None:
        try:
            env.close()
        except Exception:
            pass
        return None

    metrics, rp = rm
    rects, circles = known_obstacle_arrays(env)

    map_min = getattr(env, "map_min", None)
    map_max = getattr(env, "map_max", None)
    try:
        map_min = float(map_min)
        map_max = float(map_max)
    except Exception:
        map_min = map_max = None

    clr = point_clearance(rp, rects, circles, map_min, map_max)
    finite = clr[np.isfinite(clr)]
    if len(finite) == 0:
        try:
            env.close()
        except Exception:
            pass
        return None

    metrics.update(
        {
            "known_clearance_min_m": float(np.min(finite)),
            "known_clearance_q20_m": float(np.quantile(finite, 0.20)),
            "known_clearance_median_m": float(np.median(finite)),
        }
    )

    row = {
        "seed": int(seed),
        "known_map_hash": known_map_hash(rects, circles),
        "scenario_signature": sig,
        "path_source": pname,
        "metrics": metrics,
        "rect_count_known": int(len(rects)),
        "circle_count_known": int(len(circles)),
        "path_unchanged_after_unknown_insert": bool(
            getattr(
                env,
                "phase19_path_unchanged",
                getattr(env, "phase19_original_path_unchanged", True),
            )
        ),
    }

    try:
        env.close()
    except Exception:
        pass
    return row


def stratify(rows):
    # Deduplicate known-map geometries before any outcome is observed.
    dedup = []
    seen = set()
    for r in rows:
        h = r["known_map_hash"]
        if h in seen:
            continue
        seen.add(h)
        dedup.append(r)

    if len(dedup) < 80:
        return None

    # Rank split is deliberately outcome-free and guarantees balanced geometry
    # strata without inventing arbitrary meter/degree thresholds.
    by_turn = sorted(
        dedup,
        key=lambda r: (
            r["metrics"]["turn_density_rad_per_m"],
            r["metrics"]["tortuosity"],
            r["seed"],
        ),
    )
    mid = len(by_turn) // 2
    low = by_turn[:mid]
    high = by_turn[mid:]

    def split_width(group):
        g = sorted(
            group,
            key=lambda r: (
                -r["metrics"]["known_clearance_q20_m"],
                r["seed"],
            ),
        )
        m = len(g) // 2
        return g[:m], g[m:]

    low_wide, low_con = split_width(low)
    high_wide, high_con = split_width(high)

    groups = {
        "LOW_TURN_WIDE": low_wide,
        "LOW_TURN_CONSTRAINED": low_con,
        "HIGH_TURN_WIDE": high_wide,
        "HIGH_TURN_CONSTRAINED": high_con,
    }

    if any(len(v) < NEEDED_PER_FAMILY for v in groups.values()):
        return None

    selected = []
    for family in FAMILIES:
        # Deterministic ascending seed selection inside each geometry stratum.
        pick = sorted(groups[family], key=lambda r: r["seed"])[
            :NEEDED_PER_FAMILY
        ]
        for r in pick:
            x = dict(r)
            x["family"] = family
            selected.append(x)

    turn_vals = np.asarray(
        [r["metrics"]["turn_density_rad_per_m"] for r in dedup],
        dtype=float,
    )
    clear_vals = np.asarray(
        [r["metrics"]["known_clearance_q20_m"] for r in dedup],
        dtype=float,
    )

    return {
        "scanned_unique_map_count": len(dedup),
        "turn_density_median": float(np.median(turn_vals)),
        "clearance_q20_median_m": float(np.median(clear_vals)),
        "family_pool_counts": {k: len(v) for k, v in groups.items()},
        "selected": selected,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-start", type=int, default=DEFAULT_START)
    ap.add_argument("--scan-n", type=int, default=DEFAULT_SCAN_N)
    args = ap.parse_args()

    rows = []
    scan_n = int(args.scan_n)

    print("=" * 100)
    print("G3 MULTI-SCENE MANIFEST PREPARATION — RESET ONLY")
    print("=" * 100)
    print("OUTCOME_ROLLOUTS=FALSE")
    print("TRAINING=FALSE")
    print("TUNING_ON_OUTCOMES=FALSE")

    for offset in range(MAX_SCAN_N):
        seed = int(args.seed_start + offset)
        r = scan_seed(seed)
        if r is not None:
            rows.append(r)

        if offset + 1 >= scan_n:
            s = stratify(rows)
            if s is not None:
                break

        if (offset + 1) % 16 == 0:
            print(
                f"RESET_SCAN={offset+1} valid={len(rows)}",
                flush=True,
            )
    else:
        s = stratify(rows)

    if s is None:
        dump(RESULTS / "g3_reset_scan_failed.json", rows)
        raise SystemExit("G3_MANIFEST_PREP=FAIL_INSUFFICIENT_STRATA")

    selected = s["selected"]

    if len(selected) != 80:
        raise RuntimeError(f"SELECTED_COUNT={len(selected)}")
    if len({r["seed"] for r in selected}) != 80:
        raise RuntimeError("DUPLICATE_SELECTED_SEED")
    if len({r["known_map_hash"] for r in selected}) != 80:
        raise RuntimeError("DUPLICATE_SELECTED_KNOWN_MAP")
    if not all(r["path_unchanged_after_unknown_insert"] for r in selected):
        raise RuntimeError("PATH_CHANGED_AFTER_UNKNOWN_INSERT")

    manifest_core = {
        "protocol": "G3_MULTISCENE_80_PAIRED_FROZEN_PHASE22_V1",
        "selection_is_reset_only": True,
        "outcomes_observed_during_selection": False,
        "seed_start": int(args.seed_start),
        "scanned_valid_count": len(rows),
        "scanned_unique_map_count": s["scanned_unique_map_count"],
        "families": list(FAMILIES),
        "family_definition": {
            "turn_axis": (
                "rank split by reset-only original-A* turn density "
                "(wrapped heading change / route length)"
            ),
            "width_axis": (
                "within each turn half, rank split by reset-only q20 "
                "known-obstacle centerline clearance"
            ),
            "labels_are": (
                "geometry strata, not claims of manually authored map types"
            ),
        },
        "selection_summary": {
            "turn_density_median": s["turn_density_median"],
            "clearance_q20_median_m": s["clearance_q20_median_m"],
            "family_pool_counts": s["family_pool_counts"],
        },
        "selected": selected,
    }

    core_bytes = json.dumps(
        safe(manifest_core),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    manifest = dict(manifest_core)
    manifest["manifest_core_sha256"] = sha256_bytes(core_bytes)

    dump(RESULTS / "g3_reset_scan_all.json", rows)
    dump(RESULTS / "g3_manifest.json", manifest)

    print("")
    print("G3_MANIFEST_SELECTED=80")
    for fam in FAMILIES:
        seeds = [r["seed"] for r in selected if r["family"] == fam]
        vals = [r["metrics"] for r in selected if r["family"] == fam]
        print(
            f"{fam}: n={len(seeds)} "
            f"seed_min={min(seeds)} seed_max={max(seeds)} "
            f"turn_density_mean={np.mean([v['turn_density_rad_per_m'] for v in vals]):.4f} "
            f"clear_q20_mean={np.mean([v['known_clearance_q20_m'] for v in vals]):.4f}"
        )

    print(f"MANIFEST_SHA256={manifest['manifest_core_sha256']}")
    print(f"MANIFEST={RESULTS/'g3_manifest.json'}")
    print("G3_MANIFEST_PREP=PASS")


if __name__ == "__main__":
    main()
