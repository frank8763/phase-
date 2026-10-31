
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(os.environ.get("MKMINI_PROJECT", Path.cwd())).resolve()
EXP = ROOT / "experiments/phase_paper_stageG3_multiscene_80_v1"
RESULTS = EXP / "results"

FAMILIES = (
    "LOW_TURN_WIDE",
    "LOW_TURN_CONSTRAINED",
    "HIGH_TURN_WIDE",
    "HIGH_TURN_CONSTRAINED",
)


def wilson(k, n, z=1.959963984540054):
    if n <= 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(
        p * (1 - p) / n + z * z / (4 * n * n)
    ) / den
    return [ctr - half, ctr + half]


def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    s = sum(math.comb(n, i) for i in range(k + 1))
    return min(1.0, 2.0 * s / (2 ** n))


def paired_bootstrap_diff(rows, key, reps=50000):
    x = np.asarray(
        [
            [
                int(bool(r["baseline"][key])),
                int(bool(r["proposed"][key])),
            ]
            for r in rows
        ],
        dtype=np.int8,
    )
    rng = np.random.default_rng(20260915)
    n = len(x)
    vals = np.empty(reps, dtype=np.float32)
    for i in range(reps):
        idx = rng.integers(0, n, size=n)
        y = x[idx]
        vals[i] = float(y[:, 1].mean() - y[:, 0].mean())
    return [
        float(np.quantile(vals, 0.025)),
        float(np.quantile(vals, 0.975)),
    ]


def method_stats(rows, side):
    n = len(rows)
    safe = sum(bool(r[side]["safe_success"]) for r in rows)
    coll = sum(bool(r[side]["collision"]) for r in rows)
    wall = sum(bool(r[side]["wall_timeout"]) for r in rows)
    envt = sum(bool(r[side]["env_timeout"]) for r in rows)
    times = np.asarray(
        [float(r[side]["wall_seconds"]) for r in rows],
        dtype=float,
    )
    return {
        "n": n,
        "safe_success_n": safe,
        "safe_success_rate": safe / n,
        "safe_success_wilson95": wilson(safe, n),
        "collision_n": coll,
        "collision_rate": coll / n,
        "collision_wilson95": wilson(coll, n),
        "wall_timeout_n": wall,
        "wall_timeout_rate": wall / n,
        "env_timeout_n": envt,
        "wall_seconds_mean": float(times.mean()),
        "wall_seconds_p95": float(np.quantile(times, 0.95)),
    }


def paired_stats(rows):
    b_only_s = sum(
        bool(r["baseline"]["safe_success"])
        and not bool(r["proposed"]["safe_success"])
        for r in rows
    )
    p_only_s = sum(
        bool(r["proposed"]["safe_success"])
        and not bool(r["baseline"]["safe_success"])
        for r in rows
    )
    both_s = sum(
        bool(r["baseline"]["safe_success"])
        and bool(r["proposed"]["safe_success"])
        for r in rows
    )
    neither_s = len(rows) - b_only_s - p_only_s - both_s

    b_only_c = sum(
        bool(r["baseline"]["collision"])
        and not bool(r["proposed"]["collision"])
        for r in rows
    )
    p_only_c = sum(
        bool(r["proposed"]["collision"])
        and not bool(r["baseline"]["collision"])
        for r in rows
    )

    bd = np.mean([bool(r["baseline"]["safe_success"]) for r in rows])
    pd = np.mean([bool(r["proposed"]["safe_success"]) for r in rows])
    bc = np.mean([bool(r["baseline"]["collision"]) for r in rows])
    pc = np.mean([bool(r["proposed"]["collision"]) for r in rows])

    return {
        "safe_success_diff_pp": 100.0 * (pd - bd),
        "safe_success_bootstrap95_pp": [
            100.0 * x
            for x in paired_bootstrap_diff(rows, "safe_success")
        ],
        "safe_success_both": both_s,
        "safe_success_proposed_only": p_only_s,
        "safe_success_baseline_only": b_only_s,
        "safe_success_neither": neither_s,
        "safe_success_mcnemar_p": exact_mcnemar(
            p_only_s, b_only_s
        ),
        "collision_diff_pp": 100.0 * (pc - bc),
        "collision_proposed_only": p_only_c,
        "collision_baseline_only": b_only_c,
        "collision_mcnemar_p": exact_mcnemar(
            p_only_c, b_only_c
        ),
    }


def load_rows():
    rows = []
    for shard in range(4):
        p = RESULTS / f"worker_{shard}.jsonl"
        if not p.exists():
            raise SystemExit(f"MISSING_WORKER={shard}")
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    rows = load_rows()
    seeds = [int(r["seed"]) for r in rows]

    if len(rows) != 80:
        raise SystemExit(f"PAIR_COUNT={len(rows)} EXPECTED=80")
    if len(set(seeds)) != 80:
        raise SystemExit("DUPLICATE_SEED")
    if not all(bool(r["same_scenario"]) for r in rows):
        raise SystemExit("SCENARIO_MISMATCH_PRESENT")

    fam_counts = {
        f: sum(r["family"] == f for r in rows)
        for f in FAMILIES
    }
    if any(v != 20 for v in fam_counts.values()):
        raise SystemExit(f"BAD_FAMILY_COUNTS={fam_counts}")

    summary = {
        "protocol": "G3_MULTISCENE_80_PAIRED_FROZEN_PHASE22_V1",
        "pairs": 80,
        "rollouts": 160,
        "family_counts": fam_counts,
        "pooled": {
            "baseline": method_stats(rows, "baseline"),
            "proposed": method_stats(rows, "proposed"),
            "paired": paired_stats(rows),
        },
        "families": {},
        "phase22": {
            "attempted_n": sum(
                bool(r["proposed"].get("phase22_attempted", False))
                for r in rows
            ),
            "corridor_success_n": sum(
                bool(
                    r["proposed"].get(
                        "phase22_corridor_success", False
                    )
                )
                for r in rows
            ),
        },
        "protocol_failures": {
            "scenario_mismatch": 0,
            "ground_truth_control": sum(
                bool(
                    r[side].get(
                        "ground_truth_used_for_control", False
                    )
                )
                for r in rows
                for side in ("baseline", "proposed")
            ),
        },
    }

    for fam in FAMILIES:
        rr = [r for r in rows if r["family"] == fam]
        summary["families"][fam] = {
            "baseline": method_stats(rr, "baseline"),
            "proposed": method_stats(rr, "proposed"),
            "paired_descriptive": paired_stats(rr),
        }

    (RESULTS / "g3_formal_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = []
    lines.append("G3 MULTI-SCENE 80-PAIR FORMAL SUMMARY")
    lines.append("=" * 80)
    p = summary["pooled"]
    lines.append(
        "POOLED safe success: "
        f"{p['baseline']['safe_success_n']}/80 "
        f"({100*p['baseline']['safe_success_rate']:.2f}%) -> "
        f"{p['proposed']['safe_success_n']}/80 "
        f"({100*p['proposed']['safe_success_rate']:.2f}%)"
    )
    lines.append(
        f"POOLED paired diff = {p['paired']['safe_success_diff_pp']:.2f} pp, "
        f"bootstrap95 = "
        f"[{p['paired']['safe_success_bootstrap95_pp'][0]:.2f}, "
        f"{p['paired']['safe_success_bootstrap95_pp'][1]:.2f}] pp, "
        f"McNemar p = {p['paired']['safe_success_mcnemar_p']:.8g}"
    )
    lines.append(
        "POOLED collision: "
        f"{p['baseline']['collision_n']}/80 "
        f"({100*p['baseline']['collision_rate']:.2f}%) -> "
        f"{p['proposed']['collision_n']}/80 "
        f"({100*p['proposed']['collision_rate']:.2f}%), "
        f"McNemar p = {p['paired']['collision_mcnemar_p']:.8g}"
    )
    lines.append("")
    for fam in FAMILIES:
        q = summary["families"][fam]
        lines.append(
            f"{fam}: safe "
            f"{q['baseline']['safe_success_n']}/20 -> "
            f"{q['proposed']['safe_success_n']}/20; "
            f"collision {q['baseline']['collision_n']}/20 -> "
            f"{q['proposed']['collision_n']}/20; "
            f"diff={q['paired_descriptive']['safe_success_diff_pp']:.1f}pp"
        )
    lines.append("")
    lines.append(
        f"Phase22 attempted={summary['phase22']['attempted_n']}/80, "
        f"corridor_success={summary['phase22']['corridor_success_n']}/80"
    )
    lines.append("G3_FORMAL_COMPLETE=PASS")

    text = "\n".join(lines) + "\n"
    (RESULTS / "g3_paper_summary.txt").write_text(
        text, encoding="utf-8"
    )
    print(text, end="")


if __name__ == "__main__":
    main()
